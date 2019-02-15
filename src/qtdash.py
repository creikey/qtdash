#!/usr/bin/env python

from PySide2.QtCore import Qt, Signal, QObject, Slot
from PySide2 import QtCore, QtWidgets, QtGui
from networktables import NetworkTables
import sys
import logging
import coloredlogs
import re


STYLESHEET_NAME = "stylesheet.qss"
#SERVER_URL = "10.29.84.2"
SERVER_URL = "127.0.0.1"
cur_regex_matcher = re.compile(".*")


def connectionListener(connected, info, indicator_widget):
    logging.info(str(info) + ": Connected={}".format(connected))
    if connected:
        indicator_widget.setText("Connected")
    else:
        indicator_widget.setText("Disconnected")
    indicator_widget.setProperty("connected", connected)
    indicator_widget.style().unpolish(indicator_widget)
    indicator_widget.style().polish(indicator_widget)


def entryListener(key, value, isNew, layout, key_input, entrySignalHolder):
        entrySignalHolder.entrySignal.emit(
            str(key), str(value), isNew, layout, key_input)


class ValuePath(QtWidgets.QLineEdit):
    def __init__(self, *args):
        super().__init__(*args)

    @Slot(str)
    def change_cur_path(self, new_path):
        #logging.debug("Setting path to {}".format(new_path))
        self.setText(new_path)

class RegexEdit(QtWidgets.QLineEdit):
    filterEntries = Signal(())
    def __init__(self):
        super().__init__()
        self.editingFinished.connect(self.filter_entries)

    @Slot()
    def filter_entries(self):
        global cur_regex_matcher
        logging.debug("setting regex matcher. before: {}".format(cur_regex_matcher))
        cur_regex_matcher = re.compile(self.text(), flags=re.IGNORECASE)
        self.filterEntries.emit()


class DataEdit(QtWidgets.QLineEdit):
    def __init__(self, val_path_widget, type_dropdown_widget):
        super().__init__()
        self.editingFinished.connect(self.send_data)
        self.val_path_widget = val_path_widget
        self.type_dropdown_widget = type_dropdown_widget

    @Slot()
    def send_data(self):
        entry = NetworkTables.getEntry(self.val_path_widget.text())
        send_method = getattr(
            entry, self.type_dropdown_widget.currentText())
        send_method(self.text())
        #logging.debug(str(entry.__dict__))
        #entry.putString(self.text())


class ValuePathButton(QtWidgets.QPushButton):
    setValPath = Signal((str))

    def __init__(self, *args):
        super().__init__(*args)
        self.pressed.connect(self.button_pushed)

    @Slot()
    def button_pushed(self):
        #logging.debug("My text is {}".format(self.text()))
        self.setValPath.emit(self.text())


class EntrySignalHolder(QObject):
    entrySignal = Signal((str, str, bool, QtWidgets.QGridLayout, ValuePath))

    def __init__(self):
        super().__init__()
        self.widget_dict = {}

    @Slot()
    def filter_entries(self):
        global cur_regex_matcher
        logging.debug("Filtering entries with {}".format(cur_regex_matcher))
        for key in list(self.widget_dict.keys()):
            #logging.debug("KEY D OGer    : {}".format(key))
            if not cur_regex_matcher.search(key):
                logging.info("filtering {}".format(key))
                self.widget_dict[key][0].hide()
                self.widget_dict[key][1].hide()
            else:
                self.widget_dict[key][0].show()
                self.widget_dict[key][1].show()

    @Slot(str, str, bool, QtWidgets.QGridLayout, ValuePath)
    def rearrange_gui(self, key, value, isNew, layout, key_input):
        if key not in self.widget_dict:
            #logging.debug("creating {}".format(key))
            self.widget_dict[key] = (ValuePathButton(
                key), QtWidgets.QLabel(value))
            self.widget_dict[key][0].setValPath.connect(
                key_input.change_cur_path)
            self.widget_dict[key][1].setAlignment(Qt.AlignRight)
            cur_row = len(self.widget_dict.keys())
            layout.addWidget(self.widget_dict[key][0], cur_row, 0, 1, 1)
            layout.addWidget(self.widget_dict[key][1], cur_row, 1, 1, 1)
        else:
            self.widget_dict[key][1].setText(value)


def main():
    NetworkTables.initialize(server=SERVER_URL)
    smart_dash = NetworkTables.getTable("SmartDashboard")
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

    # window has to have multiple widgets
    window = QtWidgets.QWidget()
    window_layout = QtWidgets.QVBoxLayout()
    window.setLayout(window_layout)

    toolbox = QtWidgets.QWidget()
    toolbox_layout = QtWidgets.QGridLayout()
    toolbox.setLayout(toolbox_layout)

    vals = QtWidgets.QWidget()
    vals_layout = QtWidgets.QGridLayout()
    vals.setLayout(vals_layout)

    window_layout.addWidget(toolbox)
    window_layout.addWidget(scrollArea)

    stat_label = QtWidgets.QLabel("Connection Status")
    stat_label.setAlignment(Qt.AlignLeft)
    toolbox_layout.addWidget(stat_label, 0, 0, 1, 1)

    conn_status = QtWidgets.QLabel("Disconnected")
    conn_status.setAlignment(Qt.AlignRight)
    conn_status.setProperty("connected", False)
    toolbox_layout.addWidget(conn_status, 0, 1, 1, 1)

    key_input = ValuePath()
    toolbox_layout.addWidget(key_input, 1, 0, 1, 1)

    type_dropdown = QtWidgets.QComboBox()
    type_dropdown.addItem("setBoolean")  # TODO Add array and bytes support
    type_dropdown.addItem("setNumber")
    type_dropdown.addItem("setString")
    toolbox_layout.addWidget(type_dropdown, 1, 1, 1, 1)

    value_input = DataEdit(key_input, type_dropdown)
    toolbox_layout.addWidget(value_input, 1, 2, 1, 1)

    regex_edit = RegexEdit()
    regex_edit.filterEntries.connect(entrySignalHolder.filter_entries)
    toolbox_layout.addWidget(regex_edit, 2, 0, 1, 3)

    NetworkTables.addConnectionListener(
        lambda *args: connectionListener(*args, conn_status), immediateNotify=True)
    NetworkTables.addEntryListener(
        lambda *args: entryListener(*args, vals_layout, key_input, entrySignalHolder))

    scrollArea.setWidget(vals)
    scrollArea.setWidgetResizable(True)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
