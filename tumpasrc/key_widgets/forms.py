import datetime

import johnnycanencrypt as jce
from PySide2 import QtWidgets
from PySide2.QtCore import QObject, QSize, Qt, QThread, Signal

from tumpasrc.commons import MessageDialogs, PasswordEdit, css


class NewKeyFormWidget(QtWidgets.QWidget):
    update_ui = Signal((jce.Key,))

    def __init__(
        self,
        ks: jce.KeyStore,
        restore_list_view,
    ):
        super(NewKeyFormWidget, self).__init__()
        self.update_ui.connect(restore_list_view)
        self.ks = ks  # jce.KeyStore
        self.setFixedSize(QSize(600, 525))
        vboxlayout = QtWidgets.QVBoxLayout()
        name_label = QtWidgets.QLabel("Your name:")
        self.name_box = QtWidgets.QLineEdit("")

        vboxlayout.addWidget(name_label)
        vboxlayout.addWidget(self.name_box)

        email_label = QtWidgets.QLabel("Email addresses (one email per line)")
        self.email_box = QtWidgets.QPlainTextEdit()
        self.email_box.setTabChangesFocus(True)

        vboxlayout.addWidget(email_label)
        vboxlayout.addWidget(self.email_box)
        passphrase_label = QtWidgets.QLabel(
            "Key Passphrase (recommended: 12+ chars in length):"
        )
        self.passphrase_box = PasswordEdit()

        vboxlayout.addWidget(passphrase_label)
        vboxlayout.addWidget(self.passphrase_box)

        # now the checkboxes for subkey
        self.encryptionSubkey = QtWidgets.QCheckBox("Encryption subkey")
        self.encryptionSubkey.setCheckState(Qt.Checked)
        self.signingSubkey = QtWidgets.QCheckBox("Signing subkey")
        self.signingSubkey.setCheckState(Qt.Checked)
        self.authenticationSubkey = QtWidgets.QCheckBox("Authentication subkey")

        hboxlayout = QtWidgets.QHBoxLayout()
        hboxlayout.addWidget(self.encryptionSubkey)
        hboxlayout.addWidget(self.signingSubkey)
        hboxlayout.addWidget(self.authenticationSubkey)

        widget = QtWidgets.QWidget()
        widget.setLayout(hboxlayout)
        vboxlayout.addWidget(widget)

        hboxbuttonslayout = QtWidgets.QHBoxLayout()
        self.generateButton = QtWidgets.QPushButton("Generate")
        self.generateButton.clicked.connect(self.generate)
        hboxbuttonslayout.addWidget(self.generateButton)

        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.cancelButton.setObjectName("secondary_button")
        self.cancelButton.clicked.connect(restore_list_view)
        hboxbuttonslayout.addWidget(self.cancelButton)
        hbuttons = QtWidgets.QWidget()
        hbuttons.setLayout(hboxbuttonslayout)
        vboxlayout.addWidget(hbuttons)

        self.setLayout(vboxlayout)
        self.setWindowTitle("Generate a new OpenPGP key")
        self.setStyleSheet(css)

    def generate(self):
        self.generateButton.setEnabled(False)
        emails = self.email_box.toPlainText()
        name = self.name_box.text().strip()
        password = self.passphrase_box.text().strip()

        if not len(name):
            self.error_dialog = MessageDialogs.error_dialog(
                "generating new key", "Name cannot be blank."
            )
            self.error_dialog.show()
            self.generateButton.setEnabled(True)
            return

        if not len(emails):
            self.error_dialog = MessageDialogs.error_dialog(
                "generating new key", "There must be at least one email."
            )
            self.error_dialog.show()
            self.generateButton.setEnabled(True)
            return

        if not len(password):
            self.error_dialog = MessageDialogs.error_dialog(
                "generating new key", "Key passphrase cannot be blank."
            )
            self.error_dialog.show()
            self.generateButton.setEnabled(True)
            return

        if len(password) < 6:
            self.error_dialog = MessageDialogs.error_dialog(
                "generating new key",
                "Key Passphrase must be at least 6 characters long.",
            )
            self.error_dialog.show()
            self.generateButton.setEnabled(True)
            return

        # Now check which all subkeys are required
        whichkeys = 0
        if self.encryptionSubkey.checkState():
            whichkeys += 1
        if self.signingSubkey.checkState():
            whichkeys += 2
        if self.authenticationSubkey.checkState():
            whichkeys += 4

        # At least one subkey must be selected
        if whichkeys == 0:
            self.error_dialog = MessageDialogs.error_dialog(
                "Generating new key", "At least one subkey must be selected"
            )
            self.error_dialog.show()
            return

        uids = []
        for email in emails.split("\n"):
            value = f"{name} <{email}>"
            uids.append(value)
        edate = datetime.datetime.now() + datetime.timedelta(days=3 * 365)
        # To make sure that the Generate button is disabled first
        self.generateButton.setEnabled(False)
        self.update()
        self.repaint()
        # Now let us try to create a key
        newk = self.ks.create_newkey(
            password,
            uids,
            ciphersuite=jce.Cipher.Cv25519,
            expiration=edate,
            subkeys_expiration=True,
            whichkeys=whichkeys,
        )
        self.success_dialog = MessageDialogs.success_dialog(
            "Generated keys successfully!"
        )
        self.success_dialog.show()
        self.update_ui.emit(newk)
