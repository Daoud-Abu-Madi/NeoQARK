import logging
import re
from qark.issue import Severity, Issue
from qark.scanner.plugin import FileContentsPlugin

log = logging.getLogger(__name__)

API_KEY_REGEX = re.compile(r'(?=.{20,})(?=.+\d)(?=.+[a-z])(?=.+[A-Z])(?=.+[-_])')
SPECIAL_CHARACTER_REGEX = re.compile(r'(?=.+[!$%^&*()_+|~=`{}\[\]:<>?,./])')
BLACKLISTED_EXTENSIONS = (".apk", ".dex", ".png", ".jar")

API_KEY_DESCRIPTION = "Please confirm and investigate the API key to determine its severity."


class JavaAPIKeys(FileContentsPlugin):
    """
    This plugin checks for potential API keys in the code. It looks for patterns matching
    the API_KEY_REGEX and ensures they do not match the SPECIAL_CHARACTER_REGEX.
    """
    
    def __init__(self):
        super().__init__(category="file", name="Potential API Key found", description=API_KEY_DESCRIPTION)
        self.severity = Severity.INFO

    def run(self):
        """
        Scans through the file contents looking for potential API keys based on the defined regex patterns.
        If a potential API key is found, an issue is logged.
        """
        # Skip files with blacklisted extensions
        if any(self.file_path.endswith(extension) for extension in BLACKLISTED_EXTENSIONS):
            return

        # Iterate through each line in the file
        for line_number, line in enumerate(self.file_contents.split("\n")):
            # Check each word in the line for potential API keys
            for word in line.split():
                # If it matches the API key pattern and not the special character pattern, it's a potential key
                if re.search(API_KEY_REGEX, word) and not re.search(SPECIAL_CHARACTER_REGEX, word):
                    self.issues.append(
                        Issue(
                            category=self.category,
                            severity=self.severity,
                            name=self.name,
                            description=self.description,
                            file_object=self.file_path,
                            line_number=(line_number, 0)
                        )
                    )


plugin = JavaAPIKeys()
