import time

import johnnycanencrypt.johnnycanencrypt as rjce
from PySide2.QtCore import QThread, Signal


class HardwareThread(QThread):
    signal = Signal((bool,))

    def __init__(self, nextsteps_slot):
        QThread.__init__(self)
        self.flag = True
        self.signal.connect(nextsteps_slot)

    def run(self):
        while self.flag:
            time.sleep(1)
            result = rjce.is_smartcard_connected()
            self.signal.emit(result)
