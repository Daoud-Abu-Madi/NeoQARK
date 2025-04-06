import logging
import re

from qark.issue import Severity, Issue
from qark.scanner.plugin import JavaASTPlugin

log = logging.getLogger(__name__)

CHECK_PERMISSIONS_DESCRIPTION = (
    "Be careful with use of {used_permission} permission function\nApp maybe vulnerable to Privilege escalation or "
    "Confused Deputy Attack. This function can grant access to malicious application, lacking the "
    "appropriate permission, by assuming your applications permissions. This means a malicious application, "
    "without appropriate permissions, can bypass its permission check by using your application"
    "permission to get access to otherwise denied resources. Use - {recommended_permission}CallingPermission instead. "
    "Reference: https://developer.android.com/reference/android/content/Context.html\n"
)

CHECK_PERMISSION_REGEX = re.compile(r'checkCallingOrSelfPermission|checkCallingOrSelfUriPermission|checkPermission')
ENFORCE_PERMISSION_REGEX = re.compile(
    r'enforceCallingOrSelfPermission|enforceCallingOrSelfUriPermission|enforcePermission'
)

class CheckPermissions(JavaASTPlugin):
    def __init__(self):
        super(CheckPermissions, self).__init__(category="manifest",
                                               name="Potentially vulnerable check permission function called",
                                               description=CHECK_PERMISSIONS_DESCRIPTION)
        self.severity = Severity.WARNING

    def run(self):
        # Only check if the Java file imports "Context"
        if any("Context" in imp.path for imp in self.java_ast.imports):
            # Search for insecure permission checks and add issues if found
            self._check_for_permissions(self.file_contents)

    def _check_for_permissions(self, file_contents):
        """Helper method to check for vulnerable permission calls and log issues."""
        # Check for 'check' functions
        if re.search(CHECK_PERMISSION_REGEX, file_contents):
            self.issues.append(Issue(
                category=self.category, severity=self.severity, name=self.name,
                description=self.description.format(used_permission="Check", recommended_permission="check"),
                file_object=self.file_path
            ))

        # Check for 'enforce' functions
        if re.search(ENFORCE_PERMISSION_REGEX, file_contents):
            self.issues.append(Issue(
                category=self.category, severity=self.severity, name=self.name,
                description=self.description.format(used_permission="Enforce", recommended_permission="enforce"),
                file_object=self.file_path
            ))

plugin = CheckPermissions()
