import os
from functools import partial


def create_directories_to_path(file_path):
    """
    Create directories leading to the specified path if they don't exist.
    
    :param file_path: Path to create directories for.
    """
    dir_path = os.path.dirname(file_path)
    if dir_path and not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
        except OSError as e:
            if e.errno != os.errno.EEXIST:
                raise
            # Ignore error if directories were created by another process


def file_has_extension(extension, file_path):
    """
    Check if a file has the specified extension.
    
    :param extension: File extension to check.
    :param file_path: Path of the file.
    :return: True if the file has the specified extension, otherwise False.
    """
    return os.path.splitext(file_path.lower())[1] == extension.lower()


# Partial function to check for .java files
is_java_file = partial(file_has_extension, ".java")


def environ_path_variable_exists(variable_name):
    """
    Check if an environment variable exists and is a valid path.

    :param variable_name: Name of the environment variable.
    :return: True if the environment variable exists and points to a valid path, otherwise False.
    """
    path_value = os.environ.get(variable_name)
    return bool(path_value and os.path.exists(path_value))
