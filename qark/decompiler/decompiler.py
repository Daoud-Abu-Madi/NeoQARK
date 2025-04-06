import logging
import os
import platform
import re
import shlex
import shutil
import stat
import subprocess
import zipfile
from multiprocessing.pool import ThreadPool

from decompiler.external_decompiler import DECOMPILERS, LIB_PATH
from utils import is_java_file

log = logging.getLogger(__name__)

OS = platform.system()
JAVA_VERSION_REGEX = r'(\d+\.\d+)(\.\d+)?'
APK_TOOL_PATH = os.path.join(LIB_PATH, "apktool")

DEX2JAR_NAME = "dex2jar-2.0"
DEX2JAR_PATH = os.path.join(LIB_PATH, DEX2JAR_NAME)
DEX2JAR_EXTENSION = "sh" if OS != "Windows" else "bat"
DEX2JAR_EXECUTABLE = "d2j-dex2jar.{extension}".format(extension=DEX2JAR_EXTENSION)
DEX2JAR_INVOKE = "d2j_invoke.{extension}".format(extension=DEX2JAR_EXTENSION)

DECOMPILERS_PATH = os.path.join(LIB_PATH, "decompilers")

APK_TOOL_COMMAND = (
    "java -Djava.awt.headless=true -jar {apktool_path}/apktool.jar "
    "d {path_to_source} --no-src --force -m --output {build_directory}"
)
DEX2JAR_COMMAND = "{dex2jar_path} {path_to_dex} -o {build_apk}.jar"

def escape_windows_path(path):
    if "\\" in path and OS == "Windows":
        try:
            path = path.encode('unicode_escape').decode('utf-8')
        except Exception:
            path = path.encode('utf-8').decode('unicode_escape')
    return path

class Decompiler(object):
    """This class handles unpacking and decompiling APKs into Java source code.

    New compilers can be added by adding the command to run the compiler to the `DECOMPILER_COMMANDS` dictionary and
    adding them into the `Decompiler.decompilers` dictionary with the path to the decompiler on the system.
    Each decompiler should have at most the following keys in their command string:
    {path_to_decompiler}, {jar}, {build_directory} -- Keys can be less than these but there can be no extra keys.
    """
    def __init__(self, path_to_source, build_directory=None):
        """
        :param path_to_source: Path to directory, APK, or a .java file
        :param build_directory: directory to unpack and decompile APK to.
                                If directory does not exist it will be created, defaults to same directory as APK/qark
        """
        if not os.path.exists(path_to_source):
            raise ValueError("Invalid path, path must be to an APK, directory, or a Java file")

        self.path_to_source = path_to_source
        self.build_directory = os.path.join(build_directory, "qark") if build_directory else os.path.join(os.path.dirname(os.path.abspath(path_to_source)), "qark")

        # validate we are running on an APK, Directory, or Java source code
        if os.path.isfile(self.path_to_source) and os.path.splitext(self.path_to_source.lower())[1] not in (".java", ".apk"):
            raise ValueError("Invalid path, path must be to an APK, directory, or a Java file")

        if os.path.isdir(path_to_source) or is_java_file(path_to_source):
            self.source_code = True
            self.manifest_path = None
            log.debug("Decompiler got directory to run on, assuming Java source code")
            return

        self.source_code = False
        self.apk_name = os.path.splitext(os.path.basename(path_to_source))[0]  # name of APK without the .apk extension

        self.dex_path = self._unpack_apk()
        self.jar_path = self._run_dex2jar()
        self.manifest_path = self.run_apktool()

        self.decompilers = DECOMPILERS

    def run(self):
        """Top-level function which runs each decompiler and waits for them to finish decompilation."""
        if self.source_code:
            return

        decompiler_pool = ThreadPool(len(self.decompilers))

        for decompiler in self.decompilers:
            if not os.path.isdir(os.path.join(self.build_directory, decompiler.name)):
                os.makedirs(os.path.join(self.build_directory, decompiler.name))
            log.debug("Starting decompilation with %s", decompiler.name)
            decompiler_pool.apply_async(self._decompiler_function, args=(decompiler,))

        decompiler_pool.close()
        decompiler_pool.join()

        jar_name = os.path.split(self.jar_path)[-1]
        unpack_fernflower_jar(self.build_directory, jar_name)

    def _decompiler_function(self, decompiler):
        """
        Abstract function that subprocesses a call to a decompiler and passes it the path of the decompiler supplied.
        If the `self.jar_path` is not set this will run `self._run_dex2jar` to set its value.

        :param decompiler: Decompiler that extends `ExternalDecompiler` base class
        """
        if not self.jar_path:
            log.debug(".jar file path not found, trying to create dex file.")
            self.jar_path = self._run_dex2jar()

        decompiler_command = escape_windows_path(
            decompiler.command.format(path_to_decompiler=decompiler.path_to_decompiler,
                                      jar=self.jar_path,
                                      build_directory=self.build_directory))

        try:
            retcode = subprocess.call(shlex.split(decompiler_command))
        except Exception:
            log.exception("%s failed to finish decompiling, continuing", decompiler.name)
        else:
            if retcode != 0:
                log.info("Error running %s", decompiler.name)
                log.debug("Decompiler failed with command %s", decompiler_command)

    def run_apktool(self):
        """
        Runs `APK_TOOL_COMMAND` with the users path to APK to decompile the APK.
        Sets `self.manifest_path` to its correct location.
        """
        # check that java is version 1.7 or higher
        java_version = get_java_version()

        try:
            if float(java_version[:3]) < 1.7:
                raise SystemExit("Java version of 1.7 or higher is required to run apktool")
        except TypeError:
            log.info("Java version %s not expected, continuing run", java_version)

        user_os = platform.system().lower()
        if user_os not in ("linux", "windows", "darwin"):
            raise SystemExit("OS %s is not supported, please use Linux, Windows, or Mac OSX", user_os)

        configure_apktool()

        apktool_build_dir = os.path.join(self.build_directory, "apktool")
        if not os.path.isdir(apktool_build_dir):
            os.makedirs(apktool_build_dir)

        custom_apktool_command = escape_windows_path(APK_TOOL_COMMAND.format(apktool_path=APK_TOOL_PATH,
                                                                             path_to_source=self.path_to_source,
                                                                             build_directory=apktool_build_dir))
        log.debug("Calling APKTool with following command")
        log.debug(custom_apktool_command)
        try:
            subprocess.call(shlex.split(custom_apktool_command))
        except Exception as e:
            log.exception("Failed to run APKTool with command: %s", custom_apktool_command)
            raise SystemExit(f"Failed to run APKTool: {str(e)}")

        log.debug("APKTool finished executing, trying to move manifest into proper location")
        manifest_source = os.path.join(apktool_build_dir, "AndroidManifest.xml")
        manifest_dest = os.path.join(self.build_directory, "AndroidManifest.xml")

        if not os.path.isfile(manifest_source):
            log.error(f"File 'AndroidManifest.xml' not found in {apktool_build_dir}")
            raise FileNotFoundError(f"Manifest file {manifest_source} does not exist")

        shutil.move(manifest_source, manifest_dest)
        log.debug("Manifest moved successfully")

        log.debug("Removing apktool subdirectory of build")
        try:
            shutil.rmtree(apktool_build_dir)
        except Exception as e:
            log.warning(f"Failed to remove apktool directory: {str(e)}")
        log.debug("Removed apktool directory")

        return manifest_dest

    def _unpack_apk(self):
        """
        Unpacks an APK and extracts its contents.

        :return: location for `self.dex_path` to use
        :rtype: os.path object
        """
        log.debug("Unpacking apk")
        unzip_file(self.path_to_source, destination_to_unzip=self.build_directory)

        dex_path = os.path.join(self.build_directory, "classes.dex")
        if not os.path.isfile(dex_path):
            raise FileNotFoundError(f"Dex file not found at {dex_path}")

        return dex_path

    def _run_dex2jar(self):
        """Runs dex2jar in the lib on the dex file.

        If `self.dex_path` is None or empty it will run `_unpack_apk` to get a value for it.
        """
        if not self.dex_path:
            log.debug("Path to .dex file not found, unpacking APK")
            self.dex_path = self._unpack_apk()

        configure_dex2jar()

        dex2jar_script = os.path.join(DEX2JAR_PATH, DEX2JAR_EXECUTABLE)
        if not os.path.isfile(dex2jar_script):
            log.error(f"Dex2jar script not found at {dex2jar_script}")
            raise FileNotFoundError(f"Dex2jar script {dex2jar_script} does not exist")

        # التأكد من إنشاء المجلدات إذا لم تكن موجودة
        os.makedirs(os.path.dirname(self.dex_path), exist_ok=True)
        os.makedirs(os.path.dirname(os.path.join(self.build_directory, self.apk_name)), exist_ok=True)

        dex2jar_command = escape_windows_path(DEX2JAR_COMMAND.format(dex2jar_path=dex2jar_script,
                                                                    path_to_dex=self.dex_path,
                                                                    build_apk=os.path.join(self.build_directory,
                                                                                           self.apk_name)))

        log.debug("Running dex2jar with command %s", dex2jar_command)
        try:
            ret_code = subprocess.call(shlex.split(dex2jar_command), shell=True)  # أضفت shell=True للتعامل مع السكربتات
            if ret_code != 0:
                log.critical("Error running dex2jar command: %s", dex2jar_command)
                raise SystemExit("Error running dex2jar")
        except Exception as e:
            log.exception("Error running dex2jar command: %s", dex2jar_command)
            raise SystemExit(f"Error running dex2jar command: {str(e)}")

        jar_path = os.path.join(self.build_directory, f"{self.apk_name}.jar")
        if not os.path.isfile(jar_path):
            raise FileNotFoundError(f"JAR file not created at {jar_path}")

        return jar_path

def unzip_file(file_to_unzip, destination_to_unzip="unzip_apk"):
    """
    Extract all directories in the zip to the destination.

    :param str file_to_unzip:
    :param str destination_to_unzip:
    """
    if not os.path.isdir(destination_to_unzip):
        os.makedirs(destination_to_unzip)
    try:
        zipped_apk = zipfile.ZipFile(file_to_unzip, "r")
        zipped_apk.extractall(path=destination_to_unzip)
    except Exception as e:
        log.exception("Failed to extract zipped APK from %s to %s", file_to_unzip, destination_to_unzip)
        raise SystemExit(f"Failed to extract zipped APK: {str(e)}")

def get_java_version():
    """
    Run `java -version` and return its output

    :return: String of the version like '1.7.0' or '1.6.0_36'
    :rtype: str
    :raise: Exception if `java -version` fails to run properly
    """
    log.debug("Getting java version")
    try:
        full_version = subprocess.check_output(["java", "-version"], stderr=subprocess.STDOUT).decode('utf-8')
    except Exception as e:
        raise SystemExit(f"Error getting java version, is Java installed?: {str(e)}")

    log.debug("Got full java version %s", full_version)
    version_regex = re.search(JAVA_VERSION_REGEX, full_version)

    try:
        return version_regex.group(1)
    except TypeError:
        raise SystemExit("Java version %s doesn't match regex search of %s" % (full_version, JAVA_VERSION_REGEX))

def configure_apktool():
    """Attempts to make apktool in lib/apktool/{operating_system}/ executable."""
    try:
        make_executable(os.path.join(APK_TOOL_PATH, "apktool.jar"))
    except Exception as e:
        log.exception("Failed to make APKTool files executable, continuing: %s", str(e))

def make_executable(file_path):
    """
    Make the file at `file_path` executable.

    :param file_path: path to file to make executable
    """
    file_path = escape_windows_path(file_path)

    try:
        st = os.stat(file_path)
        os.chmod(file_path, st.st_mode | stat.S_IEXEC)
    except Exception as e:
        log.exception("Failed to make files executable, continuing: %s", str(e))
        raise

def configure_dex2jar():
    make_executable(os.path.join(DEX2JAR_PATH, DEX2JAR_EXECUTABLE))
    make_executable(os.path.join(DEX2JAR_PATH, DEX2JAR_INVOKE))

def unpack_fernflower_jar(build_directory, jar_name):
    """Fernflower puts its decompiled code back into a jar so we need to unpack it."""
    previous_dir = os.getcwd()
    command = ["jar", "xf", jar_name]

    try:
        os.chdir(os.path.join(build_directory, "fernflower"))
        retcode = subprocess.call(command)
    except Exception as e:
        log.exception("Failed to extract fernflower jar with command '%s': %s", " ".join(command), str(e))
    else:
        if retcode != 0:
            log.error("Failed to extract fernflower jar with command '%s'", " ".join(command))
    finally:
        os.chdir(previous_dir)
