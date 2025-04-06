from qark.scanner.plugin import ManifestPlugin
from qark.issue import Severity, Issue
import logging

log = logging.getLogger(__name__)

class ManifestBackupAllowed(ManifestPlugin):
    """
    This plugin checks whether the `allowBackup` attribute is set to true in the AndroidManifest.xml file.
    If allowed, it can potentially lead to data theft via local attacks such as adb backup.
    """
    def __init__(self):
        super(ManifestBackupAllowed, self).__init__(category="manifest", 
                                                   name="Backup is allowed in manifest",
                                                   description=(
                                                       "Backups enabled: Potential for data theft via local attacks "
                                                       "via adb backup, if the device has USB debugging enabled. "
                                                       "More info: "
                                                       "http://developer.android.com/reference/android/R.attr.html#allowBackup"))

        self.severity = Severity.WARNING

    def run(self):
        try:
            # Get all application tags in the manifest XML
            application_sections = self.manifest_xml.getElementsByTagName("application")

            for application in application_sections:
                # Check if 'android:allowBackup' attribute exists in the application tag
                if "android:allowBackup" in application.attributes:
                    # If it exists, append an issue
                    self.issues.append(Issue(
                        category=self.category,
                        severity=self.severity,
                        name=self.name,
                        description=self.description,
                        file_object=self.manifest_path
                    ))
        except Exception as e:
            log.error(f"Error processing manifest for backup check: {e}")

plugin = ManifestBackupAllowed()
