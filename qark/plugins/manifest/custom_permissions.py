import logging
from xml.etree import ElementTree

from qark.issue import Severity, Issue
from qark.scanner.plugin import ManifestPlugin

log = logging.getLogger(__name__)

SIGNATURE_OR_SIGNATURE_OR_SYSTEM_DESCRIPTION = (
    "This permission can be obtained by malicious apps installed prior to this "
    "one, without the proper signature. Applicable to Android Devices prior to "
    "L (Lollipop). More info: "
    "https://github.com/commonsguy/cwac-security/blob/master/PERMS.md"
)

SIGNATURE_OR_SIGNATURE_OR_SYSTEM_SEVERITY = Severity.WARNING

DANGEROUS_PERMISSION_DESCRIPTION = (
    "This permission can give a requesting application access to private user data or control over the "
    "device that can negatively impact the user."
)


class CustomPermissions(ManifestPlugin):
    def __init__(self):
        super(CustomPermissions, self).__init__(category="manifest",
                                                name="Custom permissions are enabled in the manifest",
                                                description=(
                                                    "This permission can be obtained by malicious apps installed prior to this "
                                                    "one, without the proper signature. Applicable to Android Devices prior to "
                                                    "L (Lollipop). More info: "
                                                    "https://github.com/commonsguy/cwac-security/blob/master/PERMS.md"))
        self.severity = Severity.WARNING

    def run(self):
        try:
            # Parse the manifest XML file for permission elements
            tree = ElementTree.parse(self.manifest_path)
            root = tree.getroot()

            # Loop over all permission nodes in the manifest file
            for permission in root.findall(".//permission"):
                protection_level = permission.attrib.get("android:protectionLevel")
                
                if protection_level:
                    if protection_level in ("signature", "signatureOrSystem") and self.min_sdk < 21:
                        # Check for permissions that allow for weak security
                        self.issues.append(Issue(
                            category=self.category,
                            severity=SIGNATURE_OR_SIGNATURE_OR_SYSTEM_SEVERITY,
                            name=self.name,
                            description=SIGNATURE_OR_SIGNATURE_OR_SYSTEM_DESCRIPTION,
                            file_object=self.manifest_path
                        ))

                    elif protection_level == "dangerous":
                        # Flag dangerous permissions
                        self.issues.append(Issue(
                            category=self.category,
                            severity=Severity.INFO,
                            name=self.name,
                            description=DANGEROUS_PERMISSION_DESCRIPTION,
                            file_object=self.manifest_path
                        ))

        except Exception as e:
            log.error(f"Error processing the manifest for custom permissions check: {e}")


plugin = CustomPermissions()
