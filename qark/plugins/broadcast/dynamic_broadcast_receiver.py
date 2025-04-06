import logging
from javalang.tree import MethodInvocation
from qark.issue import Issue, Severity
from qark.scanner.plugin import CoroutinePlugin, ManifestPlugin

log = logging.getLogger(__name__)

DYNAMIC_BROADCAST_RECEIVER_DESCRIPTION = (
    "Application that registers a broadcast receiver dynamically is vulnerable to granting unrestricted access to the "
    "broadcast receiver. The receiver will be called with any broadcast Intent that matches the filter."
    " Reference: https://developer.android.com/reference/android/content/Context.html#registerReceiver(android.content.BroadcastReceiver, android.content.IntentFilter)"
)

JAVA_DYNAMIC_BROADCAST_RECEIVER_METHOD = 'registerReceiver'


class DynamicBroadcastReceiver(CoroutinePlugin, ManifestPlugin):
    def __init__(self):
        super().__init__(category="broadcast", name="Dynamic broadcast receiver found",
                         description=DYNAMIC_BROADCAST_RECEIVER_DESCRIPTION)
        self.severity = Severity.VULNERABILITY

    async def run_coroutine(self):
        while True:
            _, method_invocation = await self.yield_data()
            if not isinstance(method_invocation, MethodInvocation):
                continue

            # Ensure the minimum SDK is checked before proceeding
            if method_invocation.member == JAVA_DYNAMIC_BROADCAST_RECEIVER_METHOD and self.min_sdk < 14:
                issue = Issue(
                    category=self.category,
                    severity=self.severity,
                    name=self.name,
                    description=DYNAMIC_BROADCAST_RECEIVER_DESCRIPTION,
                    file_object=self.file_path,
                    line_number=method_invocation.position
                )
                self.issues.append(issue)
                log.info(f"Issue found in {self.file_path} at line {method_invocation.position}")

plugin = DynamicBroadcastReceiver()
