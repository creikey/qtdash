#!/usr/bin/env python

from PySide2.QtCore import Qt
from PySide2 import QtCore, QtWidgets, QtGui
from networktables import NetworkTables
import sys
import logging
import coloredlogs

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')


STYLESHEET_NAME = "stylesheet.qss"
SERVER_URL = "127.0.0.1"

values = {}

initialized = NetworkTables.initialize(server=SERVER_URL)
if not initialized:
    logging.warn("NetworkTables failed to initialize")


def entryListener(key, value, isNew, val_dict):  # isNew is if new entry
    val_dict[key] = value


def connectionListener(connected, info, indicator_widget):
    logging.info(str(info) + ": Connected={}".format(connected))
    if connected:
        indicator_widget.setText("Connected")
    else:
        indicator_widget.setText("Disconnected")
    indicator_widget.setProperty("connected", connected)
    indicator_widget.style().unpolish(indicator_widget)
    indicator_widget.style().polish(indicator_widget)


class OnlineWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.text = QtWidgets.QLabel("Connection Status")
        self.conn_status = QtWidgets.QLabel("Disconnected")
        self.conn_status.setProperty("connected", False)
        self.text.setAlignment(Qt.AlignLeft)
        self.conn_status.setAlignment(Qt.AlignRight)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.conn_status)
        self.setLayout(self.layout)


if __name__ == "__main__":
    try:
        with open(STYLESHEET_NAME, "r") as stylesheet:
            app = QtWidgets.QApplication(sys.argv)
            app.setStyleSheet(stylesheet.read())
    except FileNotFoundError:
        logging.warn("Could not find stylesheet {}".format(STYLESHEET_NAME))
    window = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout()

    online_widget = OnlineWidget()
    NetworkTables.addConnectionListener(
        lambda *args: connectionListener(*args, online_widget.conn_status), immediateNotify=True)
    NetworkTables.addEntryListener(lambda *args: entryListener(*args, values))

    layout.addWidget(online_widget)

    window.setLayout(layout)
    window.show()
    sys.exit(app.exec_())
