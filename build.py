"""
SCRIPT TO BUILD PROXYSHOP AS EXE RELEASE
"""
import os
import sys
import zipfile
from glob import glob
from pathlib import Path
from shutil import copy2, copytree, rmtree, move
import PyInstaller.__main__

from src.env import ENV_VERSION

# Folder definitions
CWD = os.getcwd()
DIST = os.path.join(CWD, 'dist')

SRC = os.path.join(CWD, 'src')
DIST_SRC = os.path.join(DIST, 'src')

DATA = os.path.join(SRC, 'data')
DIST_DATA = os.path.join(DIST_SRC, 'data')

TEMPS = os.path.join(CWD, 'templates')
DIST_TEMPS = os.path.join(DIST, 'templates')

PLUGINS = os.path.join(CWD, 'plugins')
DIST_PLUGINS = os.path.join(DIST, 'plugins')

# All individual files that need to be copied upon pyinstaller completion
files = [
    # --- WORKING DIRECTORY
    {'src': os.path.join(CWD, 'LICENSE'), 'dst': os.path.join(DIST, 'LICENSE')},
    {'src': os.path.join(CWD, 'README.md'), 'dst': os.path.join(DIST, 'README.md')},
    # --- SOURCE DIRECTORY
    {'src': os.path.join(DATA, 'tests.json'), 'dst': os.path.join(DIST_DATA, 'tests.json')},
    {'src': os.path.join(DATA, 'app_templates.json'), 'dst': os.path.join(DIST_DATA, 'app_templates.json')},
    {'src': os.path.join(DATA, 'symbols.yaml'), 'dst': os.path.join(DIST_DATA, 'symbols.yaml')},
    {'src': os.path.join(DATA, 'watermarks.json'), 'dst': os.path.join(DIST_DATA, 'watermarks.json')},
    {'src': os.path.join(DATA, 'app_settings.json'), 'dst': os.path.join(DIST_DATA, 'app_settings.json')},
    {'src': os.path.join(DATA, 'base_settings.json'), 'dst': os.path.join(DIST_DATA, 'base_settings.json')},
]

# Folders that need to be copied
folders = [
    # --- WORKING DIRECTORY
    {'src': os.path.join(CWD, "fonts"), 'dst': os.path.join(DIST, 'fonts')},
    # --- SOURCE DIRECTORY
    {'src': os.path.join(SRC, "kv"), 'dst': os.path.join(DIST_SRC, 'kv')},
    {'src': os.path.join(SRC, "img"), 'dst': os.path.join(DIST_SRC, 'img')},
    {'src': os.path.join(SRC, "configs"), 'dst': os.path.join(DIST_SRC, 'configs')},
    # --- TEMPLATE TOOLS
    {'src': os.path.join(TEMPS, 'tools'), 'dst': os.path.join(DIST_TEMPS, 'tools')},
    # --- PLUGINS DIRECTORY
    {'src': os.path.join(PLUGINS, "MrTeferi"), 'dst': os.path.join(DIST_PLUGINS, 'MrTeferi')},
    {'src': os.path.join(PLUGINS, "SilvanMTG"), 'dst': os.path.join(DIST_PLUGINS, 'SilvanMTG')},
]

# Directories containing ini files
remove_dirs = [
    os.path.join(DIST_SRC, 'configs'),
    os.path.join(DIST_PLUGINS, 'MrTeferi/configs'),
    os.path.join(DIST_PLUGINS, 'SilvanMTG/configs'),
    os.path.join(DIST_PLUGINS, 'MrTeferi/templates'),
    os.path.join(DIST_PLUGINS, 'SilvanMTG/templates')
]


def clear_build_files(clear_dist=True):
    """
    Clean out all PYCACHE files and Pyinstaller files
    """
    os.system("pyclean -v .")
    if os.path.exists(os.path.join(CWD, '.venv')):
        os.system("pyclean -v .venv")
    try:
        rmtree(os.path.join(os.getcwd(), 'build'))
    except Exception as e:
        print(e)
    if clear_dist:
        try:
            rmtree(os.path.join(os.getcwd(), 'dist'))
        except Exception as e:
            print(e)


def make_dirs():
    """
    Make sure necessary directories exist.
    """
    # Ensure folders exist
    Path(DIST).mkdir(mode=511, parents=True, exist_ok=True)
    Path(DIST_DATA).mkdir(mode=511, parents=True, exist_ok=True)
    Path(DIST_PLUGINS).mkdir(mode=511, parents=True, exist_ok=True)
    Path(os.path.join(DIST, "art")).mkdir(mode=511, parents=True, exist_ok=True)
    Path(os.path.join(DIST, "templates")).mkdir(mode=511, parents=True, exist_ok=True)


def move_data():
    """
    Move our data files into the release.
    """
    # Transfer our necessary files
    print("Transferring data files...")
    for f in files:
        copy2(f['src'], f['dst'])

    # Transfer our necessary folders
    print("Transferring data folders...")
    for f in folders:
        copytree(f['src'], f['dst'])


def remove_unneeded_files():
    """
    Remove autogenerated ini config files and PSD templates.
    """
    for directory in remove_dirs:
        for file_name in os.listdir(directory):
            if file_name.endswith(('.ini', '.psd', '.psb')):
                os.remove(os.path.join(directory, file_name))


def build_zip(tag: str = None):
    """
    Create a zip of this release.
    """
    print("Building ZIP...")
    tag = f'.{tag}' if tag else ''
    ZIP = os.path.join(CWD, 'Proxyshop.v{}{}.zip'.format(ENV_VERSION, tag))
    ZIP_DIST = os.path.join(DIST, 'Proxyshop.v{}{}.zip'.format(ENV_VERSION, tag))
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for fp in glob(os.path.join(DIST, "**/*"), recursive=True):
            base = os.path.commonpath([DIST, fp])
            zipf.write(fp, arcname=fp.replace(base, ""))
    move(ZIP, ZIP_DIST)


if __name__ == '__main__':

    # Console enabled build?
    if '--console' in sys.argv:
        build_spec = 'Proxyshop-console.spec'
        zip_tag = 'console'
        del sys.argv[1]
    else:
        build_spec = 'Proxyshop.spec'
        zip_tag = ''

    # Pre-build steps
    clear_build_files()
    make_dirs()

    # Run pyinstaller
    print("Starting PyInstaller...")
    PyInstaller.__main__.run([
        build_spec,
        '--clean'
    ])

    # Post-build steps
    move_data()
    remove_unneeded_files()
    build_zip(zip_tag)
    clear_build_files(False)
