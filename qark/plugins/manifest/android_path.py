import logging
import xml.etree.ElementTree as ET

from qark.issue import Severity, Issue
from qark.scanner.plugin import ManifestPlugin

log = logging.getLogger(__name__)

PATH_USAGE_DESCRIPTION = (
    "android:path means that the permission applies to the exact path declared "
    "in android:path. This expression does not protect the sub-directories."
)

class AndroidPath(ManifestPlugin):
    def __init__(self):
        super(AndroidPath, self).__init__(category="manifest", name="android:path tag used",
                                          description=PATH_USAGE_DESCRIPTION)

        self.severity = Severity.WARNING

    def run(self):
        try:
            # Parse the manifest XML file
            tree = ET.parse(self.manifest_path)
            root = tree.getroot()

            # Loop through all <intent-filter> elements and check for android:path
            for application in root.findall(".//application"):
                for intent_filter in application.findall(".//intent-filter"):
                    for data in intent_filter.findall("data"):
                        path = data.get("android:path")
                        if path:
                            self.issues.append(Issue(
                                category=self.category, severity=self.severity, name=self.name,
                                description=self.description,
                                file_object=self.manifest_path,
                                line_number=self.get_line_number(data)
                            ))
        except Exception as e:
            log.error(f"Error processing manifest for android:path check: {e}")

    def get_line_number(self, element):
        """Helper method to get the line number of an XML element."""
        try:
            # Trying to get the line number from the XML element
            return element.sourceline
        except AttributeError:
            return None


plugin = AndroidPath()
