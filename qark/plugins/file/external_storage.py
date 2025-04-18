import logging
from javalang.tree import MethodInvocation
from qark.issue import Severity, Issue
from qark.scanner.plugin import CoroutinePlugin

log = logging.getLogger(__name__)

EXTERNAL_STORAGE_DESCRIPTION = (
    "Reading files stored on {storage_location} makes it vulnerable to data injection attacks. "
    "Note that this code does no error checking and there is no security enforced with these files. "
    "For example, any application holding WRITE_EXTERNAL_STORAGE can write to these files. "
    "Reference: https://developer.android.com/reference/android/content/Context.html"
)

EXTERNAL_FILES_DIR_METHOD = 'getExternalFilesDir'
EXTERNAL_FILES_DIRS_METHOD = 'getExternalFilesDirs'
EXTERNAL_MEDIA_DIR_METHOD = 'getExternalMediaDirs'
EXTERNAL_STORAGE_PUBLIC_DIR_METHOD = 'getExternalStoragePublicDirectory'


class ExternalStorage(CoroutinePlugin):
    """
    This plugin checks if any of the following methods are used:
    - getExternalFilesDir
    - getExternalFilesDirs
    - getExternalMediaDirs
    - getExternalStoragePublicDirectory
    
    These methods are associated with external storage access and may pose security risks.
    """
    
    def __init__(self):
        super(ExternalStorage, self).__init__(category="file", name="External storage used", description=EXTERNAL_STORAGE_DESCRIPTION)
        self.severity = Severity.WARNING

    def run_coroutine(self):
        """
        Scans method invocations for the use of external storage access methods.
        If any of the methods from the list are called, it logs an issue.
        """
        while True:
            _, method_invocation = (yield)

            if not isinstance(method_invocation, MethodInvocation):
                continue

            storage_location = None
            # Check for any method invocation matching the known external storage access methods
            if method_invocation.member == EXTERNAL_FILES_DIR_METHOD or method_invocation.member == EXTERNAL_FILES_DIRS_METHOD:
                storage_location = "External Storage"
            elif method_invocation.member == EXTERNAL_MEDIA_DIR_METHOD:
                storage_location = "External Media Directory"
            elif method_invocation.member == EXTERNAL_STORAGE_PUBLIC_DIR_METHOD:
                storage_location = "External Storage Public Directory"

            # If a storage location is identified, create an issue
            if storage_location:
                self.issues.append(Issue(
                    category=self.category, severity=self.severity, name=self.name,
                    description=self.description.format(storage_location=storage_location),
                    file_object=self.file_path,
                    line_number=method_invocation.position)
                )


plugin = ExternalStorage()
