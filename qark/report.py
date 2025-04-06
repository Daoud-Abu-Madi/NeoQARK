import os
from jinja2 import Environment, PackageLoader, select_autoescape, Template

from issue import Issue, Severity, issue_json  # noqa:F401 These are expected to be used later.
from utils import create_directories_to_path

DEFAULT_REPORT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'report', '')

# Configure Jinja2 Environment
jinja_env = Environment(
    loader=PackageLoader('qark', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

jinja_env.filters['issue_json'] = issue_json


class Report:
    """An object to store issues and generate reports in different formats using a Singleton pattern."""

    _instance = None

    def __new__(cls, issues=None, report_path=None, keep_report=False):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, issues=None, report_path=None, keep_report=False):
        """
        Initialize the report with optional issues and report configuration.

        :param issues: List of issues to include in the report.
        :param report_path: Path to the report directory.
        :param keep_report: Append to the report if True, otherwise overwrite.
        """
        self.issues = issues or []
        self.report_path = report_path or DEFAULT_REPORT_PATH
        self.keep_report = keep_report

    def generate(self, file_type='html', template_file=None):
        """
        Generate a report using Jinja2 templates.

        :param file_type: Type of report to generate (html, xml, json, csv).
        :param template_file: Custom template file path (optional).
        :return: Path to the generated report.
        """
        create_directories_to_path(self.report_path)
        full_report_path = os.path.join(self.report_path, f'report.{file_type}')

        try:
            with open(full_report_path, mode='a' if self.keep_report else 'w') as report_file:
                if template_file:
                    template = Template(template_file)
                else:
                    template = jinja_env.get_template(f'{file_type}_report.jinja')
                
                report_file.write(template.render(issues=list(self.issues)) + '\n')

            return full_report_path

        except Exception as e:
            raise RuntimeError(f"Failed to generate report: {e}")
