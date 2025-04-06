import logging
from copy import deepcopy
from enum import Enum
from json import JSONEncoder, dumps

log = logging.getLogger(__name__)


class Severity(Enum):
    INFO = 0
    WARNING = 1
    ERROR = 2
    VULNERABILITY = 3


class Issue:
    def __init__(self, category, name, severity, description, line_number=None, file_object=None, apk_exploit_dict=None):
        """
        Create a vulnerability, used by Plugins.

        :param str category: Category to put the vulnerability in the report.
        :param Severity or str severity: Severity of the vulnerability. Can be a Severity enum or a string.
        :param str description: Description of the issue.
        :param Tuple[int, int] or None line_number: Line number where the vulnerability was found.
        :param str or None file_object: File where the vulnerability occurred.
        :param Dict or None apk_exploit_dict: Dictionary containing information needed to build the exploit APK.
        """
        self.category = category
        self.severity = self._validate_severity(severity)
        self.description = description
        self.name = name
        self.line_number = line_number
        self.file_object = file_object
        self.apk_exploit_dict = apk_exploit_dict

    @staticmethod
    def _validate_severity(severity):
        """
        Validates and converts severity to a Severity Enum if necessary.

        :param severity: Severity in Enum or string form.
        :return: Severity Enum
        """
        if isinstance(severity, Severity):
            return severity
        elif isinstance(severity, str):
            severity_name = severity.strip().upper()
            try:
                return Severity[severity_name]
            except KeyError:
                log.warning(f"Invalid severity '{severity_name}'. Setting to Severity.WARNING.")
                return Severity.WARNING
        else:
            log.warning("Severity is not set or invalid. Setting to Severity.WARNING.")
            return Severity.WARNING

    def __repr__(self):
        return (f"Issue(category={self.category}, name={self.name}, severity={self.severity.name}, "
                f"description={self.description}, line_number={self.line_number}, "
                f"file_object={self.file_object}, apk_exploit_dict={self.apk_exploit_dict})")

    def __hash__(self):
        return hash((self.name, self.file_object, self.line_number))


class IssueEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Issue):
            working_dict = deepcopy(obj.__dict__)
            working_dict['severity'] = working_dict['severity'].name
            return working_dict
        log.error(f"Error converting object {repr(obj)} to JSON. Unsupported type: {type(obj)}")
        return super().default(obj)


def issue_json(value):
    """
    Converts an Issue or a list of Issues to JSON using IssueEncoder.
    
    :param value: Issue object or list of Issue objects.
    :return: JSON string
    """
    try:
        return dumps(value, cls=IssueEncoder, indent=4)
    except TypeError as e:
        log.exception(f"Error encoding to JSON: {e}")
        return dumps({"error": "Error encoding to JSON"})
