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


def entryListener(key, value, isNew, val_dict, widget_dict, layout, entrySignalHolder):
    entrySignalHolder.entrySignal.emit(
        str(key), str(value), isNew, val_dict, widget_dict, layout)


class EntrySignalHolder(QObject):
    entrySignal = Signal((str, str, bool, dict, dict, QtWidgets.QGridLayout))


@Slot(str, str, bool, dict, dict, QtWidgets.QGridLayout)
def rearrange_gui(key, value, isNew, val_dict, widget_dict, layout):
    val_dict[key] = value
    if isNew:
        widget_dict[key] = (QtWidgets.QPushButton(
            key), QtWidgets.QLabel(value))
        cur_row = len(widget_dict.keys())
        layout.addWidget(widget_dict[key][0], cur_row, 0, 1, 1)
        layout.addWidget(widget_dict[key][1], cur_row, 1, 1, 1)
    else:
        widget_dict[key][1].setText(value)


def main():
    values = {}
    val_widgets = {}
    NetworkTables.initialize(server=SERVER_URL)
    logger = logging.getLogger(__name__)
    coloredlogs.install(level='DEBUG')
    entrySignalHolder = EntrySignalHolder()
    entrySignalHolder.entrySignal.connect(rearrange_gui)

    try:
        with open(STYLESHEET_NAME, "r") as stylesheet:
            app = QtWidgets.QApplication(sys.argv)
            app.setStyleSheet(stylesheet.read())
    except FileNotFoundError:
        logging.warn("Could not find stylesheet {}".format(STYLESHEET_NAME))
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
        lambda *args: entryListener(*args, values, val_widgets, layout, entrySignalHolder))

    window.setLayout(layout)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
