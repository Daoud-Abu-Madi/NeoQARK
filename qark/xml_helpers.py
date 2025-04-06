import logging
from xml.etree import ElementTree
from pathlib import Path

log = logging.getLogger(__name__)


def write_key_value_to_xml(key, value, path):
    """
    Adds or updates a key-value pair in an XML file.

    :param str key: The name of the key.
    :param str value: The value associated with the key.
    :param str | Path path: Path to the XML file.
    """
    path = Path(path)

    if not path.exists():
        log.error(f"Error: XML file '{path}' does not exist.")
        raise SystemExit(f"XML file '{path}' does not exist.")

    try:
        xml_to_write = ElementTree.parse(path)
    except (IOError, ElementTree.ParseError) as e:
        log.exception(f"Failed to parse XML file: {e}")
        raise SystemExit(f"Error parsing XML file: {path}")

    root = xml_to_write.getroot()

    # Check for existing key and update if it exists
    existing_element = root.find(f".//string[@name='{key}']")
    if existing_element is not None:
        existing_element.text = value
    else:
        new_element = ElementTree.SubElement(root, "string", attrib={"name": key})
        new_element.text = value

    xml_to_write.write(path)
    log.info(f"Successfully added/updated key '{key}' in {path}")


def write_key_value_to_string_array_xml(array_name, value, path, add_id=True):
    """
    Adds or updates a value within a string-array in an XML file.

    :param str array_name: Name of the string-array.
    :param str value: Value to add or update.
    :param str | Path path: Path to the XML file.
    :param bool add_id: Whether to add an incremental ID if duplicates exist.
    :return: The updated value.
    :rtype: str
    """
    path = Path(path)

    if not path.exists():
        log.error(f"Error: XML file '{path}' does not exist.")
        raise SystemExit(f"XML file '{path}' does not exist.")

    try:
        strings_xml = ElementTree.parse(path)
    except (IOError, ElementTree.ParseError) as e:
        log.exception(f"Failed to parse XML file: {e}")
        raise SystemExit(f"Error parsing XML file: {path}")

    root = strings_xml.getroot()
    last_id = 0

    # Search for an existing string-array
    for string_array in root.findall("string-array"):
        if string_array.attrib.get("name") == array_name:
            # Increment ID if required
            if add_id:
                last_id = len(string_array.findall("item"))
                value = f"{value}{last_id + 1}"

            sub_element_item = ElementTree.SubElement(string_array, "item")
            sub_element_item.text = value

            strings_xml.write(path)
            log.info(f"Added value '{value}' to existing string-array '{array_name}'")
            return value

    # Create new string-array if not found
    if add_id:
        value = f"{value}{last_id + 1}"

    new_string_array = ElementTree.SubElement(root, "string-array", attrib={"name": array_name})
    sub_element_item = ElementTree.SubElement(new_string_array, "item")
    sub_element_item.text = value

    strings_xml.write(path)
    log.info(f"Created new string-array '{array_name}' with value '{value}'")
    return value


def get_manifest_out_of_files(files):
    """
    Finds and returns the path of 'AndroidManifest.xml' from a set of files.

    :param set files: Set of absolute file paths.
    :return: Path to 'AndroidManifest.xml' if found, otherwise None.
    :rtype: str | None
    """
    return next((file for file in files if file.lower().endswith("androidmanifest.xml")), None)
