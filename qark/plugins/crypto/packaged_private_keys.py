import logging
import re

from qark.issue import Severity, Issue
from qark.plugins.helpers import run_regex
from qark.scanner.plugin import FileContentsPlugin

log = logging.getLogger(__name__)

class PackagedPrivateKeys(FileContentsPlugin):
    PRIVATE_KEY_REGEXES = (
        re.compile(r'PRIVATE\sKEY', re.IGNORECASE),  # Added re.IGNORECASE for better matching
    )

    def __init__(self):
        super().__init__(category="crypto", name="Encryption keys are packaged with the application")
        self.severity = Severity.VULNERABILITY

    def run(self):
        for regex in PackagedPrivateKeys.PRIVATE_KEY_REGEXES:
            try:
                if run_regex(self.file_path, regex):
                    log.debug("Private key potentially found in the file: %s", self.file_path)
                    description = "A private key may be embedded in your application in the following file:"
                    self.issues.append(
                        Issue(self.category, self.name, self.severity, description, file_object=self.file_path)
                    )
            except Exception as e:
                log.error(f"Error processing file {self.file_path}: {e}")
                continue

plugin = PackagedPrivateKeys()
