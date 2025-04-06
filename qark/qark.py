#!/usr/bin/env python

import logging
import logging.config
import os

import click

#from apk_builder import APKBuilder
#from decompiler.decompiler import Decompiler
#from utils import environ_path_variable_exists

DEBUG_LOG_PATH = os.path.join(os.getcwd(), "qark_debug.log")

# Environment variable names for the SDK
ANDROID_SDK_ENV_VARS = ["ANDROID_SDK_HOME", "ANDROID_HOME", "ANDROID_SDK_ROOT"]

logger = logging.getLogger(__name__)

def initialize_logging(level):
    """
    Initializes logging configuration with both console and file handlers.

    Args:
        level (str): Logging level ("DEBUG" or "INFO").
    """
    handlers = {
        "stderr_handler": {
            "level": level,
            "class": "logging.StreamHandler"
        },
        "debug_handler": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": DEBUG_LOG_PATH,
            "mode": "w",
            "formatter": "standard"
        }
    }

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            }
        },
        "handlers": handlers,
        "loggers": {
            "": {
                "handlers": ["stderr_handler", "debug_handler"] if level == "DEBUG" else ["stderr_handler"],
                "level": level,
                "propagate": True
            }
        }
    })

    logger.info(f"Logging initialized with level {level}")

def find_sdk_path():
    """
    Finds Android SDK Path using environment variables in preferred order.

    Returns:
        str or None: Path to SDK if found, None otherwise.
    """
    from utils import environ_path_variable_exists
    
    for env_var in ANDROID_SDK_ENV_VARS:
        if environ_path_variable_exists(env_var):
            sdk_path = os.environ[env_var]
            if os.path.exists(sdk_path):
                return sdk_path
            else:
                logger.warning(f"{env_var} is set but the path is invalid: {sdk_path}")
    return None

@click.command()
@click.option("--sdk-path", type=click.Path(exists=True, file_okay=False, resolve_path=True),
              help="Path to the downloaded SDK directory. Required if --exploit-apk is passed.")
@click.option("--build-path", type=click.Path(resolve_path=True, file_okay=False),
              help="Path to store decompiled files and exploit APK.", default="build", show_default=True)
@click.option("--debug/--no-debug", default=False, help="Enable or disable debugging.", show_default=True)
@click.option("--apk", "source", help="Path to APK for analysis.", type=click.Path(exists=True, resolve_path=True))
@click.option("--java", "source", type=click.Path(exists=True, resolve_path=True),
              help="Path to Java source code or directory.")
@click.option("--report-type", type=click.Choice(["html", "xml", "json", "csv"]),
              help="Report format.", default="html", show_default=True)
@click.option("--exploit-apk/--no-exploit-apk", default=False,
              help="Generate an exploit APK if vulnerabilities are found.", show_default=True)
@click.option("--report-path", type=click.Path(resolve_path=True, file_okay=False),
              default=None, help="Path for report output.")
@click.option("--keep-report/--no-keep-report", default=False,
              help="Append to existing reports instead of overwriting.", show_default=True)
@click.version_option(version="1.0.0")  # تحديد الإصدار هنا
@click.pass_context
def cli(ctx, sdk_path, build_path, debug, source, report_type, exploit_apk, report_path, keep_report):
    """Main CLI command for QARK tool."""
    # Check if source is provided
    if not source:
        click.secho("Please provide a source using --java or --apk.", fg='red')
        click.secho(ctx.get_help())
        ctx.exit(1)

    # Handle SDK path for exploit APK
    if exploit_apk:
        sdk_path = sdk_path or find_sdk_path()
        if not sdk_path:
            click.secho("Error: Unable to locate Android SDK. Provide SDK path using --sdk-path or set environment variables.", fg='red')
            ctx.exit(1)

    # Initialize logging
    initialize_logging("DEBUG" if debug else "INFO")

    try:
        # Decompile the source
        from decompiler.decompiler import Decompiler
        
        click.secho("Starting Decompilation...", fg='green')
        decompiler = Decompiler(path_to_source=source, build_directory=build_path)
        decompiler.run()

        # Scan for vulnerabilities
        click.secho("Scanning for vulnerabilities...", fg='green')
        path_to_source = decompiler.path_to_source if decompiler.source_code else decompiler.build_directory

        # Lazy import to avoid circular imports
        from scanner.scanner import Scanner
        scanner = Scanner(manifest_path=decompiler.manifest_path, path_to_source=path_to_source)
        scanner.run()
        click.secho("Scanning complete.", fg='blue')

        # Generate report
        click.secho("Generating report...", fg='green')
        from report import Report
        report = Report(issues=set(scanner.issues), report_path=report_path, keep_report=keep_report)
        final_report_path = report.generate(file_type=report_type)
        click.secho(f"Report saved to: {final_report_path}", fg='blue')

        # Build exploit APK if requested
        if exploit_apk:
            click.secho("Building exploit APK...", fg='green')
            from apk_builder import APKBuilder
            exploit_builder = APKBuilder(
                exploit_apk_path=build_path,
                issues=scanner.issues,
                apk_name=decompiler.apk_name,
                manifest_path=decompiler.manifest_path,
                sdk_path=sdk_path
            )
            exploit_builder.build()
            click.secho("Exploit APK built successfully.", fg='blue')

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        click.secho(f"Error: {str(e)}", fg='red')
        ctx.exit(1)

if __name__ == "__main__":
    cli()
