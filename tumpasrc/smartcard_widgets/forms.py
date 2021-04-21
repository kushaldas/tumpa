from PySide2 import QtWidgets
from PySide2.QtCore import Qt, Signal

from tumpasrc.commons import MessageDialogs, PasswordEdit, css


class SmartCardConfirmationDialog(QtWidgets.QDialog):
    # passphrase, adminpin
    writetocard = Signal(
        (str, str, int),
    )

    def __init__(
        self,
        nextsteps_slot,
        title="Enter passphrase and pin for the smartcard",
        firstinput="Key passphrase",
        key=None,
        enable_window=None,
    ):
        super(SmartCardConfirmationDialog, self).__init__()
        self.setModal(True)
        self.setFixedSize(600, 220)
        self.setWindowTitle(title)
        if enable_window:
            self.rejected.connect(enable_window)
        layout = QtWidgets.QFormLayout(self)
        label = QtWidgets.QLabel(firstinput)
        self.firstinput = firstinput
        self.key = key
        self.encryptionSubkey = QtWidgets.QCheckBox("Encryption")
        self.encryptionSubkey.setEnabled(False)
        self.signingSubkey = QtWidgets.QCheckBox("Signing")
        self.signingSubkey.setEnabled(False)
        self.authenticationSubkey = QtWidgets.QCheckBox("Authentication")
        self.authenticationSubkey.setEnabled(False)
        self.passphraseEdit = PasswordEdit()
        layout.addRow(label, self.passphraseEdit)
        label = QtWidgets.QLabel("Current Admin Pin")
        self.addminPinEdit = PasswordEdit()
        layout.addRow(label, self.addminPinEdit)
        if self.key is not None:
            label = QtWidgets.QLabel("Choose subkeys to upload:")
            inhlayout = QtWidgets.QHBoxLayout()
            got_enc, got_sign, got_auth = self.key.available_subkeys()
            inhlayout.addWidget(self.encryptionSubkey)
            inhlayout.addWidget(self.signingSubkey)
            inhlayout.addWidget(self.authenticationSubkey)

            if got_enc:
                self.encryptionSubkey.setCheckState(Qt.Checked)
                self.encryptionSubkey.setEnabled(True)
            if got_sign:
                self.signingSubkey.setCheckState(Qt.Checked)
                self.signingSubkey.setEnabled(True)
            if got_auth:
                self.authenticationSubkey.setCheckState(Qt.Checked)
                self.authenticationSubkey.setEnabled(True)
            if any([got_enc, got_auth, got_sign]):  # Means we have at least one subkey
                widget = QtWidgets.QWidget()
                widget.setLayout(inhlayout)
                # Now add in the formlayout
                layout.addRow(label, widget)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        # now the button
        self.finalButton = QtWidgets.QPushButton(text="Write to smartcard")
        self.finalButton.clicked.connect(self.getPassphrases)
        vboxlayout = QtWidgets.QVBoxLayout()
        vboxlayout.addWidget(widget)
        vboxlayout.addWidget(self.finalButton)
        self.setLayout(vboxlayout)
        self.writetocard.connect(nextsteps_slot)
        self.setStyleSheet(css)

    def getPassphrases(self):
        passphrase = self.passphraseEdit.text().strip()
        adminpin = self.addminPinEdit.text().strip()
        if len(adminpin) < 8:
            self.error_dialog = MessageDialogs.error_dialog(
                "Editing smart card details", "Admin pin must be 8 character or more."
            )
            self.error_dialog.show()
            return
        if len(passphrase) < 6:
            self.error_dialog = MessageDialogs.error_dialog(
                "Editing smart card details",
                "{} must be 6 character or more.".format(self.firstinput),
            )
            self.error_dialog.show()
            return

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
                "Editing smart card details", "At least one subkey must be selected"
            )
            self.error_dialog.show()
            return

        self.hide()

        self.writetocard.emit(passphrase, adminpin, whichkeys)


class SmartPinFormWidget(QtWidgets.QWidget):
    # passphrase, adminpin
    writetocard = Signal(
        (str, str),
    )

    CSS = """QLabel {
        margin-top:20px;
    }
    """

    def __init__(
        self,
        nextsteps_slot,
        title="Change user pin",
        firstinput="New user pin",
    ):
        super(SmartPinFormWidget, self).__init__()
        self.setFixedSize(390, 420)
        self.setWindowTitle(title)
        layout = QtWidgets.QFormLayout(self)
        label = QtWidgets.QLabel(firstinput)
        self.firstinput = firstinput
        self.passphraseEdit = PasswordEdit()
        layout.addRow(label, self.passphraseEdit)
        label = QtWidgets.QLabel("Current Admin Pin")
        self.addminPinEdit = PasswordEdit()
        layout.addRow(label, self.addminPinEdit)
        layout.setRowWrapPolicy(QtWidgets.QFormLayout.WrapAllRows)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        # now the button
        self.finalButton = QtWidgets.QPushButton(text="Write to smartcard")
        self.finalButton.clicked.connect(self.getPassphrases)
        vboxlayout = QtWidgets.QVBoxLayout()
        vboxlayout.addWidget(widget)
        vboxlayout.addWidget(self.finalButton)
        vboxlayout.setAlignment(Qt.AlignTop)
        self.setLayout(vboxlayout)
        self.writetocard.connect(nextsteps_slot)
        self.setStyleSheet(css)
        self.setStyleSheet(self.CSS)

    def getPassphrases(self):
        passphrase = self.passphraseEdit.text().strip()
        adminpin = self.addminPinEdit.text().strip()
        if len(adminpin) < 8:
            self.error_dialog = MessageDialogs.error_dialog(
                "Editing smart card details", "Admin pin must be 8 character or more."
            )
            self.error_dialog.show()
            return
        if self.firstinput == "New Admin pin" and len(passphrase) < 8:
            self.error_dialog = MessageDialogs.error_dialog(
                "Editing smart card details", "Admin pin must be 8 character or more."
            )
            self.error_dialog.show()
            return
        if len(passphrase) < 6:
            self.error_dialog = MessageDialogs.error_dialog(
                "Editing smart card details",
                "{} must be 6 character or more.".format(self.firstinput),
            )
            self.error_dialog.show()
            return

        self.writetocard.emit(passphrase, adminpin)


class SmartCardTextFormWidget(QtWidgets.QWidget):
    # Public URL and Name
    writetocard = Signal(
        (str, str),
    )

    def __init__(
        self,
        nextsteps_slot,
        title="Enter public URL",
        textInput="Public URL",
    ):
        super(SmartCardTextFormWidget, self).__init__()
        self.setFixedSize(390, 420)
        self.setWindowTitle(title)
        layout = QtWidgets.QFormLayout(self)
        label = QtWidgets.QLabel(textInput)
        self.textInput = textInput
        self.textField = QtWidgets.QLineEdit("")
        layout.addRow(label, self.textField)
        label = QtWidgets.QLabel("Admin Pin")
        self.adminPinEdit = PasswordEdit()
        layout.addRow(label, self.adminPinEdit)
        layout.setRowWrapPolicy(QtWidgets.QFormLayout.WrapAllRows)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        # now the button
        self.finalButton = QtWidgets.QPushButton(text="Write to smartcard")
        self.finalButton.clicked.connect(self.getTextValue)
        vboxlayout = QtWidgets.QVBoxLayout()
        vboxlayout.addWidget(widget)
        vboxlayout.addWidget(self.finalButton)
        vboxlayout.setAlignment(Qt.AlignTop)
        self.setLayout(vboxlayout)
        self.writetocard.connect(nextsteps_slot)
        self.setStyleSheet(css)

    def getTextValue(self):
        text = self.textField.text().strip()
        adminpin = self.adminPinEdit.text().strip()
        if len(adminpin) < 8:
            self.error_dialog = MessageDialogs.error_dialog(
                "Editing smart card details", "Admin pin must be 8 character or more."
            )
            self.error_dialog.show()
            return
        if len(text) > 35:
            self.error_dialog = MessageDialogs.error_dialog(
                "Editing smart card details",
                "{} must be less than 35 characters.".format(self.textInput),
            )
            self.error_dialog.show()
            return
        if not len(text):
            self.error_dialog = MessageDialogs.error_dialog(
                "Editing smart card details",
                "{} cannot be blank.".format(self.textInput),
            )
            self.error_dialog.show()
            return

        self.hide()
        self.writetocard.emit(text, adminpin)
