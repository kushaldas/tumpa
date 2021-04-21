import johnnycanencrypt as jce
from PySide2 import QtWidgets
from PySide2.QtCore import QObject, QSize, Qt, QThread, Signal

import tumpasrc.key_widgets.utils as key_utils
from tumpasrc.commons import MessageDialogs


class KeyWidget(QtWidgets.QWidget):
    SPACER = 14
    BOTTOM_SPACER = 11

    def __init__(self, key: jce.Key):
        super(KeyWidget, self).__init__()
        self.setObjectName("KeyWidgetItem")
        self.setMinimumWidth(400)
        self.setMinimumHeight(84)
        self.key = key
        fingerprint = key.fingerprint
        self.fingerprint = fingerprint
        self.keyfingerprint = QtWidgets.QLabel(fingerprint)
        self.keyfingerprint.setObjectName("keyfingerprint")
        date = key.creationtime.date()
        date_label = QtWidgets.QLabel(f"Created at: {date.strftime('%Y-%m-%d')}")
        date_label.setAlignment(Qt.AlignTop)
        date_label.setContentsMargins(0, 0, 0, 0)

        # UIDs
        uid_vboxlayout = QtWidgets.QVBoxLayout()
        uid_vboxlayout.setSpacing(0)
        uid_vboxlayout.setContentsMargins(0, 0, 0, 0)
        for uid in key.uids:
            uid_label = QtWidgets.QLabel(uid["value"])
            uid_vboxlayout.addWidget(uid_label)
        uid_widget = QtWidgets.QWidget()
        uid_widget.setLayout(uid_vboxlayout)

        # UID and date layout
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(uid_widget)
        hlayout.addWidget(date_label)
        hlayout.setAlignment(Qt.AlignTop)
        hlayout.setContentsMargins(11, 0, 11, 11)
        group_widget = QtWidgets.QWidget()
        group_widget.setLayout(hlayout)

        fp_group_layout = QtWidgets.QVBoxLayout()
        fp_group_layout.addWidget(self.keyfingerprint)
        fp_group_layout.addWidget(group_widget)

        self.setLayout(fp_group_layout)
        self.setToolTip("Double click to export public key")
        self.setObjectName("keywidget")

    def mouseDoubleClickEvent(self, event):
        if key_utils.export_public_key(self, self.fingerprint, self.key.get_pub_key()):
            self.success_dialog = MessageDialogs.success_dialog(
                "Exported public key successfully!"
            )
            self.success_dialog.show()


class KeyWidgetList(QtWidgets.QListWidget):
    def __init__(self, ks):
        super(KeyWidgetList, self).__init__()
        self.setObjectName("KeyWidgetList")
        self.ks = ks

        # Set layout.
        # self.layout = QtWidgets.QVBoxLayout(self)
        # self.setLayout(self.layout)
        self.updateList()
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.setMinimumHeight(400)
        self.currentItemChanged.connect(self.on_item_changed)

    def updateList(self):
        try:
            keys = self.ks.get_all_keys()
            keys.sort(key=lambda x: x.creationtime, reverse=True)
            for key in keys:
                kw = KeyWidget(key)
                item = QtWidgets.QListWidgetItem()
                item.setSizeHint(kw.sizeHint())
                self.addItem(item)
                self.setItemWidget(item, kw)
            if len(keys) > 0:
                # Select the top most row
                self.setCurrentRow(0)
        except Exception as e:
            print(e)

    def on_item_changed(self):
        print(self.selectedItems())

    def addnewKey(self, key):
        kw = KeyWidget(key)
        item = QtWidgets.QListWidgetItem()
        item.setSizeHint(kw.sizeHint())
        self.insertItem(0, item)
        self.setItemWidget(item, kw)
        self.setCurrentRow(0)
