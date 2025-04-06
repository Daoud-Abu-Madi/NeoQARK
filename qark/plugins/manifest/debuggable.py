import logging
from xml.etree import ElementTree

from qark.issue import Severity, Issue
from qark.scanner.plugin import ManifestPlugin

log = logging.getLogger(__name__)

class DebuggableManifest(ManifestPlugin):
    def __init__(self):
        super(DebuggableManifest, self).__init__(category="manifest", name="Manifest is manually set to debug",
                                                 description=(
                                                     "The android:debuggable flag is manually set to true in the"
                                                     " AndroidManifest.xml. This will cause your application to be debuggable "
                                                     "in production builds and can result in data leakage "
                                                     "and other security issues. It is not necessary to set the "
                                                     "android:debuggable flag in the manifest, it will be set appropriately "
                                                     "automatically by the tools. More info: "
                                                     "http://developer.android.com/guide/topics/manifest/application-element.html#debug"))
        self.severity = Severity.VULNERABILITY

    def run(self):
        try:
            # Parse the manifest XML file
            tree = ElementTree.parse(self.manifest_path)
            root = tree.getroot()

            # Check the "application" tag for the debuggable attribute
            for application in root.findall(".//application"):
                debuggable = application.attrib.get("android:debuggable")
                if debuggable and debuggable.lower() == "true":
                    self.issues.append(Issue(
                        category=self.category,
                        severity=self.severity,
                        name=self.name,
                        description=self.description,
                        file_object=self.manifest_path
                    ))
        except Exception as e:
            log.error(f"Error processing the AndroidManifest.xml for debuggable flag: {e}")


plugin = DebuggableManifest()
