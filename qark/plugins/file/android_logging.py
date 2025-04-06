import logging
from javalang.tree import MethodInvocation
from qark.issue import Severity, Issue
from qark.scanner.plugin import CoroutinePlugin

log = logging.getLogger(__name__)

ANDROID_LOGGING_DESCRIPTION = (
    "Logs are detected. This may allow potential leakage of information from Android applications. Logs should never be"
    " compiled into an application except during development. Reference: "
    "https://developer.android.com/reference/android/util/Log.html"
)

ANDROID_LOGGING_METHODS = ("v", "d", "i", "w", "e")


class AndroidLogging(CoroutinePlugin):
    """
    This plugin checks if any logging methods are used in the application code,
    which could potentially leak sensitive information.
    """

    def __init__(self):
        super().__init__(category="file", name="Logging found", description=ANDROID_LOGGING_DESCRIPTION)
        self.severity = Severity.WARNING

    async def run_coroutine(self):
        """
        Coroutine to scan for any log method calls such as Log.d(), Log.e(), etc.
        It adds an issue whenever one of these methods is found.
        """
        while True:
            _, method_invocation = await self.yield_data()

            if not isinstance(method_invocation, MethodInvocation):
                continue

            # Check if it's a Log method invocation
            if method_invocation.qualifier == "Log" and method_invocation.member in ANDROID_LOGGING_METHODS:
                self.issues.append(
                    Issue(
                        category=self.category,
                        severity=self.severity,
                        name=self.name,
                        description=self.description,
                        file_object=self.file_path,
                        line_number=method_invocation.position
                    )
                )


plugin = AndroidLogging()
