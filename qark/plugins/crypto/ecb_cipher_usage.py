import logging
import re

import javalang

from qark.issue import Severity, Issue
from qark.scanner.plugin import CoroutinePlugin

log = logging.getLogger(__name__)

class ECBCipherCheck(CoroutinePlugin):
    """
    This plugin checks for the usage of the insecure ECB cipher mode.
    ECB (Electronic Codebook) mode is considered insecure and should not be used.
    """
    def __init__(self):
        super().__init__(category="crypto", name="ECB Cipher Usage",
                         description="ECB mode is an insecure encryption technique and prone to data leakage")
        self.severity = Severity.VULNERABILITY

    async def run_coroutine(self):
        while True:
            _, method_invocation = await self.yield_data()

            if not isinstance(method_invocation, javalang.tree.MethodInvocation):
                continue

            try:
                method_name = method_invocation.member
                encryption_type = method_invocation.arguments[0].value
                qualifier = method_invocation.qualifier  # the object that getInstance is called on
                if method_name == 'getInstance' and qualifier == 'Cipher' and re.search(r'.*/ECB/.*', encryption_type):
                    description = "getInstance should not be called with ECB as the cipher mode, as it is insecure."
                    self.issues.append(
                        Issue(self.category, self.name, self.severity, description, file_object=self.file_path)
                    )
            except Exception as e:
                log.error(f"Error processing method invocation: {e}")
                continue


plugin = ECBCipherCheck()
