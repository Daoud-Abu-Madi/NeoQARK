import logging
import os
import javalang
from xml.etree import ElementTree
from qark.issue import Severity, Issue
from qark.scanner.plugin import ManifestPlugin
from qark.plugins.helpers import java_files_from_files

log = logging.getLogger(__name__)

COMPONENT_ENTRIES = {
    "activity": {"onCreate", "onStart"},
    "activity-alias": {"onCreate", "onStart"},
    "receiver": {"onReceive", },
    "service": {"onCreate", "onBind", "onStartCommand", "onHandleIntent"},
    "provider": {"onReceive", }
}

# it seems like get, getInt, getString are the ones that are used for decompiled APKs
EXTRAS_METHOD_NAMES = [
    'getExtras',
    'getStringExtra',
    'getIntExtra',
    'getIntArrayExtra',
    'getFloatExtra',
    'getFloatArrayExtra',
    'getDoubleExtra',
    'getDoubleArrayExtra',
    'getCharExtra',
    'getCharArrayExtra',
    'getByteExtra',
    'getByteArrayExtra',
    'getBundleExtra',
    'getBooleanExtra',
    'getBooleanArrayExtra',
    'getCharSequenceArrayExtra',
    'getCharSequenceArrayListExtra',
    'getCharSequenceExtra',
    'getIntegerArrayListExtra',
    'getLongArrayExtra',
    'getLongExtra',
    'getParcelableArrayExtra',
    'getParcelableArrayListExtra',
    'getParcelableExtra',
    'getSerializableExtra',
    'getShortArrayExtra',
    'getShortExtra',
    'getStringArrayExtra',
    'getStringArrayListExtra',
    'getString',
    'getInt',
]

PROTECTED_BROADCASTS = ['android.intent.action.SCREEN_OFF', 'android.intent.action.SCREEN_ON',
                        'android.intent.action.USER_PRESENT', 'android.intent.action.TIME_TICK',
                        'android.intent.action.TIMEZONE_CHANGED', 'android.intent.action.BOOT_COMPLETED',
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
                        'android.intent.action.NEW_OUTGOING_CALL', 'android.intent.action.REBOOT',
                        'android.intent.action.DOCK_EVENT', 'android.intent.action.MASTER_CLEAR_NOTIFICATION',
                        'android.intent.action.USER_ADDED', 'android.intent.action.USER_REMOVED',
                        'android.intent.action.USER_STOPPED', 'android.intent.action.USER_BACKGROUND',
                        'android.intent.action.USER_FOREGROUND', 'android.intent.action.USER_SWITCHED',
                        'android.app.action.ENTER_CAR_MODE', 'android.app.action.EXIT_CAR_MODE',
                        'android.app.action.ENTER_DESK_MODE', 'android.app.action.EXIT_DESK_MODE',
                        'android.appwidget.action.APPWIDGET_UPDATE_OPTIONS',
                        'android.appwidget.action.APPWIDGET_DELETED', 'android.appwidget.action.APPWIDGET_DISABLED',
                        'android.appwidget.action.APPWIDGET_ENABLED', 'android.backup.intent.RUN',
                        'android.backup.intent.CLEAR', 'android.backup.intent.INIT',
                        'android.bluetooth.adapter.action.STATE_CHANGED',
                        'android.bluetooth.adapter.action.SCAN_MODE_CHANGED',
                        'android.bluetooth.adapter.action.DISCOVERY_STARTED',
                        'android.bluetooth.adapter.action.DISCOVERY_FINISHED',
                        'android.bluetooth.adapter.action.LOCAL_NAME_CHANGED',
                        'android.bluetooth.adapter.action.CONNECTION_STATE_CHANGED',
                        'android.bluetooth.device.action.FOUND', 'android.bluetooth.device.action.DISAPPEARED',
                        'android.bluetooth.device.action.CLASS_CHANGED',
                        'android.bluetooth.device.action.ACL_CONNECTED',
                        'android.bluetooth.device.action.ACL_DISCONNECT_REQUESTED',
                        'android.bluetooth.device.action.ACL_DISCONNECTED',
                        'android.bluetooth.device.action.NAME_CHANGED',
                        'android.bluetooth.device.action.BOND_STATE_CHANGED',
                        'android.bluetooth.device.action.NAME_FAILED',
                        'android.bluetooth.device.action.PAIRING_REQUEST',
                        'android.bluetooth.device.action.PAIRING_CANCEL',
                        'android.bluetooth.device.action.CONNECTION_ACCESS_REPLY',
                        'android.bluetooth.headset.profile.action.CONNECTION_STATE_CHANGED',
                        'android.bluetooth.headset.profile.action.AUDIO_STATE_CHANGED',
                        'android.bluetooth.headset.action.VENDOR_SPECIFIC_HEADSET_EVENT',
                        'android.bluetooth.a2dp.profile.action.CONNECTION_STATE_CHANGED',
                        'android.bluetooth.a2dp.profile.action.PLAYING_STATE_CHANGED',
                        'android.bluetooth.input.profile.action.CONNECTION_STATE_CHANGED',
                        'android.bluetooth.pan.profile.action.CONNECTION_STATE_CHANGED',
                        'android.hardware.display.action.WIFI_DISPLAY_STATUS_CHANGED',
                        'android.hardware.usb.action.USB_STATE', 'android.hardware.usb.action.USB_ACCESSORY_ATTACHED',
                        'android.hardware.usb.action.USB_ACCESSORY_ATTACHED',
                        'android.hardware.usb.action.USB_DEVICE_ATTACHED',
                        'android.hardware.usb.action.USB_DEVICE_DETACHED', 'android.intent.action.HEADSET_PLUG',
                        'android.intent.action.ANALOG_AUDIO_DOCK_PLUG', 'android.intent.action.DIGITAL_AUDIO_DOCK_PLUG',
                        'android.intent.action.HDMI_AUDIO_PLUG', 'android.intent.action.USB_AUDIO_ACCESSORY_PLUG',
                        'android.intent.action.USB_AUDIO_DEVICE_PLUG', 'android.net.conn.CONNECTIVITY_CHANGE',
                        'android.net.conn.CONNECTIVITY_CHANGE_IMMEDIATE', 'android.net.conn.DATA_ACTIVITY_CHANGE',
                        'android.net.conn.BACKGROUND_DATA_SETTING_CHANGED',
                        'android.net.conn.CAPTIVE_PORTAL_TEST_COMPLETED', 'android.nfc.action.LLCP_LINK_STATE_CHANGED',
                        'com.android.nfc_extras.action.RF_FIELD_ON_DETECTED',
                        'com.android.nfc_extras.action.RF_FIELD_OFF_DETECTED',
                        'com.android.nfc_extras.action.AID_SELECTED', 'android.nfc.action.TRANSACTION_DETECTED',
                        'android.intent.action.CLEAR_DNS_CACHE', 'android.intent.action.PROXY_CHANGE',
                        'android.os.UpdateLock.UPDATE_LOCK_CHANGED', 'android.intent.action.DREAMING_STARTED',
                        'android.intent.action.DREAMING_STOPPED', 'android.intent.action.ANY_DATA_STATE',
                        'com.android.server.WifiManager.action.START_SCAN',
                        'com.android.server.WifiManager.action.DELAYED_DRIVER_STOP',
                        'android.net.wifi.WIFI_STATE_CHANGED', 'android.net.wifi.WIFI_AP_STATE_CHANGED',
                        'android.net.wifi.WIFI_SCAN_AVAILABLE', 'android.net.wifi.SCAN_RESULTS',
                        'android.net.wifi.RSSI_CHANGED', 'android.net.wifi.STATE_CHANGE',
                        'android.net.wifi.LINK_CONFIGURATION_CHANGED', 'android.net.wifi.CONFIGURED_NETWORKS_CHANGE',
                        'android.net.wifi.supplicant.CONNECTION_CHANGE', 'android.net.wifi.supplicant.STATE_CHANGE',
                        'android.net.wifi.p2p.STATE_CHANGED', 'android.net.wifi.p2p.DISCOVERY_STATE_CHANGE',
                        'android.net.wifi.p2p.THIS_DEVICE_CHANGED', 'android.net.wifi.p2p.PEERS_CHANGED',
                        'android.net.wifi.p2p.CONNECTION_STATE_CHANGE',
                        'android.net.wifi.p2p.PERSISTENT_GROUPS_CHANGED', 'android.net.conn.TETHER_STATE_CHANGED',
                        'android.net.conn.INET_CONDITION_ACTION',
                        'android.intent.action.EXTERNAL_APPLICATIONS_AVAILABLE',
                        'android.intent.action.EXTERNAL_APPLICATIONS_UNAVAILABLE',
                        'android.intent.action.AIRPLANE_MODE', 'android.intent.action.ADVANCED_SETTINGS',
                        'android.intent.action.BUGREPORT_FINISHED',
                        'android.intent.action.ACTION_IDLE_MAINTENANCE_START',
                        'android.intent.action.ACTION_IDLE_MAINTENANCE_END', 'android.intent.action.SERVICE_STATE',
                        'android.intent.action.RADIO_TECHNOLOGY',
                        'android.intent.action.EMERGENCY_CALLBACK_MODE_CHANGED', 'android.intent.action.SIG_STR',
                        'android.intent.action.ANY_DATA_STATE', 'android.intent.action.DATA_CONNECTION_FAILED',
                        'android.intent.action.SIM_STATE_CHANGED', 'android.intent.action.NETWORK_SET_TIME',
                        'android.intent.action.NETWORK_SET_TIMEZONE',
                        'android.intent.action.ACTION_SHOW_NOTICE_ECM_BLOCK_OTHERS',
                        'android.intent.action.ACTION_MDN_STATE_CHANGED',
                        'android.provider.Telephony.SPN_STRINGS_UPDATED', 'android.provider.Telephony.SIM_FULL',
                        'com.android.internal.telephony.data-restart-trysetup',
                        'com.android.internal.telephony.data-stall']

EXPORTED_TAGS_ISSUE_NAME = "Exported tags"


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


class ExportedTags(ManifestPlugin):
    def __init__(self):
        super(ExportedTags, self).__init__(category="manifest", name=EXPORTED_TAGS_ISSUE_NAME)

        self.bad_exported_tags = ("activity", "activity-alias", "service", "receiver", "provider")

    def run(self):
        try:
            tree = ElementTree.parse(self.manifest_path)
            root = tree.getroot()

            # Check each component type for vulnerabilities
            for tag in self.bad_exported_tags:
                components = root.findall(f".//{tag}")
                for component in components:
                    self._check_manifest_issues(component, tag)

            self._add_exported_tags_arguments_to_issue(list(java_files_from_files(self.all_files)))
        except Exception as e:
            log.error(f"Error processing the manifest: {e}")

    def _check_manifest_issues(self, component, tag):
        is_exported = "android:exported" in component.attrib
        has_permission = "android:permission" in component.attrib
        exported_value = component.attrib.get("android:exported")
        tag_name = component.attrib.get("android:name")

        if exported_value == "false":
            return  # Skip if not exported

        # Handle exported tags with or without permission
        if exported_value != "false":
            if has_permission and self.min_sdk < 20:
                self.issues.append(Issue(category="Manifest", severity=Severity.INFO,
                                         name=self.name, description=EXPORTED_AND_PERMISSION_TAG.format(tag=tag, tag_name=tag_name),
                                         file_object=self.manifest_path))
            else:
                self.issues.append(Issue(category="Manifest", severity=Severity.WARNING,
                                         name=self.name, description=EXPORTED.format(tag=tag, tag_name=tag_name),
                                         file_object=self.manifest_path))

    def _add_exported_tags_arguments_to_issue(self, java_files):
        for issue in self.issues:
            try:
                file_name = issue.apk_exploit_dict["tag_name"].replace(".", os.sep)
            except IndexError:
                log.exception("Tag name %s does not have a period in it", issue.apk_exploit_dict["tag_name"])
                return
            self._get_arguments_for_method_from_file(java_files, issue, name_to_search_for=file_name)

    def _get_arguments_for_method_from_file(self, java_files, issue, name_to_search_for):
        added = False
        for java_file in java_files:
            if name_to_search_for not in java_file:
                continue
            try:
                with open(java_file, "r") as file:
                    file_contents = file.read()
                parsed_tree = javalang.parse.parse(file_contents)
                for _, method_declaration in parsed_tree.filter(javalang.tree.MethodDeclaration):
                    if method_declaration.name in COMPONENT_ENTRIES[issue.apk_exploit_dict["exported_enum"].type.value]:
                        for _, method_invocation in parsed_tree.filter(javalang.tree.MethodInvocation):
                            if method_invocation.member in EXTRAS_METHOD_NAMES:
                                for argument in method_invocation.arguments:
                                    if isinstance(argument, javalang.tree.Literal):
                                        if argument.value not in issue.apk_exploit_dict["arguments"]:
                                            added = True
                                            issue.apk_exploit_dict["arguments"].append(argument.value)
                if added:
                    return
            except IOError:
                log.debug("Error reading file %s", java_file)
            except javalang.parser.JavaSyntaxError:
                log.debug("Error parsing file %s", java_file)

plugin = ExportedTags()
