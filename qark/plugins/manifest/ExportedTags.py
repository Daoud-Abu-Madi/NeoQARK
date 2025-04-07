from qark.plugins.manifest_helpers import get_min_sdk, get_target_sdk, get_package_from_manifest
from qark.plugins.helpers import java_files_from_files
from qark.scanner.plugin import ManifestPlugin
from qark.issue import Severity, Issue

import os
import logging
from enum import Enum
import javalang
from javalang.tree import Literal, MethodDeclaration, MethodInvocation
from typing import List, Optional, Dict, Any

# Initialize the logger
log = logging.getLogger(__name__)

# Define components and their methods
COMPONENT_ENTRIES = {
    "activity": {"onCreate", "onStart"},
    "activity-alias": {"onCreate", "onStart"},
    "receiver": {"onReceive", },
    "service": {"onCreate", "onBind", "onStartCommand", "onHandleIntent"},
    "provider": {"onReceive", }
}

# List of method names used to retrieve extra data
EXTRAS_METHOD_NAMES = [
    'getExtras', 'getStringExtra', 'getIntExtra', 'getIntArrayExtra', 'getFloatExtra', 'getFloatArrayExtra',
    'getDoubleExtra', 'getDoubleArrayExtra', 'getCharExtra', 'getCharArrayExtra', 'getByteExtra', 'getByteArrayExtra',
    'getBundleExtra', 'getBooleanExtra', 'getBooleanArrayExtra', 'getCharSequenceArrayExtra',
    'getCharSequenceArrayListExtra', 'getCharSequenceExtra', 'getIntegerArrayListExtra', 'getLongArrayExtra',
    'getLongExtra', 'getParcelableArrayExtra', 'getParcelableArrayListExtra', 'getParcelableExtra',
    'getSerializableExtra', 'getShortArrayExtra', 'getShortExtra', 'getStringArrayExtra',
    'getStringArrayListExtra', 'getString', 'getInt'
]

# List of protected broadcasts
PROTECTED_BROADCASTS = [
    'android.intent.action.SCREEN_OFF', 'android.intent.action.SCREEN_ON', 'android.intent.action.USER_PRESENT',
    'android.intent.action.TIME_TICK', 'android.intent.action.TIMEZONE_CHANGED', 'android.intent.action.BOOT_COMPLETED',
    'android.intent.action.PACKAGE_INSTALL', 'android.intent.action.PACKAGE_ADDED',
    'android.intent.action.PACKAGE_REPLACED', 'android.intent.action.MY_PACKAGE_REPLACED',
    'android.intent.action.PACKAGE_REMOVED', 'android.intent.action.PACKAGE_FULLY_REMOVED',
    'android.intent.action.PACKAGE_CHANGED', 'android.intent.action.PACKAGE_RESTARTED',
    'android.intent.action.PACKAGE_DATA_CLEARED', 'android.intent.action.PACKAGE_FIRST_LAUNCH',
    'android.intent.action.PACKAGE_NEEDS_VERIFICATION', 'android.intent.action.PACKAGE_VERIFIED',
    'android.intent.action.UID_REMOVED', 'android.intent.action.QUERY_PACKAGE_RESTART',
    'android.intent.action.CONFIGURATION_CHANGED', 'android.intent.action.LOCALE_CHANGED',
    'android.intent.action.BATTERY_CHANGED', 'android.intent.action.BATTERY_LOW',
    'android.intent.action.BATTERY_OKAY', 'android.intent.action.ACTION_POWER_CONNECTED',
    'android.intent.action.ACTION_POWER_DISCONNECTED', 'android.intent.action.ACTION_SHUTDOWN',
    'android.intent.action.DEVICE_STORAGE_LOW', 'android.intent.action.DEVICE_STORAGE_OK',
    'android.intent.action.DEVICE_STORAGE_FULL', 'android.intent.action.DEVICE_STORAGE_NOT_FULL',
    'android.intent.action.NEW_OUTGOING_CALL', 'android.intent.action.REBOOT', 'android.intent.action.DOCK_EVENT',
    'android.intent.action.MASTER_CLEAR_NOTIFICATION', 'android.intent.action.USER_ADDED',
    'android.intent.action.USER_REMOVED', 'android.intent.action.USER_STOPPED', 'android.intent.action.USER_BACKGROUND',
    'android.intent.action.USER_FOREGROUND', 'android.intent.action.USER_SWITCHED',
    'android.app.action.ENTER_CAR_MODE', 'android.app.action.EXIT_CAR_MODE', 'android.app.action.ENTER_DESK_MODE',
    'android.app.action.EXIT_DESK_MODE', 'android.appwidget.action.APPWIDGET_UPDATE_OPTIONS',
    'android.appwidget.action.APPWIDGET_DELETED', 'android.appwidget.action.APPWIDGET_DISABLED',
    'android.appwidget.action.APPWIDGET_ENABLED', 'android.backup.intent.RUN', 'android.backup.intent.CLEAR',
    'android.backup.intent.INIT', 'android.bluetooth.adapter.action.STATE_CHANGED',
    'android.bluetooth.adapter.action.SCAN_MODE_CHANGED', 'android.bluetooth.adapter.action.DISCOVERY_STARTED',
    'android.bluetooth.adapter.action.DISCOVERY_FINISHED', 'android.bluetooth.adapter.action.LOCAL_NAME_CHANGED',
    'android.bluetooth.adapter.action.CONNECTION_STATE_CHANGED', 'android.bluetooth.device.action.FOUND',
    'android.bluetooth.device.action.DISAPPEARED', 'android.bluetooth.device.action.CLASS_CHANGED',
    'android.bluetooth.device.action.ACL_CONNECTED', 'android.bluetooth.device.action.ACL_DISCONNECT_REQUESTED',
    'android.bluetooth.device.action.ACL_DISCONNECTED', 'android.bluetooth.device.action.NAME_CHANGED',
    'android.bluetooth.device.action.BOND_STATE_CHANGED', 'android.bluetooth.device.action.NAME_FAILED',
    'android.bluetooth.device.action.PAIRING_REQUEST', 'android.bluetooth.device.action.PAIRING_CANCEL',
    'android.bluetooth.device.action.CONNECTION_ACCESS_REPLY',
    'android.bluetooth.headset.profile.action.CONNECTION_STATE_CHANGED',
    'android.bluetooth.headset.profile.action.AUDIO_STATE_CHANGED',
    'android.bluetooth.headset.action.VENDOR_SPECIFIC_HEADSET_EVENT',
    'android.bluetooth.a2dp.profile.action.CONNECTION_STATE_CHANGED',
    'android.bluetooth.a2dp.profile.action.PLAYING_STATE_CHANGED',
    'android.bluetooth.input.profile.action.CONNECTION_STATE_CHANGED',
    'android.bluetooth.pan.profile.action.CONNECTION_STATE_CHANGED',
    'android.hardware.display.action.WIFI_DISPLAY_STATUS_CHANGED', 'android.hardware.usb.action.USB_STATE',
    'android.hardware.usb.action.USB_ACCESSORY_ATTACHED', 'android.hardware.usb.action.USB_DEVICE_ATTACHED',
    'android.hardware.usb.action.USB_DEVICE_DETACHED', 'android.intent.action.HEADSET_PLUG',
    'android.intent.action.ANALOG_AUDIO_DOCK_PLUG', 'android.intent.action.DIGITAL_AUDIO_DOCK_PLUG',
    'android.intent.action.HDMI_AUDIO_PLUG', 'android.intent.action.USB_AUDIO_ACCESSORY_PLUG',
    'android.intent.action.USB_AUDIO_DEVICE_PLUG', 'android.net.conn.CONNECTIVITY_CHANGE',
    'android.net.conn.CONNECTIVITY_CHANGE_IMMEDIATE', 'android.net.conn.DATA_ACTIVITY_CHANGE',
    'android.net.conn.BACKGROUND_DATA_SETTING_CHANGED', 'android.net.conn.CAPTIVE_PORTAL_TEST_COMPLETED',
    'android.nfc.action.LLCP_LINK_STATE_CHANGED', 'com.android.nfc_extras.action.RF_FIELD_ON_DETECTED',
    'com.android.nfc_extras.action.RF_FIELD_OFF_DETECTED', 'com.android.nfc_extras.action.AID_SELECTED',
    'android.nfc.action.TRANSACTION_DETECTED', 'android.intent.action.CLEAR_DNS_CACHE',
    'android.intent.action.PROXY_CHANGE', 'android.os.UpdateLock.UPDATE_LOCK_CHANGED',
    'android.intent.action.DREAMING_STARTED', 'android.intent.action.DREAMING_STOPPED',
    'android.intent.action.ANY_DATA_STATE', 'com.android.server.WifiManager.action.START_SCAN',
    'com.android.server.WifiManager.action.DELAYED_DRIVER_STOP', 'android.net.wifi.WIFI_STATE_CHANGED',
    'android.net.wifi.WIFI_AP_STATE_CHANGED', 'android.net.wifi.WIFI_SCAN_AVAILABLE',
    'android.net.wifi.SCAN_RESULTS', 'android.net.wifi.RSSI_CHANGED', 'android.net.wifi.STATE_CHANGE',
    'android.net.wifi.LINK_CONFIGURATION_CHANGED', 'android.net.wifi.CONFIGURED_NETWORKS_CHANGE',
    'android.net.wifi.supplicant.CONNECTION_CHANGE', 'android.net.wifi.supplicant.STATE_CHANGE',
    'android.net.wifi.p2p.STATE_CHANGED', 'android.net.wifi.p2p.DISCOVERY_STATE_CHANGE',
    'android.net.wifi.p2p.THIS_DEVICE_CHANGED', 'android.net.wifi.p2p.PEERS_CHANGED',
    'android.net.wifi.p2p.CONNECTION_STATE_CHANGE', 'android.net.wifi.p2p.PERSISTENT_GROUPS_CHANGED',
    'android.net.conn.TETHER_STATE_CHANGED', 'android.net.conn.INET_CONDITION_ACTION',
    'android.intent.action.EXTERNAL_APPLICATIONS_AVAILABLE', 'android.intent.action.EXTERNAL_APPLICATIONS_UNAVAILABLE',
    'android.intent.action.AIRPLANE_MODE', 'android.intent.action.ADVANCED_SETTINGS',
    'android.intent.action.BUGREPORT_FINISHED', 'android.intent.action.ACTION_IDLE_MAINTENANCE_START',
    'android.intent.action.ACTION_IDLE_MAINTENANCE_END', 'android.intent.action.SERVICE_STATE',
    'android.intent.action.RADIO_TECHNOLOGY', 'android.intent.action.EMERGENCY_CALLBACK_MODE_CHANGED',
    'android.intent.action.SIG_STR', 'android.intent.action.DATA_CONNECTION_FAILED',
    'android.intent.action.SIM_STATE_CHANGED', 'android.intent.action.NETWORK_SET_TIME',
    'android.intent.action.NETWORK_SET_TIMEZONE', 'android.intent.action.ACTION_SHOW_NOTICE_ECM_BLOCK_OTHERS',
    'android.intent.action.ACTION_MDN_STATE_CHANGED', 'android.provider.Telephony.SPN_STRINGS_UPDATED',
    'android.provider.Telephony.SIM_FULL', 'com.android.internal.telephony.data-restart-trysetup',
    'com.android.internal.telephony.data-stall'
]

# Error and warning messages
EXPORTED_AND_PERMISSION_TAG = ("The {tag} {tag_name} tag is exported and protected by a permission, "
                               "but the permission can be obtained by malicious apps installed "
                               "prior to this one. More info: "
                               "https://github.com/commonsguy/cwac-security/blob/master/PERMS.md. "
                               "Failing to protect {tag} tags could leave them vulnerable to attack "
                               "by malicious apps. The {tag} tags should be reviewed for "
                               "vulnerabilities, such as injection and information leakage.")
EXPORTED_IN_PROTECTED = ("The {tag} {tag_name} is exported, but the associated Intents can only be sent "
                         "by SYSTEM level apps. They could still potentially be vulnerable, "
                         "if the Intent carries data that is tainted (2nd order injection)")
EXPORTED = ("The {tag} {tag_name} is exported, but not protected by any permissions. Failing to protect "
            "{tag} tags could leave them vulnerable to attack by malicious apps. The "
            "{tag} tags should be reviewed for vulnerabilities, such as injection and information leakage.")

EXPORTED_TAGS_ISSUE_NAME = "Exported tags"

# Define Enum classes for components
class Receiver(Enum):
    id = 1
    type = "receiver"
    parent = "exportedReceivers"


class Provider(Enum):
    id = 2
    type = "provider"
    parent = "exportedContentProviders"


class Activity(Enum):
    id = 3
    type = "activity"
    parent = "exportedActivities"


class Broadcast(Enum):
    id = 4
    type = "broadcast"
    parent = "exportedBroadcasts"


class Service(Enum):
    id = 5
    parent = "exportedServices"
    type = "service"


TAG_INFO = {"receiver": Receiver, "provider": Provider, "activity": Activity,
            "activity-alias": Activity, "service": Service}

# Plugin class to check exported tags
class ExportedTags(ManifestPlugin):
    all_files = None  # Define variable to avoid violating Liskov Substitution Principle

    def __init__(self):
        # Update super() to be compatible with Python 3.8
        super().__init__(category="manifest", name=EXPORTED_TAGS_ISSUE_NAME)
        self.bad_exported_tags = ("activity", "activity-alias", "service", "receiver", "provider")
        self.package_name: str = ""  # Explicit variable definition

    def run(self) -> None:
        """
        Execute the check on exported tags in the manifest file.

        This function searches for exported tags in the manifest file and checks for security issues.
        """
        # Ensure the manifest file exists
        if not hasattr(self, "manifest_xml") or not self.manifest_xml:
            log.error("Manifest XML is not available")
            return

        # Check each type of exported tags
        for tag in self.bad_exported_tags:
            all_tags_of_type_tag = self.manifest_xml.getElementsByTagName(tag)
            for possibly_vulnerable_tag in all_tags_of_type_tag:
                self._check_manifest_issues(possibly_vulnerable_tag, tag, self.manifest_path)

        # Add arguments from Java files to the issues
        java_files = list(java_files_from_files(self.all_files))
        self._add_exported_tags_arguments_to_issue(java_files)

    def _check_manifest_issues(self, possibly_vulnerable_tag: Any, tag: str, file_object: str) -> None:
        """
        Check exported tags for security vulnerabilities or warnings.

        :param possibly_vulnerable_tag: The tag as an XML object
        :param str tag: The tag name
        :param str file_object: The path to the manifest file
        """
        # Check for attribute presence
        is_exported = "android:exported" in possibly_vulnerable_tag.attributes.keys()
        has_permission = "android:permission" in possibly_vulnerable_tag.attributes.keys()
        has_intent_filters = len(possibly_vulnerable_tag.getElementsByTagName("intent-filter")) > 0

        # Retrieve attribute values
        exported = (possibly_vulnerable_tag.attributes.get("android:exported").value.lower() 
                   if is_exported else None)
        tag_is_provider = tag.lower() == "provider"

        # Get tag name with error handling
        try:
            tag_name = possibly_vulnerable_tag.attributes.get("android:name").value
        except AttributeError:
            log.warning(f"Tag {tag} has no name attribute, skipping")
            tag_name = "unknown_tag"

        # Get Enum information based on tag type
        info_enum = TAG_INFO[tag]

        # If the tag is not exported, do nothing
        if exported == "false":
            return

        # Check different cases
        if (exported is not None and exported != "false") or tag_is_provider:
            if tag_is_provider and self.min_sdk > 16 or self.target_sdk > 16:
                log.debug(f"Provider {tag_name} is not vulnerable under SDK conditions")
                return

            if has_permission and self.min_sdk < 20:
                self._add_issue(
                    name=self.name,
                    description=EXPORTED_AND_PERMISSION_TAG.format(tag=tag, tag_name=tag_name),
                    severity=Severity.INFO,
                    file_object=file_object,
                    apk_exploit_dict={"exported_enum": info_enum, "tag_name": tag_name, "package_name": self.package_name}
                )
            elif exported and not has_intent_filters:
                self._add_issue(
                    name=self.name,
                    description=EXPORTED.format(tag=tag, tag_name=tag_name),
                    severity=Severity.WARNING,
                    file_object=file_object,
                    apk_exploit_dict={"exported_enum": info_enum, "tag_name": tag_name, "package_name": self.package_name}
                )

        # Check filters
        for intent_filter in possibly_vulnerable_tag.getElementsByTagName("intent-filter"):
            for action in intent_filter.getElementsByTagName("action"):
                try:
                    protected = action.attributes["android:name"].value in PROTECTED_BROADCASTS
                except KeyError:
                    log.debug("Action doesn't have a name field, continuing execution")
                    continue

                if protected:
                    name = "Protected Exported Tags"
                    description = EXPORTED_IN_PROTECTED.format(tag=tag, tag_name=tag_name)
                    severity = Severity.INFO
                elif has_permission and self.min_sdk < 20:
                    name = "Exported Tag With Permission"
                    description = EXPORTED_AND_PERMISSION_TAG.format(tag=tag, tag_name=tag_name)
                    severity = Severity.INFO
                else:
                    name = self.name
                    description = EXPORTED.format(tag=tag, tag_name=tag_name)
                    severity = Severity.WARNING

                self._add_issue(
                    name=name,
                    description=description,
                    severity=severity,
                    file_object=file_object,
                    apk_exploit_dict={"exported_enum": info_enum, "tag_name": tag_name, "package_name": self.package_name}
                )

    def _add_issue(self, name: str, description: str, severity: Severity, file_object: str, 
                   apk_exploit_dict: Dict[str, Any]) -> None:
        """
        Add an issue to the list of issues.

        :param str name: Name of the issue
        :param str description: Description of the issue
        :param Severity severity: Severity level
        :param str file_object: Path to the file
        :param Dict[str, Any] apk_exploit_dict: Dictionary containing exploit data
        """
        issue = Issue(
            category="Manifest",
            severity=severity,
            name=name,
            description=description,
            file_object=file_object,
            apk_exploit_dict=apk_exploit_dict
        )
        self.issues.append(issue)
        log.info(f"Added issue: {name} in {file_object}")

    def _add_exported_tags_arguments_to_issue(self, java_files: List[str]) -> None:
        """
        Add arguments from Java files to the issues.

        :param List[str] java_files: List of Java file paths
        """
        for issue in self.issues:
            try:
                file_name = issue.apk_exploit_dict["tag_name"].replace(".", os.sep)
            except (KeyError, AttributeError) as e:
                log.exception(f"Tag name error: {str(e)}")
                continue

            self._get_arguments_for_method_from_file(java_files, issue, name_to_search_for=file_name)

    def _get_arguments_for_method_from_file(self, java_files: List[str], issue: Issue, 
                                          name_to_search_for: str) -> None:
        """
        Retrieve arguments from a Java file based on the component name.

        :param List[str] java_files: List of Java file paths
        :param Issue issue: The issue to which arguments are added
        :param str name_to_search_for: Name of the file or component to search for
        """
        added = False
        for java_file in java_files:
            if name_to_search_for not in java_file:
                continue

            try:
                with open(java_file, "r", encoding="utf-8") as java_file_to_read:  # Add UTF-8 encoding
                    file_contents = java_file_to_read.read()
            except IOError as e:
                log.debug(f"Error reading file {java_file}: {str(e)}")
                continue

            try:
                parsed_tree = javalang.parse.parse(file_contents)
            except (javalang.parser.JavaSyntaxError, IndexError) as e:
                log.debug(f"Error parsing file {java_file}: {str(e)}, continuing")
                continue

            # Initialize the arguments list
            issue.apk_exploit_dict.setdefault("arguments", [])

            # Search for method declarations for the component type
            for path, method_declaration in parsed_tree.filter(MethodDeclaration):
                if method_declaration.name in COMPONENT_ENTRIES[issue.apk_exploit_dict["exported_enum"].type.value]:
                    # Search for method invocations that might contain arguments
                    for _, method_invocation in parsed_tree.filter(MethodInvocation):
                        if method_invocation.member in EXTRAS_METHOD_NAMES:
                            if not method_invocation.arguments:
                                continue

                            for argument in method_invocation.arguments:
                                if not isinstance(argument, Literal):
                                    continue

                                # Use walrus operator to check and add the value in one step
                                if (value := argument.value) not in issue.apk_exploit_dict["arguments"]:
                                    added = True
                                    issue.apk_exploit_dict["arguments"].append(value)

            if added:
                log.info(f"Arguments added to issue for {name_to_search_for} in {java_file}")
                return


# Create an instance of the class
plugin = ExportedTags()