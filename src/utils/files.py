"""
FILE UTILITIES
"""
# Standard Library Imports
import json
import logging
import os
import shutil
import subprocess
from glob import glob
from configparser import ConfigParser
from os import path as osp, makedirs
from os import remove
from pathlib import Path
from time import perf_counter
from typing import Optional

# Third Party Imports
from tqdm import tqdm
import py7zr

# Local Imports
from src.utils.testing import time_function
from src.utils.strings import StrEnum


class WordSize(StrEnum):
    """Word Size for 7z compression."""
    WS16 = "16"
    WS24 = "24"
    WS32 = "32"
    WS48 = "48"
    WS64 = "64"
    WS96 = "96"
    WS128 = "128"


class DictionarySize:
    """Dictionary Size for 7z compression."""
    DS32 = "32"
    DS48 = "48"
    DS64 = "64"
    DS96 = "96"
    DS128 = "128"
    DS192 = "192"
    DS256 = "256"
    DS384 = "384"
    DS512 = "512"
    DS768 = "768"
    DS1024 = "1024"
    DS1536 = "1536"


"""
FILE INFO UTILITIES
"""


def get_file_size_mb(file_path: str, decimal: int = 1) -> float:
    """
    Get a file's size in megabytes rounded.
    @param file_path: Path to the file.
    @param decimal: Number of decimal places to allow when rounding.
    @return: Float representing the filesize in megabytes rounded..
    """
    return round(os.path.getsize(file_path) / (1024 * 1024), decimal)


"""
CONFIG FILES
"""


def verify_config_fields(ini_file: str, json_file: str):
    """
    Validate that all settings fields present in a given json data are present in config file.
    If any are missing, add them and return
    @param ini_file: Config file to verify contains the proper fields.
    @param json_file: Json file containing config fields to check for.
    """
    # Track data
    data = {}
    changed = False

    # Load the json
    if not osp.exists(json_file):
        return
    with open(json_file, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Load the config
    conf_file = ConfigParser(allow_no_value=True)
    conf_file.optionxform = str
    if not osp.exists(ini_file):
        # Create a blank file if it doesn't exist
        with open(ini_file, "w", encoding="utf-8") as f:
            conf_file.write(f)
    with open(ini_file, "r", encoding="utf-8") as f:
        conf_file.read_file(f)

    # Build a dictionary of the necessary values
    for row in raw:
        # Add row if it's not a title
        if row['type'] == 'title':
            continue
        data.setdefault(row['section'], []).append({
            'key': row.get('key', ''),
            'value': row.get('default', 0)
        })

    # Add the data to ini where missing
    for section, settings in data.items():
        # Check if the section exists
        if not conf_file.has_section(section):
            conf_file.add_section(section)
            changed = True
        # Check if each setting exists
        for setting in settings:
            if not conf_file.has_option(section, setting['key']):
                conf_file.set(section, setting['key'], str(setting['value']))
                changed = True

    # If ini has changed, write changes
    if changed:
        with open(ini_file, "w", encoding="utf-8") as f:
            conf_file.write(f)


def get_valid_config_json(json_file: str):
    """
    Return valid JSON data for use with settings panel.
    @param json_file: Path to json file.
    @return: Json string dump of validated data.
    """
    # Load the json
    with open(json_file, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Remove unsupported keys
    for row in raw:
        if 'default' in row:
            row.pop('default')

    # Return json data
    return json.dumps(raw)


def copy_config_or_verify(path_from: str, path_to: str, validate_json: str) -> None:
    """
    Copy one config to another, or verify it if it exists.
    @param path_from: Path to the file to be copied.
    @param path_to: Path to the file to create, if it doesn't exist.
    @param validate_json: JSON settins to validate if the file exists.
    """
    if osp.isfile(path_to):
        verify_config_fields(path_to, validate_json)
    else:
        shutil.copy(path_from, path_to)


def remove_config_file(ini_file: str) -> bool:
    """
    Check if config file exists, then remove it.
    @return: True if removed, False if not.
    """
    if osp.isfile(ini_file):
        try:
            remove(ini_file)
            return True
        except OSError:
            return False
    return False


"""
PATHS AND FILENAMES
"""


def ensure_path_exists(path: str):
    """
    Ensure that directories in path exists.
    @param path:
    @return:
    """
    Path(osp.dirname(path)).mkdir(mode=511, parents=True, exist_ok=True)


def get_unique_filename(path: str, name: str, ext: str, suffix: str):
    """
    If a filepath exists, number the file according to the lowest number that doesn't exist.
    @param path: Path to the file.
    @param name: Name of the file.
    @param ext: Extension of the file.
    @param suffix: Suffix to add before the number.
    @return: Unique filename.
    """
    num = 0
    new_name = f"{name} ({suffix})" if suffix else name
    suffix = f' ({suffix}'+' {})' if suffix else ' ({})'
    while osp.isfile(osp.join(path, f"{new_name}{ext}")):
        num += 1
        new_name = name + suffix.format(num)
    return new_name


"""
ARCHIVE COMPRESSION
"""


def compress_file(file_path: str, output_dir: str) -> bool:
    """
    Compress a target file and save it as a 7z archive to the output directory.
    @param file_path: File to compress.
    @param output_dir: Directory to save archive to.
    @return: True if compression succeeded, otherwise False.
    """
    # Define the output file path
    filename = osp.basename(file_path).replace('.psd', '.7z')
    out_file = osp.join(output_dir, filename)
    null_device = open(os.devnull, 'w')

    # Compress the file
    try:
        subprocess.run([
                "7z", "a", "-t7z", "-m0=LZMA", "-mx=9",
                f"-md={DictionarySize.DS96}M",
                f"-mfb={WordSize.WS24}",
                out_file, file_path
            ], stdout=null_device, stderr=null_device)
    except Exception as e:
        logging.error("An error occurred compressing file!", exc_info=e)
        return False
    return True


def compress_template(
    file_name: str,
    plugin: Optional[str] = None,
    word_size: WordSize = WordSize.WS16,
    dict_size: DictionarySize = DictionarySize.DS1536
):
    """
    Compress a given template from an optional given plugin.
    @param file_name: Template PSD/PSB file name.
    @param plugin: Plugin containing the template, assume a base template if not provided.
    @param word_size: Word size value to use for the compression.
    @param dict_size: Dictionary size value to use for the compression.
    @return:
    """
    # Build the template path
    from_dir = osp.join(os.getcwd(), f'plugins\\{plugin}\\templates' if plugin else 'templates')
    to_dir = osp.join(os.getcwd(), f'plugins\\{plugin}\\templates\\compressed' if plugin else 'templates\\compressed')
    from_file = osp.join(from_dir, file_name)
    to_file = osp.join(to_dir, file_name.replace('.psd', '.7z').replace('.psb', '.7z'))
    null_device = open(os.devnull, 'w')

    # Compress the file
    s = perf_counter()
    try:
        subprocess.run(
            ["7z", "a", "-t7z", "-m0=LZMA", "-mx=9", f"-md={dict_size}M", f"-mfb={word_size}", to_file, from_file],
            stdout=null_device, stderr=null_device)
    except Exception as e:
        logging.error("An error occurred compressing file!", exc_info=e)
    return get_file_size_mb(to_file), perf_counter()-s


def compress_all(directory: str) -> None:
    """
    Compress all PSD files in a directory.
    @param directory: Directory containing PSD files to compress.
    """
    # Create "compressed" subdirectory if it doesn't exist
    output_dir = osp.join(directory, 'compressed')
    makedirs(output_dir, exist_ok=True)

    # Get a list of all .psd files in the directory
    files = glob(osp.join(directory, '*.psd'))

    with tqdm(total=len(files), desc="Compressing files", unit="file") as pbar:
        # Compress each file
        for f in files:
            pbar.set_description(os.path.basename(f))
            compress_file(f, output_dir)
            pbar.update()


"""
ARCHIVE DECOMPRESSION
"""


def decompress_file(file_path: str) -> None:
    """
    Decompress target 7z archive.
    @param file_path: Path to the 7z archive.
    """
    with py7zr.SevenZipFile(file_path, 'r') as archive:
        archive.extractall(path=osp.dirname(file_path))
    os.remove(file_path)
