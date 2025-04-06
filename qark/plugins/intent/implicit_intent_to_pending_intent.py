import logging
import re

from javalang.tree import MethodInvocation, ClassCreator, ReferenceType

from qark.issue import Severity, Issue
from qark.scanner.plugin import CoroutinePlugin

log = logging.getLogger(__name__)

# Define methods related to PendingIntent
PENDING_INTENT_METHODS = ("getActivities", "getService", "getActivity", "getBroadcast")

# Regular expression to search for methods related to PendingIntent
PENDING_INTENT_REGEX = re.compile("({})".format("|".join(PENDING_INTENT_METHODS)))


class ImplicitIntentToPendingIntent(CoroutinePlugin):
    """
    This plugin checks if a `new Intent` is passed into any of the `PENDING_INTENT_METHODS`.
    If found, a vulnerability is reported.
    """
    def __init__(self):
        super(ImplicitIntentToPendingIntent, self).__init__(
            category="intent", 
            name="Implicit Pending Intent found",
            description=(
                "For security reasons, the Intent supplied here should almost always be explicit. "
                "A malicious app could potentially intercept, redirect, and/or modify this Intent. "
                "Pending Intents retain the UID of your app and all permissions, allowing another "
                "app to act on your behalf. Refer to: "
                "https://developer.android.com/reference/android/app/PendingIntent.html"
            )
        )
        self.severity = Severity.VULNERABILITY
        self.current_file = None

    def can_run_coroutine(self):
        """
        Check if the file contains 'new Intent' and 'PendingIntent' related methods
        """
        if "new Intent" not in self.file_contents or not re.search(PENDING_INTENT_REGEX, self.file_contents):
            return False

        if not any("PendingIntent" in imported_declaration.path for imported_declaration in self.java_ast.imports):
            # If PendingIntent is not imported, the file is not vulnerable
            return False

        return True

    def run_coroutine(self):
        while True:
            _, pending_intent_invocation = (yield)

            if not isinstance(pending_intent_invocation, MethodInvocation):
                continue

            if pending_intent_invocation.member not in PENDING_INTENT_METHODS:
                continue

            # Check each argument passed to the method for a new Intent()
            for method_argument in pending_intent_invocation.arguments:
                for _, creation in method_argument.filter(ClassCreator):
                    # Check if the creation of Intent is without arguments
                    if len(creation.arguments) in (0, 1):  
                        for _, reference_declaration in creation.filter(ReferenceType):
                            if reference_declaration.name == "Intent":
                                # If an implicit Intent is found, create an issue
                                self.issues.append(Issue(
                                    category=self.category,
                                    severity=self.severity,
                                    name=self.name,
                                    description=self.description,
                                    file_object=self.file_path
                                ))


plugin = ImplicitIntentToPendingIntent()
