from PySide2 import QtWidgets

from tumpasrc.resources import load_css, load_icon

css = load_css("mainwindow.css")


class MessageDialogs:
    """
    A class that contains dialogue QMessageBoxes for success, error, etc.
    """

    @classmethod
    def success_dialog(cls, msg: str):
        success_dialog = QtWidgets.QMessageBox()
        success_dialog.setText(f"{msg}")
        success_dialog.setIcon(QtWidgets.QMessageBox.Information)
        success_dialog.setWindowTitle("Success")
        success_dialog.setStyleSheet(css)
        return success_dialog

    @classmethod
    def error_dialog(cls, where: str, msg: str):
        error_dialog = QtWidgets.QMessageBox()
        error_dialog.setText(msg)
        error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        error_dialog.setWindowTitle(f"Error during {where}")
        error_dialog.setStyleSheet(css)
        return error_dialog


class PasswordEdit(QtWidgets.QLineEdit):
    """
    A LineEdit with icons to show/hide password entries
    """

    CSS = """QLineEdit {
        margin: 0px;
    }
    """

    def __init__(self):
        super().__init__()

        # Set styles
        self.setStyleSheet(self.CSS)

        self.visibleIcon = load_icon("eye_visible.svg")
        self.hiddenIcon = load_icon("eye_hidden.svg")

        self.setEchoMode(QtWidgets.QLineEdit.Password)
        self.togglepasswordAction = self.addAction(
            self.visibleIcon, QtWidgets.QLineEdit.TrailingPosition
        )
        self.togglepasswordAction.triggered.connect(self.on_toggle_password_Action)
        self.password_shown = False

    def on_toggle_password_Action(self):
        if not self.password_shown:
            self.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.password_shown = True
            self.togglepasswordAction.setIcon(self.hiddenIcon)
        else:
            self.setEchoMode(QtWidgets.QLineEdit.Password)
            self.password_shown = False
            self.togglepasswordAction.setIcon(self.visibleIcon)
