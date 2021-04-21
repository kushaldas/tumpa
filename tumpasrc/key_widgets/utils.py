import os

from PySide2 import QtWidgets


def export_public_key(widget, fingerprint, public_key):
    select_path = QtWidgets.QFileDialog.getExistingDirectory(
        widget,
        "Select directory to save public key",
        ".",
        QtWidgets.QFileDialog.ShowDirsOnly,
    )
    if select_path:
        filepassphrase = f"{fingerprint}.pub"
        filepath = os.path.join(select_path, filepassphrase)
        with open(filepath, "w") as fobj:
            fobj.write(public_key)
        return True
    return False
