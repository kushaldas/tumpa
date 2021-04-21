import datetime
import io
import os
import sys
import time

import johnnycanencrypt as jce
import johnnycanencrypt.johnnycanencrypt as rjce
from PySide2 import QtGui, QtWidgets
from PySide2.QtCore import QObject, QSize, Qt, QThread, Signal

import tumpasrc.key_widgets.utils as key_utils
from tumpasrc.commons import MessageDialogs, PasswordEdit, css
from tumpasrc.configuration import get_keystore_directory
from tumpasrc.key_widgets.display import KeyWidgetList
from tumpasrc.key_widgets.forms import NewKeyFormWidget
from tumpasrc.resources import load_css, load_icon
from tumpasrc.smartcard_widgets.forms import (
    SmartCardConfirmationDialog,
    SmartCardTextFormWidget,
    SmartPinFormWidget,
)
from tumpasrc.threads import HardwareThread


class KeyViewWidget(QtWidgets.QWidget):
    def __init__(self, ks, parent=None):
        super(KeyViewWidget, self).__init__(parent)
        keyring_instruction_label = QtWidgets.QLabel(
            "Single click on a key to enable writing to smart card. "
            + "Double click on a key to export the public key."
        )
        keyring_instruction_label.setObjectName("keyring_instruction")

        # List of keys shown
        self.widget = KeyWidgetList(ks)

        # Buttons
        self.generateButton = QtWidgets.QPushButton(text="Generate new key")
        self.generateButton.clicked.connect(self.parent().show_generate_dialog)
        self.uploadButton = QtWidgets.QPushButton(text="Upload to SmartCard")
        self.uploadButton.clicked.connect(self.parent().upload_to_smartcard)
        self.uploadButton.setEnabled(False)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.generateButton)
        hlayout.addWidget(self.uploadButton)
        wd = QtWidgets.QWidget()
        wd.setLayout(hlayout)

        vboxlayout = QtWidgets.QVBoxLayout()
        vboxlayout.addWidget(keyring_instruction_label)
        vboxlayout.addWidget(self.widget)
        vboxlayout.addWidget(wd)
        self.setLayout(vboxlayout)


class SmartCardViewWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SmartCardViewWidget, self).__init__(parent)
        self.main_area = SmartCardTextFormWidget(
            self.parent().set_name_on_card_slot,
            "Add Name",
            "Name",
        )
        self.main_area.setObjectName("mainarea")

        # Left Navbar
        self.editNameButton = QtWidgets.QPushButton(text="Edit Name")
        self.editNameButton.clicked.connect(self.parent().show_set_name)
        self.editNameButton.setProperty("active", "True")
        self.editPublicUrlButton = QtWidgets.QPushButton(text="Edit Public URL")
        self.editPublicUrlButton.clicked.connect(self.parent().show_set_public_url)
        self.editUserPinButton = QtWidgets.QPushButton(text="Edit User Pin")
        self.editUserPinButton.clicked.connect(self.parent().show_change_user_pin)
        self.editAdminPinButton = QtWidgets.QPushButton(text="Edit Admin Pin")
        self.editAdminPinButton.clicked.connect(self.parent().show_change_admin_pin)
        vnavlayout = QtWidgets.QVBoxLayout()
        vnavlayout.addWidget(self.editNameButton)
        vnavlayout.addWidget(self.editPublicUrlButton)
        vnavlayout.addWidget(self.editUserPinButton)
        vnavlayout.addWidget(self.editAdminPinButton)
        vnavlayout.setAlignment(Qt.AlignTop)
        navbarWidget = QtWidgets.QWidget()
        navbarWidget.setLayout(vnavlayout)
        navbarWidget.setObjectName("sidenavbar")
        navbarWidget.setMaximumWidth(200)

        self.hlayout = QtWidgets.QHBoxLayout()
        self.hlayout.addWidget(navbarWidget)
        self.hlayout.addWidget(self.main_area)
        self.hlayout.setMargin(0)
        self.setLayout(self.hlayout)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None, config={}):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("Tumpa: OpenPGP made simple")
        self.setMinimumWidth(600)
        self.setMinimumHeight(575)
        self.setMaximumWidth(600)
        self.setMaximumHeight(575)
        self.ks = jce.KeyStore(get_keystore_directory())
        self.current_fingerprint = ""
        self.cardcheck_thread = HardwareThread(self.enable_upload)

        # File menu
        exportPubKey = QtWidgets.QAction("&Export public key", self)
        exportPubKey.triggered.connect(self.export_public_key)
        exitAction = QtWidgets.QAction("E&xit", self)
        exitAction.triggered.connect(self.exit_process)
        menu = self.menuBar()
        filemenu = menu.addMenu("&File")
        filemenu.addAction(exportPubKey)
        filemenu.addAction(exitAction)

        # smartcard menu
        changepinAction = QtWidgets.QAction("Change user &pin", self)
        changepinAction.triggered.connect(self.show_change_user_pin)
        changeadminpinAction = QtWidgets.QAction("Change &admin pin", self)
        changeadminpinAction.triggered.connect(self.show_change_admin_pin)
        changenameAction = QtWidgets.QAction("Set cardholder &name", self)
        changenameAction.triggered.connect(self.show_set_name)
        changeurlAction = QtWidgets.QAction("Set public key &URL", self)
        changeurlAction.triggered.connect(self.show_set_public_url)
        resetYubiKeylAction = QtWidgets.QAction("Reset the YubiKey", self)
        resetYubiKeylAction.triggered.connect(self.reset_yubikey_dialog)
        smartcardmenu = menu.addMenu("&SmartCard")
        smartcardmenu.addAction(changepinAction)
        smartcardmenu.addAction(changeadminpinAction)
        smartcardmenu.addAction(changenameAction)
        smartcardmenu.addAction(changeurlAction)
        smartcardmenu.addAction(resetYubiKeylAction)

        # self.widget.itemSelectionChanged.connect(self.enable_upload)
        self.tabs = QtWidgets.QTabWidget()
        self.keyWidget = KeyViewWidget(self.ks, self)
        self.tabs.addTab(self.keyWidget, "Available Keys")
        self.smartCardWidget = SmartCardViewWidget(self)
        self.tabs.addTab(self.smartCardWidget, "Smart Card Settings")
        self.setCentralWidget(self.tabs)
        self.setStyleSheet(css)
        self.cardcheck_thread.start()

    def reset_yubikey_dialog(self):
        "Verify if the user really wants to reset the smartcard"
        reply = QtWidgets.QMessageBox.question(
            self,
            "Are you sure?",
            "This action will reset your YubiKey. Are you sure to do that?",
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                rjce.reset_yubikey()
            except Exception as e:
                self.error_dialog = MessageDialogs.error_dialog(
                    "YubiKey reset.", str(e)
                )
                self.error_dialog.show()
                return
        else:
            return

        self.success_dialog = MessageDialogs.success_dialog(
            "YubiKey successfully reset."
        )
        self.success_dialog.show()

    def enable_upload(self, value):
        "Slot to enable the upload to smartcard button"
        # If no item is selected on the ListWidget, then
        # no need to update the uploadButton status.
        try:
            if not self.keyWidget.widget.selectedItems():
                return
        except RuntimeError:
            return
        self.keyWidget.uploadButton.setEnabled(value)

    def show_change_user_pin(self):
        "This slot shows the input widget to change user pin"
        self.cardcheck_thread.flag = False
        self.tabs.setCurrentIndex(1)
        self.activateSmartCardOption("userPin")
        self.smartCardWidget.hlayout.removeWidget(self.smartCardWidget.main_area)
        self.smartCardWidget.main_area.deleteLater()
        self.smartCardWidget.main_area = SmartPinFormWidget(
            self.change_pin_on_card_slot,
            "Change user pin",
            "New User pin",
        )
        self.smartCardWidget.hlayout.addWidget(self.smartCardWidget.main_area)

    def show_set_public_url(self):
        "This slot shows the input widget to set public url"
        self.cardcheck_thread.flag = False
        self.tabs.setCurrentIndex(1)
        self.activateSmartCardOption("url")
        self.smartCardWidget.hlayout.removeWidget(self.smartCardWidget.main_area)
        self.smartCardWidget.main_area.deleteLater()
        self.smartCardWidget.main_area = SmartCardTextFormWidget(
            self.set_url_on_card_slot,
            "Add public URL",
            "Public URL",
        )
        self.smartCardWidget.hlayout.addWidget(self.smartCardWidget.main_area)

    def show_set_name(self):
        "This slot shows the input widget to set name"
        self.cardcheck_thread.flag = False
        self.tabs.setCurrentIndex(1)
        self.activateSmartCardOption("name")
        self.smartCardWidget.hlayout.removeWidget(self.smartCardWidget.main_area)
        self.smartCardWidget.main_area.deleteLater()
        self.smartCardWidget.main_area = SmartCardTextFormWidget(
            self.set_name_on_card_slot,
            "Add Name",
            "Name",
        )
        self.smartCardWidget.hlayout.addWidget(self.smartCardWidget.main_area)

    def show_change_admin_pin(self):
        "This slot shows the input widget to change admin pin"
        self.cardcheck_thread.flag = False
        self.tabs.setCurrentIndex(1)
        self.activateSmartCardOption("adminPin")
        self.smartCardWidget.hlayout.removeWidget(self.smartCardWidget.main_area)
        self.smartCardWidget.main_area.deleteLater()
        self.smartCardWidget.main_area = SmartPinFormWidget(
            self.change_admin_pin_on_card_slot,
            "Change admin pin",
            "New Admin pin",
        )
        self.smartCardWidget.hlayout.addWidget(self.smartCardWidget.main_area)

    def activateSmartCardOption(self, buttonName: str):
        self.deactivateAllSmartCardOption()
        if buttonName == "adminPin":
            self.smartCardWidget.editAdminPinButton.setProperty("active", "True")
            self.smartCardWidget.editAdminPinButton.style().unpolish(
                self.smartCardWidget.editAdminPinButton
            )
            self.smartCardWidget.editAdminPinButton.style().polish(
                self.smartCardWidget.editAdminPinButton
            )
        elif buttonName == "userPin":
            self.smartCardWidget.editUserPinButton.setProperty("active", "True")
            self.smartCardWidget.editUserPinButton.style().unpolish(
                self.smartCardWidget.editUserPinButton
            )
            self.smartCardWidget.editUserPinButton.style().polish(
                self.smartCardWidget.editUserPinButton
            )
        elif buttonName == "url":
            self.smartCardWidget.editPublicUrlButton.setProperty("active", "True")
            self.smartCardWidget.editPublicUrlButton.style().unpolish(
                self.smartCardWidget.editPublicUrlButton
            )
            self.smartCardWidget.editPublicUrlButton.style().polish(
                self.smartCardWidget.editPublicUrlButton
            )
        elif buttonName == "name":
            self.smartCardWidget.editNameButton.setProperty("active", "True")
            self.smartCardWidget.editNameButton.style().unpolish(
                self.smartCardWidget.editNameButton
            )
            self.smartCardWidget.editNameButton.style().polish(
                self.smartCardWidget.editNameButton
            )

    def deactivateAllSmartCardOption(self):
        self.smartCardWidget.editNameButton.setProperty("active", "False")
        self.smartCardWidget.editPublicUrlButton.setProperty("active", "False")
        self.smartCardWidget.editUserPinButton.setProperty("active", "False")
        self.smartCardWidget.editAdminPinButton.setProperty("active", "False")
        self.smartCardWidget.editNameButton.style().unpolish(
            self.smartCardWidget.editNameButton
        )
        self.smartCardWidget.editPublicUrlButton.style().unpolish(
            self.smartCardWidget.editPublicUrlButton
        )
        self.smartCardWidget.editUserPinButton.style().unpolish(
            self.smartCardWidget.editUserPinButton
        )
        self.smartCardWidget.editAdminPinButton.style().unpolish(
            self.smartCardWidget.editAdminPinButton
        )
        self.smartCardWidget.editNameButton.style().polish(
            self.smartCardWidget.editNameButton
        )
        self.smartCardWidget.editPublicUrlButton.style().polish(
            self.smartCardWidget.editPublicUrlButton
        )
        self.smartCardWidget.editUserPinButton.style().polish(
            self.smartCardWidget.editUserPinButton
        )
        self.smartCardWidget.editAdminPinButton.style().polish(
            self.smartCardWidget.editAdminPinButton
        )

    def change_pin_on_card_slot(self, userpin, adminpin):
        "Final slot which will try to change the userpin"
        try:
            rjce.change_user_pin(adminpin.encode("utf-8"), userpin.encode("utf-8"))
        except Exception as e:
            self.error_dialog = MessageDialogs.error_dialog("changing user pin", str(e))
            self.error_dialog.show()
            self.enable_cardcheck_thread_slot()
            return
        self.success_dialog = MessageDialogs.success_dialog(
            "Changed user pin successfully."
        )
        self.success_dialog.show()
        self.enable_cardcheck_thread_slot()

    def change_admin_pin_on_card_slot(self, userpin, adminpin):
        "Final slot which will try to change the adminpin"
        try:
            rjce.change_admin_pin(adminpin.encode("utf-8"), userpin.encode("utf-8"))
        except Exception as e:
            self.error_dialog = MessageDialogs.error_dialog(
                "changing admin pin", str(e)
            )
            self.error_dialog.show()
            self.enable_cardcheck_thread_slot()
            return
        self.success_dialog = MessageDialogs.success_dialog(
            "Changed admin pin successfully."
        )
        self.success_dialog.show()
        self.enable_cardcheck_thread_slot()

    def set_url_on_card_slot(self, publicURL, adminpin):
        "Final slot which will try to change the publicURL"
        try:
            rjce.set_url(publicURL.encode("utf-8"), adminpin.encode("utf-8"))
        except Exception as e:
            self.error_dialog = MessageDialogs.error_dialog("adding public URL", str(e))
            self.error_dialog.show()
            self.enable_cardcheck_thread_slot()
            return
        self.success_dialog = MessageDialogs.success_dialog(
            "Added public URL successfully."
        )
        self.success_dialog.show()
        self.enable_cardcheck_thread_slot()

    def set_name_on_card_slot(self, name, adminpin):
        "Final slot which will try to change the name"
        try:
            # If input is "First Middle Last",
            # the parameter sent should be "Last<<Middle<<First"
            name = "<<".join(name.split()[::-1])
            rjce.set_name(name.encode("utf-8"), adminpin.encode("utf-8"))
        except Exception as e:
            self.error_dialog = MessageDialogs.error_dialog("adding name", str(e))
            self.error_dialog.show()
            self.enable_cardcheck_thread_slot()
            return
        self.success_dialog = MessageDialogs.success_dialog("Added name successfully.")
        self.success_dialog.show()
        self.enable_cardcheck_thread_slot()

    def disable_generate_button(self):
        self.cardcheck_thread.flag = False
        self.generateButton.setEnabled(False)
        self.update()
        self.repaint()

    def enable_generate_button(self):
        self.enable_cardcheck_thread_slot()
        self.setEnabled(True)
        self.generateButton.setEnabled(True)
        self.update()
        self.repaint()

    def show_generate_dialog(self):
        "Shows the form to generate new key"
        self.disable_cardcheck_thread_slot()
        new_key_form = NewKeyFormWidget(self.ks, self.restore_list_view)
        self.setCentralWidget(new_key_form)

    def restore_list_view(self):
        self.enable_cardcheck_thread_slot()
        self.tabs = QtWidgets.QTabWidget()
        self.keyWidget = KeyViewWidget(self.ks, self)
        self.tabs.addTab(self.keyWidget, "Available Keys")
        self.smartCardWidget = SmartCardViewWidget(self)
        self.tabs.addTab(self.smartCardWidget, "Smart Card Settings")
        self.setCentralWidget(self.tabs)

    def enable_mainwindow(self):
        self.enable_cardcheck_thread_slot()
        self.setEnabled(True)

    def disable_cardcheck_thread_slot(self):
        self.cardcheck_thread.flag = False
        self.cardcheck_thread.quit()

    def enable_cardcheck_thread_slot(self):
        self.cardcheck_thread.flag = True
        self.cardcheck_thread.start()

    def upload_to_smartcard(self):
        "Shows the userinput dialog to upload the selected key to the smartcard"
        # This means no key is selected on the list
        if not self.keyWidget.widget.selectedItems():
            self.error_dialog = MessageDialogs.error_dialog(
                "upload to smart card", "Please select a key from the list."
            )
            self.error_dialog.show()
            return

        self.disable_cardcheck_thread_slot()
        self.setEnabled(False)
        item = self.keyWidget.widget.selectedItems()[0]
        kw = self.keyWidget.widget.itemWidget(item)
        self.current_key = kw.key
        self.sccd = SmartCardConfirmationDialog(
            self.get_pins_and_passphrase_and_write,
            key=kw.key,
            enable_window=self.enable_mainwindow,
        )
        self.sccd.show()

    def get_pins_and_passphrase_and_write(
        self, passphrase: str, adminpin: str, whichkeys: int
    ):
        "This method uploads the cert to the card"
        certdata = self.current_key.keyvalue
        try:
            rjce.upload_to_smartcard(
                certdata, adminpin.encode("utf-8"), passphrase, whichkeys
            )
        except Exception as e:
            self.error_dialog = MessageDialogs.error_dialog(
                "upload to smartcard.", str(e)
            )
            self.error_dialog.show()
            return
        self.success_dialog = MessageDialogs.success_dialog(
            "Uploaded to the smartcard successfully."
        )
        self.success_dialog.show()
        self.setEnabled(True)
        self.enable_cardcheck_thread_slot()

    def export_public_key(self):
        # This means no key is selected on the list
        if not self.keyWidget.widget.selectedItems():
            self.error_dialog = MessageDialogs.error_dialog(
                "exporting public key", "Please select a key from the list."
            )
            self.error_dialog.show()
            return

        item = self.keyWidget.widget.selectedItems()[0]
        kw = self.keyWidget.widget.itemWidget(item)
        if key_utils.export_public_key(self, kw.key.fingerprint, kw.key.get_pub_key()):
            self.success_dialog = MessageDialogs.success_dialog(
                "Exported public key successfully!"
            )
            self.success_dialog.show()

    def exit_process(self):
        self.cardcheck_thread.flag = False
        time.sleep(1)
        sys.exit(0)

    def closeEvent(self, event):
        self.cardcheck_thread.flag = False
        time.sleep(1)
        return super().closeEvent(event)


def main():
    app = QtWidgets.QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()
