import abc
import logging
import os
from xml.dom import minidom


def _lazy_import():
    global javalang, PluginBase, is_java_file, get_min_sdk, get_target_sdk, get_package_from_manifest
    from pluginbase import PluginBase
    import javalang
    from plugins.manifest_helpers import get_min_sdk, get_target_sdk, get_package_from_manifest
    from utils import is_java_file

_lazy_import()

log = logging.getLogger(__name__)

plugin_base = PluginBase(package="qark.custom_plugins")

# Plugin modules to blacklist
BLACKLISTED_PLUGIN_MODULES = {"helpers"}

def get_plugin_source(category=None):
    """
    Returns a PluginBase.PluginSource based on the category.

    :param category: Plugin category, subdirectory under `plugins/`
    :return: PluginBase.PluginSource
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugins")
    path = os.path.join(path, category) if category else path

    try:
        return plugin_base.make_plugin_source(searchpath=[path], persist=True)
    except Exception as e:
        log.exception(f"Failed to get plugins. Check the file path: {path}. Error: {e}")
        raise SystemExit("Failed to get plugins. Check the file path.")

def get_plugins(category=None):
    """
    Returns plugins from a specified category excluding blacklisted plugins.

    :param category: Plugin category
    :return: List of plugins
    """
    plugins = get_plugin_source(category=category).list_plugins()
    return [plugin for plugin in plugins if plugin not in BLACKLISTED_PLUGIN_MODULES]

# -------------------------- Base Plugin Classes -------------------------- #

class BasePlugin(abc.ABC):
    def __init__(self, name, category, description=None, **kwargs):
        self.category = category
        self.name = name
        self.description = description
        self.issues = []
        super().__init__(**kwargs)

    @abc.abstractmethod
    def run(self):
        """
        Abstract method for plugin execution.
        """
        pass

class PluginObserver(BasePlugin):
    @abc.abstractmethod
    def update(self, *args, **kwargs):
        """Observer method to be implemented by plugins."""
        pass

    @abc.abstractmethod
    def reset(self):
        """Resets class attributes for the file."""
        pass

class FilePathPlugin(PluginObserver):
    file_path = None
    has_been_set = False

    def update(self, file_path, call_run=False):
        if not file_path:
            FilePathPlugin.file_path = None
            return

        if not self.has_been_set:
            FilePathPlugin.file_path = file_path
            FilePathPlugin.has_been_set = True

        if call_run:
            self.run()

    @classmethod
    def reset(cls):
        cls.file_path = None
        cls.has_been_set = False

class FileContentsPlugin(FilePathPlugin):
    file_contents = None
    readable = True

    def update(self, file_path, call_run=False):
        if not self.readable:
            return

        if self.file_contents is None:
            super().update(file_path)
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.file_contents = f.read()
            except (IOError, UnicodeDecodeError) as e:
                log.debug(f"Unable to read file {self.file_path}. Error: {e}")
                self.readable = False
                self.file_contents = None
                return

        if call_run and self.file_contents:
            self.run()

    @classmethod
    def reset(cls):
        cls.file_contents = None
        cls.readable = True
        super().reset()

class JavaASTPlugin(FileContentsPlugin):
    java_ast = None
    parseable = True

    def update(self, file_path, call_run=False):
        if not self.parseable:
            return

        if self.java_ast is None and is_java_file(file_path):
            super().update(file_path, call_run=False)
            if self.file_contents:
                try:
                    self.java_ast = javalang.parse.parse(self.file_contents)
                except (javalang.parser.JavaSyntaxError, IndexError) as e:
                    log.debug(f"Failed to parse AST for {self.file_path}. Error: {e}")
                    self.java_ast = None
                    self.parseable = False
                    return

        if call_run and self.java_ast:
            try:
                self.run()
            except Exception as e:
                log.exception(f"Failed to run plugin for {self.file_path}. Error: {e}")

    @classmethod
    def reset(cls):
        cls.java_ast = None
        cls.parseable = True
        super().reset()

class CoroutinePlugin(JavaASTPlugin):
    def can_run_coroutine(self):
        """Determine whether the coroutine should run."""
        return True

    def run(self):
        """Execute coroutine on AST."""
        if self.can_run_coroutine():
            coroutine = self.prime_coroutine()
            for path, node in self.java_ast:
                coroutine.send((path, node))

    def prime_coroutine(self):
        """Prime and return the coroutine."""
        coroutine = self.run_coroutine()
        next(coroutine)
        return coroutine

    @abc.abstractmethod
    def run_coroutine(self):
        """Implement coroutine execution."""
        pass

class ManifestPlugin(BasePlugin):
    manifest_xml = None
    manifest_path = None
    min_sdk = -1
    target_sdk = -1
    package_name = "PACKAGE_NOT_FOUND"

    @classmethod
    def update_manifest(cls, path_to_manifest):
        cls.manifest_path = path_to_manifest
        try:
            cls.manifest_xml = minidom.parse(path_to_manifest)
        except Exception as e:
            cls.manifest_xml = None
            log.debug(f"Failed to update manifest for {path_to_manifest}. Error: {e}")
            return

        try:
            cls.min_sdk = get_min_sdk(cls.manifest_path)
            cls.target_sdk = get_target_sdk(cls.manifest_path)
        except AttributeError:
            cls.min_sdk = cls.target_sdk = 1

        try:
            cls.package_name = get_package_from_manifest(cls.manifest_path)
        except IOError:
            cls.package_name = "PACKAGE_NOT_FOUND"

    @abc.abstractmethod
    def run(self):
        """User-defined method for running the plugin."""
        pass
