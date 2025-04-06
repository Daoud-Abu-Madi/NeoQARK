import logging
import re
import xml.etree.ElementTree as ET

from qark.issue import Severity, Issue
from qark.scanner.plugin import ManifestPlugin

log = logging.getLogger(__name__)

HARDCODED_API_KEY_REGEX = re.compile(r'api_key|api|key', re.IGNORECASE)

API_KEY_DESCRIPTION = "Please confirm and investigate for potential API keys to determine severity."


class APIKeys(ManifestPlugin):
    def __init__(self):
        super(APIKeys, self).__init__(category="manifest", name="Potential API Key found",
                                      description=API_KEY_DESCRIPTION)
        self.severity = Severity.INFO

    def run(self):
        try:
            # Parse the manifest XML file for better performance and accuracy
            tree = ET.parse(self.manifest_path)
            root = tree.getroot()

            # Search for any occurrences of API keys in the XML elements' attributes or values
            for application in root.findall(".//application"):
                for meta_data in application.findall(".//meta-data"):
                    value = meta_data.get("value")
                    if value and re.search(HARDCODED_API_KEY_REGEX, value):
                        self.issues.append(Issue(
                            category=self.category, severity=self.severity, name=self.name,
                            description=self.description,
                            file_object=self.manifest_path,
                            line_number=self.get_line_number(meta_data)
                        ))
        except Exception as e:
            log.error(f"Error processing manifest for API keys check: {e}")

    def get_line_number(self, element):
        """Helper method to get the line number of an XML element."""
        try:
            return element.sourceline
        except AttributeError:
            return None


plugin = APIKeys()
