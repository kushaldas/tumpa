import configparser
import os
import pathlib

OS_RELEASE = "/etc/os-release"


def is_tails() -> bool:
    "Checks if we are running in tails"
    if os.path.exists(OS_RELEASE):
        with open(OS_RELEASE) as fobj:
            data = fobj.read()
            if "Tails" in data:
                return True
    return False


def has_persistent() -> bool:
    "Checks if we have the /home/amnesia/Persistent directory"
    if is_tails():
        if os.path.exists("/home/amnesia/Persistent"):
            return True

    return False


def get_configuration_file() -> str:
    """Returns the configuration file path. Creates the new configuration file if does not exist."""
    filepath = ""
    if has_persistent():
        DEFAULT_CONFIG = """[default]
        keystore = /home/amnesia/Persistent/.tumpa
"""
        filepath = "/home/amnesia/Persistent/.tumparc"
    else:
        filepath = os.path.join(pathlib.Path.home(), ".config/.tumparc")
        DEFAULT_CONFIG = """[default]
        keystore = {}/.tumpa
""".format(
            pathlib.Path.home()
        )
        dirpath = os.path.dirname(filepath)
        if not os.path.exists(dirpath):
            try:
                os.mkdir(dirpath, 0o700)
            except Exception as e:
                print("Failed to create configuration directory {}".format(e))
                return ""

    # If the filepath does not exits, means new setup, we will write the default value there.
    if not os.path.exists(filepath):
        with open(filepath, "w") as fobj:
            fobj.write(DEFAULT_CONFIG)
    return filepath


def get_keystore_directory() -> str:
    "Returns the jce KeyStore directory path"
    # We will hardcode for now
    if has_persistent():
        dirpath = "/home/amnesia/Persistent/.tumpa"
    else:
        dirpath = f"{pathlib.Path.home()}/.tumpa"
    if not os.path.exists(dirpath):
        os.mkdir(dirpath, 0o700)
    return dirpath
