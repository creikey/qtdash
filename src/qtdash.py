#!/usr/bin/env python

from PySide2.QtCore import Qt, Signal, QObject, Slot
from PySide2 import QtCore, QtWidgets, QtGui
from networktables import NetworkTables
import sys
import logging
import coloredlogs


STYLESHEET_NAME = "stylesheet.qss"
SERVER_URL = "127.0.0.1"


def connectionListener(connected, info, indicator_widget):
    logging.info(str(info) + ": Connected={}".format(connected))
    if connected:
        indicator_widget.setText("Connected")
    else:
        indicator_widget.setText("Disconnected")
    indicator_widget.setProperty("connected", connected)
    indicator_widget.style().unpolish(indicator_widget)
    indicator_widget.style().polish(indicator_widget)


def entryListener(key, value, isNew, layout, entrySignalHolder):
    entrySignalHolder.entrySignal.emit(
        str(key), str(value), isNew, layout)


class EntrySignalHolder(QObject):
    entrySignal = Signal((str, str, bool, QtWidgets.QGridLayout))

    def __init__(self):
        super().__init__()
        self.widget_dict = {}

    @Slot(str, str, bool, QtWidgets.QGridLayout)
    def rearrange_gui(self, key, value, isNew, layout):
        if key not in self.widget_dict:
            print("creating {}".format(key))
            self.widget_dict[key] = (QtWidgets.QPushButton(
                key), QtWidgets.QLabel(value))
            self.widget_dict[key][1].setAlignment(Qt.AlignRight)
            cur_row = len(self.widget_dict.keys())
            layout.addWidget(self.widget_dict[key][0], cur_row, 0, 1, 1)
            layout.addWidget(self.widget_dict[key][1], cur_row, 1, 1, 1)
        else:
            self.widget_dict[key][1].setText(value)


def main():
    NetworkTables.initialize(server=SERVER_URL)
    logger = logging.getLogger(__name__)
    coloredlogs.install(level='DEBUG')
    entrySignalHolder = EntrySignalHolder()
    entrySignalHolder.entrySignal.connect(entrySignalHolder.rearrange_gui)

    try:
        with open(STYLESHEET_NAME, "r") as stylesheet:
            app = QtWidgets.QApplication(sys.argv)
            app.setStyleSheet(stylesheet.read())
    except FileNotFoundError:
        logging.warn("Could not find stylesheet {}".format(STYLESHEET_NAME))
    scrollArea = QtWidgets.QScrollArea()
    window = QtWidgets.QWidget()
    layout = QtWidgets.QGridLayout()

    stat_label = QtWidgets.QLabel("Connection Status")
    stat_label.setAlignment(Qt.AlignLeft)
    layout.addWidget(stat_label, 0, 0, 1, 1)

    conn_status = QtWidgets.QLabel("Disconnected")
    conn_status.setAlignment(Qt.AlignRight)
    conn_status.setProperty("connected", False)
    layout.addWidget(conn_status, 0, 1, 1, 1)

    NetworkTables.addConnectionListener(
        lambda *args: connectionListener(*args, conn_status), immediateNotify=True)
    NetworkTables.addEntryListener(
        lambda *args: entryListener(*args, layout, entrySignalHolder))

    window.setLayout(layout)
    scrollArea.setWidget(window)
    scrollArea.setWidgetResizable(True)
    scrollArea.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
