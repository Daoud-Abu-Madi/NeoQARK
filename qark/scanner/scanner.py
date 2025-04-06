import logging
import os

log = logging.getLogger(__name__)

PLUGIN_CATEGORIES = ("manifest", "broadcast", "file", "crypto", "intent", "cert", "webview", "generic")

# تأخير الاستيرادات حتى الحاجة
def _lazy_import():
    global CoroutinePlugin, JavaASTPlugin, ManifestPlugin, PluginObserver, get_plugin_source, get_plugins, is_java_file, Subject
    from scanner.plugin import CoroutinePlugin, JavaASTPlugin, ManifestPlugin, PluginObserver, get_plugin_source, get_plugins
    from utils import is_java_file
    class Subject:
        def __init__(self):
            self.observers = []

        def register(self, observer):
            """
            Register an observer plugin.

            :param PluginObserver observer: Observer plugin to register
            """
            self.observers.append(observer)

        def unregister(self, observer):
            """
            Unregister an observer plugin.

            :param PluginObserver observer: Observer plugin to remove
            """
            self.observers.remove(observer)

        def notify(self, file_path):
            """
            Notify all registered observers with the file path.

            :param str file_path: Path of the file to analyze
            """
            for observer in self.observers:
                observer.update(file_path, call_run=True)

        def reset(self):
            """
            Reset all observer states.
            """
            for observer in self.observers:
                observer.reset()

_lazy_import()

class Scanner:
    def __init__(self, manifest_path, path_to_source):
        """
        Creates the scanner.

        :param str manifest_path: Path to the manifest file
        :param str path_to_source: Path to the source code or APK directory
        """
        self.files = set()
        self.issues = []
        self.manifest_path = manifest_path
        self.path_to_source = path_to_source
        self._gather_files()

    def run(self):
        """
        Runs all the plugin checks by category.
        """
        plugins = []

        for category in PLUGIN_CATEGORIES:
            plugin_source = get_plugin_source(category=category)

            if category == "manifest":
                manifest_plugins = get_plugins(category)
                ManifestPlugin.update_manifest(self.manifest_path)

                if ManifestPlugin.manifest_xml is not None:
                    for plugin_name in manifest_plugins:
                        plugin = plugin_source.load_plugin(plugin_name).plugin
                        plugin.all_files = self.files
                        plugin.run()
                        self.issues.extend(plugin.issues)
                continue

            plugins.extend(plugin_source.load_plugin(plugin_name).plugin for plugin_name in get_plugins(category))

        self._run_checks(plugins)

    def _run_checks(self, plugins):
        """
        Run all plugins (excluding manifest plugins) on each file.
        """
        current_file_subject = Subject()

        # Separate observer and coroutine plugins
        observer_plugins = [p for p in plugins if isinstance(p, PluginObserver)]
        coroutine_plugins = [p for p in plugins if isinstance(p, CoroutinePlugin)]

        for plugin in observer_plugins:
            current_file_subject.register(plugin)

        for filepath in self.files:
            # Notify observer plugins
            current_file_subject.notify(filepath)

            # Efficiently run coroutine plugins
            notify_coroutines(coroutine_plugins)

            # Reset plugin state
            current_file_subject.reset()

        for plugin in plugins:
            self.issues.extend(plugin.issues)

    def _gather_files(self):
        """
        Gather all relevant files from the source path for analysis.
        """
        if is_java_file(self.path_to_source):
            self.files.add(self.path_to_source)
            log.debug("Added single Java file to scanner.")
            return

        log.debug("Scanning and adding files from source path...")
        try:
            for dir_path, _, file_names in os.walk(self.path_to_source):
                for file_name in file_names:
                    self.files.add(os.path.join(dir_path, file_name))
        except (AttributeError, FileNotFoundError) as e:
            log.debug(f"Failed to gather files from source path: {e}")


def notify_coroutines(coroutine_plugins):
    """
    Efficiently run all coroutine plugins by iterating over the Java AST once.

    :param list coroutine_plugins: List of coroutine plugins to run
    """
    if JavaASTPlugin.java_ast is not None:
        coroutines_to_run = [plugin.prime_coroutine() for plugin in coroutine_plugins if plugin.can_run_coroutine()]

        for path, node in JavaASTPlugin.java_ast:
            for coroutine in coroutines_to_run:
                coroutine.send((path, node))
