import logging
import os
import shlex
import shutil
import subprocess
from io import StringIO
import configparser

from plugins.helpers import copy_directory_to_location
from plugins.manifest_helpers import get_package_from_manifest
from xml_helpers import write_key_value_to_string_array_xml, write_key_value_to_xml

log = logging.getLogger(__name__)

COMPONENT_ENTRIES = {
    "activity": ("onCreate", "onStart"),
    "activity-alias": ("onCreate", "onStart"),
    "receiver": ("onReceive",),
    "service": ("onCreate", "onBind", "onStartCommand", "onHandleIntent"),
    "provider": ("onReceive",)
}

EXPLOIT_APK_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exploit_apk")


class APKBuilder:
    _instance = None

    def __new__(cls, exploit_apk_path, issues, apk_name, manifest_path, sdk_path):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, exploit_apk_path, issues, apk_name, manifest_path, sdk_path):
        self.exploit_apk_path = os.path.join(exploit_apk_path, f"{apk_name}_exploit_apk")
        self.sdk_path = sdk_path
        self.issues = issues

        # Cleanup old directories safely
        if os.path.isdir(self.exploit_apk_path):
            shutil.rmtree(self.exploit_apk_path)

        try:
            copy_directory_to_location(EXPLOIT_APK_TEMPLATE_PATH, self.exploit_apk_path)
        except Exception as e:
            log.exception(f"Failed to copy {EXPLOIT_APK_TEMPLATE_PATH} to {self.exploit_apk_path}: {e}")
            raise SystemExit(f"Failed to copy {EXPLOIT_APK_TEMPLATE_PATH} to {self.exploit_apk_path}")

        values_path = os.path.join(self.exploit_apk_path, "app", "src", "main", "res", "values")
        self.strings_xml_path = os.path.join(values_path, "strings.xml")
        self.extra_keys_xml_path = os.path.join(values_path, "extraKeys.xml")
        self.intent_ids_xml_path = os.path.join(values_path, "intentID.xml")
        self.properties_file_path = os.path.join(self.exploit_apk_path, "local.properties")

        try:
            self.package_name = get_package_from_manifest(manifest_path)
        except IOError as e:
            log.exception(f"Failed to read manifest file at {manifest_path}: {e}")
            raise SystemExit(f"Failed to read manifest file at {manifest_path}")

    def build(self):
        self._write_additional_exploits()
        self._build_apk()

    def _write_additional_exploits(self):
        for issue in self.issues:
            self._write_exported_tags(issue)

    def _write_exported_tags(self, issue):
        apk_exploit = issue.apk_exploit_dict
        if not apk_exploit:
            return

        try:
            tag_enum = apk_exploit["exported_enum"]
            tag_name = apk_exploit["tag_name"]
            package_name = apk_exploit["package_name"]
            arguments = apk_exploit.get("arguments")
        except KeyError as e:
            log.error(f"Missing key in apk_exploit_dict: {e}")
            return

        new_key = write_key_value_to_string_array_xml(
            array_name=tag_enum.parent.value,
            value=tag_enum.type.value,
            path=self.intent_ids_xml_path
        )

        if arguments and tag_enum.type.value in ("activity", "broadcast", "provider", "receiver"):
            for argument in arguments:
                write_key_value_to_string_array_xml(
                    array_name=new_key,
                    value=argument,
                    path=self.extra_keys_xml_path,
                    add_id=False
                )
        write_key_value_to_xml(key=new_key, value=f"{package_name}{tag_name}", path=self.strings_xml_path)

    def _build_apk(self):
        log.debug("Building APK...")
        current_directory = os.getcwd()
        try:
            os.chdir(self.exploit_apk_path)
            write_key_value_to_xml('packageName', self.package_name, self.strings_xml_path)
            self._write_properties_file({"sdk.dir": self.sdk_path})

            command = "./gradlew assembleDebug"
            log.info(f"Running command: {command}")
            result = subprocess.run(shlex.split(command), check=True, capture_output=True, text=True)
            log.info(result.stdout)
            if result.stderr:
                log.error(result.stderr)

        except subprocess.CalledProcessError as e:
            log.error(f"Build failed: {e}")
            raise
        finally:
            os.chdir(current_directory)

    def _write_properties_file(self, properties_dict, append=True):
        mode = "a" if append else "w"
        try:
            with open(self.properties_file_path, mode) as properties_file:
                for key, value in properties_dict.items():
                    properties_file.write(f"{key}={value}\n")
            log.info("Properties file written successfully.")
        except Exception as e:
            log.error(f"Failed to write to properties file: {e}")
            raise

    def _read_properties_file(self):
        try:
            with open(self.properties_file_path, "r") as properties_file:
                config_data = "[dummy_header]\n" + properties_file.read().replace('%', '%%')
                config = StringIO(config_data)
                config.seek(0)

                cp = configparser.ConfigParser()
                cp.read_file(config)
                return dict(cp.items('dummy_header'))
        except Exception as e:
            log.error(f"Failed to read properties file: {e}")
            raise
