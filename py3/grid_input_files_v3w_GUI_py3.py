""""
Grid Input Files generator

This script will take lower and upper limits for A, B, and C, the number of grid points per dimension, and other spectroscopic parameters 
(temperature, max J value, frequency range, etc.) and generate a set of input files to be used by the autofit software.

TO-DO: 
take in input file instead of relying on user to adjust code!
clean-up and remove useless code!

GUI version:
Want to make a GUI for this that is as easy to use as possible, including standard accessibility measures.
This means that we want to get rid of as many hard coded parameters as we can and hand control over them
to the user instead, hopefully without overwhelming them. We're also going to want to incorporate things
like giving good feedback to the user so they understand what's happening and don't think everything's just
locked up.


"""

from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial
import copy
import matplotlib
matplotlib.use("Qt5Agg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import rcParams


import subprocess
import os
import sys
import multiprocessing
from multiprocessing import Process, Queue
import psutil
import re
import numpy
import string
import math
import time
from scipy.interpolate import *

class Ui_Dialog_First_Window(object):
    def setupUi(self, Dialog):

        Dialog.setObjectName("Dialog")
        Dialog.resize(275, 145)

        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.num_procs_label = QtWidgets.QLabel(Dialog)
        self.num_procs_label.setObjectName("num_procs_label")
        self.gridLayout.addWidget(self.num_procs_label, 0, 0, 1, 1)
        self.num_procs_input = QtWidgets.QLineEdit(Dialog)
        self.num_procs_input.setObjectName("num_procs_input")
        self.num_procs_input.setToolTip("This is the number of processors to use.")
        self.num_procs_input.setText(str(processors)) # Default value - way to autodetect?
        self.gridLayout.addWidget(self.num_procs_input, 0, 1, 1, 1)
        self.font_plus_button = QtWidgets.QPushButton(Dialog)
        self.font_plus_button.setObjectName = "font_plus_button"
        self.font_plus_button.clicked.connect(partial(self.font_plus,Dialog))
        self.gridLayout.addWidget(self.font_plus_button, 0, 5, 1, 1)
        self.font_minus_button = QtWidgets.QPushButton(Dialog)
        self.font_minus_button.setObjectName = "font_minus_button"
        self.font_minus_button.clicked.connect(partial(self.font_minus,Dialog))
        self.gridLayout.addWidget(self.font_minus_button, 0, 6, 1, 1)

        self.temp_label = QtWidgets.QLabel(Dialog)
        self.temp_label.setObjectName("temp_label")
        self.gridLayout.addWidget(self.temp_label, 1, 0, 1, 1)
        self.temp_input = QtWidgets.QLineEdit(Dialog)
        self.temp_input.setObjectName("temp_input")
        self.temp_input.setToolTip("Temperature (in K) at which the spectrum was collected.")
        self.temp_input.setText("2") # Default value
        self.gridLayout.addWidget(self.temp_input, 1, 1, 1, 1)
        self.Jmax_label = QtWidgets.QLabel(Dialog)
        self.Jmax_label.setObjectName("Jmax_label")
        self.gridLayout.addWidget(self.Jmax_label, 1, 2, 1, 1)
        self.Jmax_input = QtWidgets.QLineEdit(Dialog)
        self.Jmax_input.setObjectName("Jmax_input")
        self.Jmax_input.setToolTip("Maximum value of J to include in simulations / assignments.")
        self.Jmax_input.setText("10") # Default value
        self.gridLayout.addWidget(self.Jmax_input, 1, 3, 1, 1)

        self.gridLayout.addWidget(QHLine(), 2, 0, 1, 7)

        self.A_min_input = QtWidgets.QLineEdit(Dialog)
        self.A_max_input = QtWidgets.QLineEdit(Dialog)
        self.B_min_input = QtWidgets.QLineEdit(Dialog)
        self.B_max_input = QtWidgets.QLineEdit(Dialog)
        self.C_min_input = QtWidgets.QLineEdit(Dialog)
        self.C_max_input = QtWidgets.QLineEdit(Dialog)
        self.a_types_cb = QtWidgets.QCheckBox(Dialog)
        self.b_types_cb = QtWidgets.QCheckBox(Dialog)
        self.c_types_cb = QtWidgets.QCheckBox(Dialog)
        self.A_label = QtWidgets.QLabel(Dialog)
        self.B_label = QtWidgets.QLabel(Dialog)
        self.C_label = QtWidgets.QLabel(Dialog)

        self.advanced_settings_cb = QtWidgets.QCheckBox(Dialog)

        self.search_window_input = QtWidgets.QLineEdit(Dialog)
        self.num_grid_points_input = QtWidgets.QLineEdit(Dialog)
        self.spline_value_input = QtWidgets.QLineEdit(Dialog)
        self.search_window_label = QtWidgets.QLabel(Dialog)
        self.num_grid_points_label = QtWidgets.QLabel(Dialog)
        self.spline_value_label = QtWidgets.QLabel(Dialog)

        self.A_min_input.setObjectName("A_min_input")
        self.A_min_input.setToolTip("This is the minimum value of A in the grid search.")
        self.B_min_input.setObjectName("B_min_input")
        self.B_min_input.setToolTip("This is the minimum value of B in the grid search.")
        self.C_min_input.setObjectName("C_min_input")
        self.C_min_input.setToolTip("This is the minimum value of C in the grid search.")

        self.A_max_input.setObjectName("A_max_input")
        self.A_max_input.setToolTip("This is the maximum value of A in the grid search.")
        self.B_max_input.setObjectName("B_max_input")
        self.B_max_input.setToolTip("This is the maximum value of B in the grid search.")
        self.C_max_input.setObjectName("C_max_input")
        self.C_max_input.setToolTip("This is the maximum value of C in the grid search.")

        self.a_types_cb.setObjectName("a_types_cb")
        self.a_types_cb.setText("Include a-types")
        self.a_types_cb.setToolTip("If checked, search for molecules with an a-type dipole component.")
        self.b_types_cb.setObjectName("b_types_cb")
        self.b_types_cb.setText("Include b-types")
        self.b_types_cb.setToolTip("If checked, search for molecules with a b-type dipole component.")
        self.c_types_cb.setObjectName("c_types_cb")
        self.c_types_cb.setText("Include c-types")
        self.c_types_cb.setToolTip("If checked, search for molecules with a c-type dipole component.")

        self.advanced_settings_cb.setObjectName("advanced_settings_cb")
        self.advanced_settings_cb.setText("Advanced Settings")
        self.advanced_settings_cb.setToolTip("If checked, advanced settings are editable.")
        self.advanced_settings_cb.setChecked(False) # Leave unchecked by default.
        self.advanced_settings_cb.stateChanged.connect(self.advanced_settings_display)

        self.search_window_input.setObjectName("search_window_input")
        self.search_window_input.setToolTip("This is the width of the search window (in MHz) ")
        self.num_grid_points_input.setObjectName("num_grid_points_input")
        self.num_grid_points_input.setToolTip("This is the number of points to use per dimension of the search.")
        self.spline_value_input.setObjectName("spline_value_input")
        self.spline_value_input.setToolTip("This is the point spacing (in kHz) that the input spectrum file will be splined to.")

        self.A_min_input.setText("500") # Default value
        self.A_max_input.setText("5000") # Default value
        self.a_types_cb.setChecked(True) # Have it checked by default
        self.B_min_input.setText("100") # Default value
        self.B_max_input.setText("3000") # Default value
        self.b_types_cb.setChecked(True) # Have it checked by default
        self.C_min_input.setText("100") # Default value
        self.C_max_input.setText("3000") # Default value
        self.c_types_cb.setChecked(True) # Have it checked by default

        self.search_window_input.setText("500") # Default value
        self.num_grid_points_input.setText("15") # Default value
        self.spline_value_input.setText("2") # Default value

        self.search_window_label.hide() # Hide advanced settings by default
        self.search_window_input.hide()
        self.num_grid_points_label.hide()
        self.num_grid_points_input.hide()
        self.spline_value_label.hide()
        self.spline_value_input.hide()

        self.gridLayout.addWidget(self.A_min_input, 3, 0, 1, 1)
        self.gridLayout.addWidget(self.A_label, 3, 1, 1, 1)
        self.gridLayout.addWidget(self.A_max_input, 3, 2, 1, 1)
        self.gridLayout.addWidget(self.a_types_cb, 3, 3, 1, 1)
        self.gridLayout.addWidget(self.advanced_settings_cb, 3, 4, 1, 1)
        self.gridLayout.addWidget(self.search_window_label, 3, 5, 1, 1)
        self.gridLayout.addWidget(self.search_window_input, 3, 6, 1, 1)
        self.gridLayout.addWidget(self.B_min_input, 4, 0, 1, 1)
        self.gridLayout.addWidget(self.B_label, 4, 1, 1, 1)
        self.gridLayout.addWidget(self.B_max_input, 4, 2, 1, 1)
        self.gridLayout.addWidget(self.b_types_cb, 4, 3, 1, 1)
        self.gridLayout.addWidget(self.num_grid_points_label, 4, 5, 1, 1)
        self.gridLayout.addWidget(self.num_grid_points_input, 4, 6, 1, 1)
        self.gridLayout.addWidget(self.C_min_input, 5, 0, 1, 1)
        self.gridLayout.addWidget(self.C_label, 5, 1, 1, 1)
        self.gridLayout.addWidget(self.C_max_input, 5, 2, 1, 1)
        self.gridLayout.addWidget(self.c_types_cb, 5, 3, 1, 1)
        self.gridLayout.addWidget(self.spline_value_label, 5, 5, 1, 1)
        self.gridLayout.addWidget(self.spline_value_input, 5, 6, 1, 1)

        self.gridLayout.addWidget(QHLine(), 6, 0, 1, 7)

        self.file_import_label = QtWidgets.QLabel(Dialog)
        self.file_import_label.setObjectName("file_import_label")
        self.gridLayout.addWidget(self.file_import_label, 7, 0, 1, 1)
        self.file_import_input = QtWidgets.QLineEdit(Dialog)
        self.file_import_input.setObjectName("file_import_input")
        self.file_import_input.setToolTip("Name of the data file to be loaded and processed.")
        self.gridLayout.addWidget(self.file_import_input, 7, 1, 1, 3)
        self.browse_import_button = QtWidgets.QPushButton(Dialog)
        self.browse_import_button.setObjectName("browse_import_button")
        self.browse_import_button.clicked.connect(self.browse)
        self.gridLayout.addWidget(self.browse_import_button, 7, 4, 1, 1)
        self.load_button = QtWidgets.QPushButton(Dialog)
        self.load_button.setObjectName("load_button")
        self.load_button.clicked.connect(self.load_input)
        self.gridLayout.addWidget(self.load_button, 7, 5, 1, 1)
        self.load_button.setEnabled(False)
        self.plot_button = QtWidgets.QPushButton(Dialog)
        self.plot_button.setObjectName("plot_button")
        self.plot_button.clicked.connect(self.plot_input)
        self.gridLayout.addWidget(self.plot_button, 7, 6, 1, 1)
        self.plot_button.setEnabled(False)

        self.inten_low_input = QtWidgets.QLineEdit(Dialog)
        self.inten_high_input = QtWidgets.QLineEdit(Dialog)
        self.inten_label = QtWidgets.QLabel(Dialog)
        self.inten_low_input.setObjectName("inten_low_input")
        self.inten_low_input.setToolTip("This is the minimum threshold for a peak in intensity units of your data file.")
        self.inten_high_input.setObjectName("inten_high_input")
        self.inten_high_input.setToolTip("This is the maximum threshold for a peak in intensity units of your data file.")
        self.inten_low_input.setEnabled(False) # Turn off until after file is loaded
        self.inten_high_input.setEnabled(False)

        self.gridLayout.addWidget(self.inten_low_input, 8, 0, 1, 1)
        self.gridLayout.addWidget(self.inten_label, 8, 1, 1, 1)
        self.gridLayout.addWidget(self.inten_high_input, 8, 2, 1, 1)

        self.gridLayout.addWidget(QHLine(), 9, 0, 1, 7)

        self.file_export_label = QtWidgets.QLabel(Dialog) # Need to modify it so it's choosing a directory rather than a file...
        self.file_export_label.setObjectName("file_export_label")
        self.gridLayout.addWidget(self.file_export_label, 10, 0, 1, 1)
        self.file_export_input = QtWidgets.QLineEdit(Dialog)
        self.file_export_input.setObjectName("file_export_input")
        self.file_export_input.setToolTip("Name of the file that data will be saved to.")
        self.gridLayout.addWidget(self.file_export_input, 10, 1, 1, 3)
        self.browse_export_button = QtWidgets.QPushButton(Dialog)
        self.browse_export_button.setObjectName("browse_export_button")
        self.browse_export_button.clicked.connect(self.browse_export)
        self.gridLayout.addWidget(self.browse_export_button, 10, 4, 1, 1)

        self.gridLayout.addWidget(QHLine(), 11, 0, 1, 7)

        self.gen_files_button = QtWidgets.QPushButton(Dialog) # Needs to be updated to a "do the thing" for a specific, not FT thing.
        self.gen_files_button.setObjectName("gen_files_button")
        self.gen_files_button.clicked.connect(self.gen_files)
        self.gridLayout.addWidget(self.gen_files_button, 12, 0, 1, 4)
        self.gen_files_button.setEnabled(False)
        self.exit_button = QtWidgets.QPushButton(Dialog)
        self.exit_button.setObjectName("exit_button")
        self.exit_button.clicked.connect(app.quit) # Probably should interrupt if haven't saved yet
        self.gridLayout.addWidget(self.exit_button, 12, 4, 1, 3)

        self.status_window = QtWidgets.QTextEdit(Dialog)
        self.status_window.setObjectName("status_window")
        self.gridLayout.addWidget(self.status_window, 13, 0, 5, 7) # make it big!!!!
        self.status_window.setReadOnly(True)

        self.progress = QtWidgets.QProgressBar(Dialog)
        self.progress.setObjectName("progress")
        self.gridLayout.addWidget(self.progress, 18, 0, 1, 7)
        self.progress.setValue(0)

        self.font_plus_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl++"), self.font_plus_button)
        self.font_plus_button.shortcut.activated.connect(partial(self.font_plus,Dialog))
        self.font_minus_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+-"), self.font_minus_button)
        self.font_minus_button.shortcut.activated.connect(partial(self.font_minus,Dialog))
        self.browse_import_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+D"), self.browse_import_button)
        self.browse_import_button.shortcut.activated.connect(self.browse)
        self.load_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+L"), self.load_button)
        self.load_button.shortcut.activated.connect(self.load_input)
        self.plot_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+1"), self.plot_button)
        self.plot_button.shortcut.activated.connect(self.plot_input)
        self.browse_export_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+O"), self.browse_export_button)
        self.browse_export_button.shortcut.activated.connect(self.browse_export)
        self.gen_files_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+R"), self.gen_files_button)
        self.gen_files_button.shortcut.activated.connect(self.gen_files)
        self.exit_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self.exit_button)
        self.exit_button.shortcut.activated.connect(app.quit)

        self.font_plus_button.setWhatsThis("Shortcut: Ctrl++")
        self.font_minus_button.setWhatsThis("Shortcut: Ctrl+-")
        self.browse_import_button.setWhatsThis("Shortcut: Ctrl+D")
        self.load_button.setWhatsThis("Shortcut: Ctrl+L")
        self.plot_button.setWhatsThis("Shortcut: Ctrl+1")
        self.browse_export_button.setWhatsThis("Shortcut: Ctrl+O")
        self.gen_files_button.setWhatsThis("Shortcut: Ctrl+R")
        self.exit_button.setWhatsThis("Shortcut: Ctrl+Q")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Grid Autofit Input File Generation"))
        self.num_procs_label.setText(_translate("Dialog", "# of Processors"))
        self.font_plus_button.setText(_translate("Dialog", "Increase Font"))
        self.font_minus_button.setText(_translate("Dialog", "Decrease Font"))
        self.temp_label.setText(_translate("Dialog", "Temperature (K)"))
        self.Jmax_label.setText(_translate("Dialog", "Max J value"))
        self.A_label.setText(_translate("Dialog", "<= A (MHz) <="))
        self.B_label.setText(_translate("Dialog", "<= B (MHz) <="))
        self.C_label.setText(_translate("Dialog", "<= C (MHz) <="))
        self.search_window_label.setText(_translate("Dialog", "Search Size (MHz)"))
        self.num_grid_points_label.setText(_translate("Dialog", "# Grid Points"))
        self.spline_value_label.setText(_translate("Dialog", "Data Spacing (kHz)"))
        self.file_import_label.setText(_translate("Dialog", "Data File Name"))
        self.browse_import_button.setText(_translate("Dialog", "Browse Data"))
        self.load_button.setText(_translate("Dialog", "Load Data"))
        self.plot_button.setText(_translate("Dialog", "Plot Data"))
        self.inten_label.setText(_translate("Dialog", "<= Peak Height <="))
        self.file_export_label.setText(_translate("Dialog", "Output Folder Name"))
        self.browse_export_button.setText(_translate("Dialog", "Browse Output"))
        self.gen_files_button.setText(_translate("Dialog", "Generate Files!"))
        self.exit_button.setText(_translate("Dialog", "Exit"))

    def advanced_settings_display(self):
        adv_setting = self.advanced_settings_cb.isChecked()

        if adv_setting:
            self.search_window_label.show()
            self.search_window_input.show()
            self.num_grid_points_label.show()
            self.num_grid_points_input.show()
            self.spline_value_label.show()
            self.spline_value_input.show()
        else:
            self.search_window_label.hide()
            self.search_window_input.hide()
            self.num_grid_points_label.hide()
            self.num_grid_points_input.hide()
            self.spline_value_label.hide()
            self.spline_value_input.hide()

    def font_plus(self,Dialog):
        font = Dialog.font()
        curr_size = font.pointSize()
        new_size = curr_size + 3
        font.setPointSize(new_size)
        Dialog.setFont(font)

    def font_minus(self,Dialog):
        font = Dialog.font()
        curr_size = font.pointSize()
        new_size = curr_size - 3
        font.setPointSize(new_size)
        Dialog.setFont(font)

    def browse(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName()
        if fileName:
            self.file_import_input.setText(fileName)
            self.load_button.setEnabled(True)
            self.load_button.setFocus()
            self.plot_button.setEnabled(False)
            self.are_we_there_yet()

    def browse_export(self): # Need to select a folder rather than a file here
        folderName, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Enter name of new directory to be created", options=QtWidgets.QFileDialog.ShowDirsOnly)
        if folderName:
            self.file_export_input.setText(folderName)
            self.are_we_there_yet()

    def raise_error(self):
        self.are_we_there_yet()
        self.error_dialog = QtWidgets.QMessageBox()
        self.error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        self.error_dialog.setWindowTitle("Something's Wrong!")
        self.error_dialog.setText(self.error_message)
        self.error_dialog.show()

    def load_input(self):
        global xdata
        global ydata
        global low_intensity
        global high_intensity

        data_file = self.file_import_input.text()

        self.status_window.append("Loading data file! (This may take 20-30 seconds.)") # Force this update!
        QtWidgets.QApplication.processEvents()
        # Would be nice to add some status indicator since this can take a long time.

        # Spectra-containing files are big - need to spin this off to a separate thread so it doesn't freeze app.

        try:
            fh = numpy.loadtxt(data_file,delimiter=',') #loads full experimental data file, not just list of peaks. Should be in directory this script is run from (same as input file).
        except:
            try:
                fh = numpy.loadtxt(data_file)
            except:
                self.error_message = "%s couldn't be properly loaded. Try again with a different file or check the file for issues."%(data_file) # will probably want to try a whole bunch of things and then only raise an error if none of them work.
                self.raise_error()
                return 0

        xdata = copy.copy(fh[:,0]) # Need to handle both of these, just in case it's like an empty file (or has wrong number of columns or something)
        ydata = copy.copy(fh[:,1]) 
        low_intensity = numpy.mean(ydata)*2 # does this work? seems too easy. Probably not bad for semi-sparse spectra
        high_intensity = max(ydata)*1.05 # later actually read it in, but this isn't a bad guess
        self.status_window.append("Data file loaded successfully!")
        self.plot_button.setEnabled(True)
        self.inten_low_input.setEnabled(True)
        self.inten_high_input.setEnabled(True)
        self.inten_low_input.setText((str(low_intensity))[0:7])
        self.inten_high_input.setText((str(high_intensity))[0:7])
        self.are_we_there_yet()

    def plot_input(self):
        global low_intensity
        global high_intensity

        try:
            low_intensity = float(self.inten_low_input.text())
        except:
            self.error_message = "The low intensity threshold should be a number!"
            self.raise_error()
            self.inten_low_input.setFocus()
            return 0

        try:
            high_intensity = float(self.inten_high_input.text())
        except:
            self.error_message = "The high intensity threshold should be a number!"
            self.raise_error()
            self.inten_high_input.setFocus()
            return 0

        rcParams.update({'figure.autolayout': True}) # Magic from here: https://stackoverflow.com/questions/6774086/why-is-my-xlabel-cut-off-in-my-matplotlib-plot

        self.plot = Actual_Plot()
        self.plot.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self.plot)
        self.plot.shortcut.activated.connect(self.plot.close)
        self.plot.alt_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self.plot)
        self.plot.alt_shortcut.activated.connect(self.plot.close)
        self.plot.show()

    def gen_files(self): # will eventually do the thing
        # start it out with checks on all of the fields, then pass it off to the worker thread
        # do the checks here
        global low_intensity
        global high_intensity

        try:
            num_procs = int(self.num_procs_input.text())
        except:
            self.error_message = "The number of processors should be an integer!"
            self.raise_error()
            self.num_procs_input.setFocus()
            return 0

        if num_procs > processors:
            self.error_message = "The number of processors you've set is greater than the number of physical cores on your machine. This will lead to significant performance degradation; please reduce the number of processors."
            self.raise_error()
            self.num_procs_input.setFocus()
            return 0

        try:
            temperature = float(self.temp_input.text())
        except:
            self.error_message = "The temperature should be a number!"
            self.raise_error()
            self.temp_input.setFocus()
            return 0

        try:
            Jmax = int(self.Jmax_input.text())
        except:
            self.error_message = "The maximum value of J should be an integer!"
            self.raise_error()
            self.Jmax_input.setFocus()
            return 0

        try:
            Amin = float(self.A_min_input.text())
        except:
            self.error_message = "The lower limit on A should be a number!"
            self.raise_error()
            self.A_min_input.setFocus()
            return 0

        try:
            Amax = float(self.A_max_input.text())
        except:
            self.error_message = "The upper limit on A should be a number!"
            self.raise_error()
            self.A_max_input.setFocus()
            return 0

        try:
            Bmin = float(self.B_min_input.text())
        except:
            self.error_message = "The lower limit on B should be a number!"
            self.raise_error()
            self.B_min_input.setFocus()
            return 0

        try:
            Bmax = float(self.B_max_input.text())
        except:
            self.error_message = "The upper limit on B should be a number!"
            self.raise_error()
            self.B_max_input.setFocus()
            return 0

        try:
            Cmin = float(self.C_min_input.text())
        except:
            self.error_message = "The lower limit on C should be a number!"
            self.raise_error()
            self.C_min_input.setFocus()
            return 0

        try:
            Cmax = float(self.C_max_input.text())
        except:
            self.error_message = "The upper limit on C should be a number!"
            self.raise_error()
            self.C_max_input.setFocus()
            return 0

        try:
            search_window = float(self.search_window_input.text())
        except:
            self.error_message = "The search window should be a number!"
            self.raise_error()
            self.search_window_input.setFocus()
            return 0

        try:
            grid_points = int(self.num_grid_points_input.text())
        except:
            self.error_message = "The number of grid points should be an integer!"
            self.raise_error()
            self.num_grid_points_input.setFocus()
            return 0

        try:
            resolution = float(self.spline_value_input.text())
        except:
            self.error_message = "The final resolution to spline to should be a number!"
            self.raise_error()
            self.spline_value_input.setFocus()
            return 0

        try:
            low_intensity = float(self.inten_low_input.text())
        except:
            self.error_message = "The low intensity threshold should be a number!"
            self.raise_error()
            self.inten_low_input.setFocus()
            return 0

        try:
            high_intensity = float(self.inten_high_input.text())
        except:
            self.error_message = "The high intensity threshold should be a number!"
            self.raise_error()
            self.inten_high_input.setFocus()
            return 0

        # Now we decide which searches to do based on the check boxes.

        a_flag = self.a_types_cb.isChecked()
        b_flag = self.b_types_cb.isChecked()
        c_flag = self.c_types_cb.isChecked()

        dipole_string = ""

        if a_flag:
            dipole_string += "a"
        if b_flag:
            dipole_string += "b"
        if c_flag:
            dipole_string += "c"

        # We need to hopefully make sure users know that we're going to do searches of all combinations consistent with flags (e.g. type ab means we check ab, a only, and b only). What's the best way to inform them?
        if dipole_string == "":
            self.error_message = "At least one of the dipole types should be checked to perform a search!"
            self.raise_error()
            self.a_types_cb.setFocus()
            return 0

        # Still need to test output label, but may make more sense to do that when we need them. That said, verifying we can create the new directory should be done very early in the worker script.
        data_file = self.file_import_input.text()
        out_dir_name = self.file_export_input.text()

        job_name = out_dir_name # Do the processing on it here...

        x = subprocess.Popen("dir /b", stdout=subprocess.PIPE, shell=True) # Windows specific code...
        x = x.stdout.read().split()

        file_flag = 1
    
        while file_flag==1:
            marker1 = 0
            for file1 in x:
                if job_name ==file1:
                    marker1 = 1
                    job_name += 'a' # Need to do something cleverer than this later, but this will be fine for now.  I also like that doing this repeatedly will make a file name that screams at you. 
            if marker1 ==0:
                file_flag =0
        
        # Need to do try/except here, with return on failure:
        try:
            a = subprocess.Popen("mkdir \"%s\""%job_name, shell=True) # Will almost certainly need to do string parsing on job name to only grab last part of it
            a.wait()
        except:
            self.error_message = "Couldn't create directory %s. Please use another name and try again."%job_name
            self.raise_error()
            self.file_export_input.setFocus()
            return 0

        self.status_window.append("Starting to generate input files!")

        # worker/threading stuff starts here
        thread = self.thread = QtCore.QThread()
        worker = self.worker = Worker(num_procs,temperature,Jmax,Amin,Amax,Bmin,Bmax,Cmin,Cmax,search_window,grid_points,resolution,dipole_string,data_file,out_dir_name) # will want to give it whatever arguments it needs
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self.progress_update)
        worker.status.connect(self.status_update)
        worker.done.connect(self.exit_update)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        worker.finished.connect(thread.quit)
        thread.start()
        pass

    def are_we_there_yet(self): #logic flow controller, may not actually need
    # need to check for whether or not data has been chosen and loaded and whether or not output folder name has been chosen (and is valid(?))
        if self.file_import_input.text() != '':
            have_data_file = True
        else:
            have_data_file = False

        if self.file_export_input.text() != '':
            have_export_dir = True
        else:
            have_export_dir = False

        if self.plot_button.isEnabled():
            data_loaded = True
        else:
            data_loaded = False

        if have_data_file == False:
            self.browse_import_button.setFocus()
            self.load_button.setEnabled(False)
            self.plot_button.setEnabled(False)
            self.gen_files_button.setEnabled(False)
            return False
        else: # we have a data file
            if data_loaded == False:
                self.load_button.setEnabled(True)
                self.load_button.setFocus()
                self.plot_button.setEnabled(False)
                self.gen_files_button.setEnabled(False)
                return False
            else: # the data file has been loaded
                if have_export_dir == False:
                    self.browse_export_button.setFocus()
                    self.gen_files_button.setEnabled(False)
                    return False
                else: # we have an export filename
                    self.gen_files_button.setEnabled(True)
                    self.gen_files_button.setFocus()
                    return True        

    def progress_update(self,value):
        self.progress.setValue(value)

    def status_update(self,value):
        self.status_window.append(value) # Force this update!

    def exit_update(self,value):
        if value:
            self.status_window.append("Complete!")
            self.exit_button.setFocus()

    def error_update(self,value):
        self.error_message = value
        self.raise_error()

class QHLine(QtWidgets.QFrame): # Using this: https://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)

class WidgetPlot(QtWidgets.QWidget): # Trying this one: https://stackoverflow.com/questions/48140576/matplotlib-toolbar-in-a-pyqt5-application
    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.canvas = PlotCanvas(self, width=10, height=8)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=10, height=8, dpi=100):
        fig = Figure(figsize=(width,height), dpi=dpi)
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()

    def plot(self):
        ax = self.figure.add_subplot(111)
        ax.plot(xdata,ydata,'-')
        ax.axhline(y=low_intensity,color='r',linestyle='--') # Fix me!
        ax.axhline(y=high_intensity,color='r',linestyle='--')
        ax.set_title('Spectrum + Intensity Thresholds')
        ax.set_xlabel('Frequency (MHz)')
        ax.set_ylabel('Intensity (arb. units)')
        self.draw()

class Actual_Plot(QtWidgets.QMainWindow):
    def __init__(self, **kwargs):
        QtWidgets.QMainWindow.__init__(self)
        self.__dict__.update(kwargs)

        self.title = 'Plot of Spectrum with Intensity Thresholds'

        self.left = 300
        self.top = 300
        self.width = 500
        self.height = 400

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        widget = QtWidgets.QWidget(self)
        self.setCentralWidget(widget)
        vlay = QtWidgets.QVBoxLayout(widget)
        hlay = QtWidgets.QHBoxLayout()
        vlay.addLayout(hlay)

        m = WidgetPlot(self)
        vlay.addWidget(m)

class Worker(QtCore.QObject): # looks like we need to use threading in order to get progress bars to update!
# Thanks go to this thread: https://gis.stackexchange.com/questions/64831/how-do-i-prevent-qgis-from-being-detected-as-not-responding-when-running-a-hea
    def __init__(self, num_procs, temperature, Jmax, Amin, Amax, Bmin, Bmax, Cmin, Cmax, search_window, grid_points, resolution, dipole_string, data_file, out_dir_name, *args, **kwargs):
        QtCore.QObject.__init__(self, *args, **kwargs)
        self.percentage = 0
        self.num_procs = num_procs
        self.temperature = temperature
        self.Jmax = Jmax
        self.Amin = Amin
        self.Amax = Amax
        self.Bmin = Bmin
        self.Bmax = Bmax
        self.Cmin = Cmin
        self.Cmax = Cmax
        self.search_window = search_window
        self.grid_points = grid_points
        self.resolution = resolution
        self.dipole_string = dipole_string
        self.data_file = data_file
        self.out_dir_name = out_dir_name

    def run(self):
        # do real stuff or something
        DJ = "0.0"
        DJK = "0.0"
        DK = "0.0"
        dJ = "0.0"
        dK = "0.0"

        inten_high = high_intensity
        inten_low = low_intensity
        freq_uncertainty = self.search_window
        temperature = self.temperature
        Jmax = self.Jmax

        Amin = self.Amin
        Amax = self.Amax
        Bmin = self.Bmin
        Bmax = self.Bmax
        Cmin = self.Cmin
        Cmax = self.Cmax

        grid_pts = self.grid_points
        dipole_string = self.dipole_string

        data_file = self.data_file

        Avals = []
        Bvals = []
        Cvals = []

        for i in range(grid_pts):
            Avals.append(int(Amin + ((Amax - Amin) / (grid_pts - 1))*i))
            Bvals.append(int(Bmin + ((Bmax - Bmin) / (grid_pts - 1))*i))
            Cvals.append(int(Cmin + ((Cmax - Cmin) / (grid_pts - 1))*i))

        job_name = self.out_dir_name

        splined_spectrum = cubic_spline(self.resolution) # Interpolates experimental spectrum to a 2 kHz resolution with a cubic spline.  Gives better peak-pick values.
        (peaklist, freq_low, freq_high) = peakpicker(splined_spectrum,inten_low,inten_high) # Calls slightly modified version of Cristobal's routine to pick peaks instead of forcing user to do so.

        # Need to check that SPCAT already exists in this directory!
        for num in range(processors):
            y = subprocess.Popen("copy SPCAT.EXE \"%s\SPCAT%s.EXE\""%(job_name,num), stdout=subprocess.PIPE, shell=True) # Windows specific, need to have SPCAT.EXE already
            y.stdout.read() 
    
        os.chdir(job_name)
        #print "The job_name as of line 767 is %s"%job_name


        temp_peaklist = ""

        for item in peaklist:
            if temp_peaklist != "":
                temp_peaklist += "\n"
            temp_string = "%s, %s"%(str(item[0]),str(item[1]))
            temp_peaklist = temp_peaklist + temp_string

        peaklist_fh = open("peaklist.txt","w")
        peaklist_fh.write(temp_peaklist)
        peaklist_fh.close()

        grid_counter = 0
        obj_list = []

        for Apoint in Avals:
            for Bpoint in Bvals:

                if (Bpoint > Apoint):
                    break

                else:
                    for Cpoint in Cvals:
                        if (Cpoint > Bpoint) or (Cpoint > Apoint):
                            break
                    
                        else:

                            grid_counter += 1 # This will be the total number of files made at the end; could use for progress bar / percentage tracking

                            if Apoint == Bpoint:
                                Apoint = Apoint*1.05

                            if Bpoint == Cpoint:
                                Bpoint = Bpoint*1.05

                            A = str(Apoint)
                            B = str(Bpoint)
                            C = str(Cpoint)

                            obj_list.append((A,B,C,freq_uncertainty,freq_low,freq_high,Jmax,temperature,DJ,DJK,DK,dJ,dK,job_name,peaklist,grid_counter))

        q = Queue()
        finished_tracker = numpy.zeros(processors, dtype=int)
        counter_tracker = numpy.zeros(processors)

        for num in range(processors):
            procs = float(processors)
            fnum = float(num)
            x = int((fnum)*(len(obj_list)/procs))
            y = int(len(obj_list)*((fnum+1)/procs))
            vars()["p%s"%str(num)] = Process(target=grid_point_file_gen, args=(q,obj_list,x,y,num,data_file,processors,inten_low,inten_high,dipole_string))

        start_time = time.time()

        for num in range(processors):
            vars()["p%s"%str(num)].start()

        while True: # have it break when it receives a "done" from everyone
            try:
                [curr_counter,frac_counter,message,which_proc] = q.get()
                if message == "Processing":
                    counter_tracker[which_proc] = frac_counter
                    total_progress = sum(counter_tracker)
                    percentage = int(math.floor(100.0*(float((total_progress)/float(processors)))))
                    self.calculate_progress(percentage)
                    if percentage > 1:
                        current_time = time.time()
                        elapsed_time = current_time - start_time
                        remaining_time = (elapsed_time*100/percentage) - elapsed_time
                        temp_string = "%s percent complete by file number! Taken %s seconds so far, about %s seconds remaining."%(percentage,int(math.ceil(elapsed_time)),int(math.ceil(remaining_time)))
                        self.status.emit(temp_string)
                if message == "Done":
                    finished_tracker[which_proc] = 1
            except EOFError:
                pass
            # if everything is done, then break
            if (all(value != 0 for value in finished_tracker)):
                self.done.emit(True)
                self.finished.emit(True)
                break

        for num in range(processors):
            vars()["p%s"%str(num)].join() # Do we get some signal when these start or finish? Can we use it to do the progress bar / percentage thing? Need to learn more about process, start, join, etc.

        #print "Complete!"

    def calculate_progress(self,percentage_new):

        if percentage_new > self.percentage:
            self.percentage = percentage_new
            self.progress.emit(self.percentage)

    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(bool)
    done = QtCore.pyqtSignal(bool)
    status = QtCore.pyqtSignal(str)



def int_writer(u_A,u_B,u_C,num, J_min="00", J_max="20", inten="-10.0",Q_rot="300000",freq="25.8", temperature="298"):#generates SPCAT input file
    input_file = ""
    input_file += "Molecule \n"
    input_file += "0  91  %s  %s  %s  %s  %s %s  %s\n"%(Q_rot, J_min, J_max,inten,inten,freq, temperature)
    input_file += " 001  %s \n" % u_A
    input_file += " 002  %s \n" % u_B
    input_file += " 003  %s \n" % u_C

    fh_int = open("default%s.int"%(str(num)), "w")

    fh_int.write(input_file)
    fh_int.close()


def var_writer(A,B,C,DJ,DJK,DK,dJ,dK,num):#generates SPCAT input file

	dA = str(0.05*float(A))  #These are very rough estimates of the uncertainty on the rotational constants.  May need to be considerably refined.
	dB = str(0.05*float(B))
	dC = str(0.05*float(C))
	dDJ = str(0.2*float(DJ))
	dDJK = str(0.2*float(DJK))
	dDK = str(0.2*float(DK))
	ddJ = str(0.2*float(dJ))
	ddK = str(0.2*float(dK))

	fh_var = open("default%s.var"%(str(num)),'w')

	input_file = ""
	input_file += "anisole                                         Wed Mar Thu Jun 03 17:45:45 2010\n"
	input_file += "   8  430   51    0    0.0000E+000    1.0000E+005    1.0000E+000 1.0000000000\n"
	input_file +="a   1  1  0  99  0  1  1  1  1  -1   0\n"
	input_file += "           10000  %s %s \n" %(A,dA)
	input_file += "           20000  %s %s \n" %(B, dB)
	input_file += "           30000  %s %s \n" %(C, dC)
	input_file += "             200  %s %s \n" %(DJ, dDJ)
	input_file += "            1100  %s %s \n" %(DJK, dDJK) #need to actually check numbers: SPFIT doesn't read -- as a positive!
	input_file += "            2000  %s %s \n" %(DK, dDK)
	input_file += "           40100  %s %s \n" %(dJ, ddJ)
	input_file += "           41000  %s %s \n" %(dK, ddK)
	
	fh_var.write(input_file)
	fh_var.close()

def cubic_spline(new_resolution_kHz): # Cubic spline of spectrum to new_resolution; used pre-peak-picking.  Assumes spectrum is already in order of increasing frequency.

    x = copy.copy(xdata)
    y = copy.copy(ydata)

    new_resolution = new_resolution_kHz / 1000.0

    old_resolution = (x[-1]-x[0]) / len(x)
    scale_factor = old_resolution / new_resolution

    new_length = int(math.floor(scale_factor*len(x)))

    tck = splrep(x,y,s=0)
    xnew = numpy.arange(x[0],x[-1],new_resolution)
    ynew = splev(xnew,tck,der=0)

    output_spectrum = numpy.column_stack((xnew,ynew))

    return output_spectrum

def peakpicker(spectrum,thresh_l,thresh_h):#Code taken from Cristobal's peak-picking script; assumes spectrum is in increasing frequency order
    peaks=[]
    for i in range(1, len(spectrum)-1):
        if spectrum[i,1] > thresh_l and spectrum[i,1] < thresh_h and spectrum[i,1] > spectrum[(i-1),1] and spectrum[i,1] > spectrum[(i+1),1]:
            peaks.append(spectrum[i])

    peakpicks=numpy.zeros((len(peaks),2))
    for i,row in enumerate(peaks):
        peakpicks[i,0]=row[0]
        peakpicks[i,1]=row[1]
    freq_low = spectrum[0,0]
    freq_high = spectrum[-1,0]
    return peakpicks, freq_low, freq_high

def run_SPCAT(num): 
    #a = subprocess.Popen("SPCAT default", stdout=subprocess.PIPE, shell=False)
    #a.stdout.read()#seems to be best way to get SPCAT to finish. I tried .wait(), but it outputted everything to screen
    a = subprocess.call(["SPCAT%s"%(str(num)), "default%s"%(str(num))], stdout=open(os.devnull, 'wb'))
 
def cat_reader(freq_high,freq_low,num): #reads output from SPCAT

	fh = open("default%s.cat"%(str(num)))

	linelist = []
	for line in fh:
		if line[8:9]==".": 
			freq = line[3:13]
			inten = line[22:29]
			qnum_up = line[55:61]
			qnum_low = line[67:73]
			uncert = line[13:21]
			if float(freq)> freq_low and float(freq)<freq_high:#<<<<<<<<<<<<<<<<<<<<
				linelist.append((inten,freq, qnum_up, qnum_low,uncert))

	linelist.sort()
	fh.close()
	return linelist
    
def gen_full_list(u_A,u_B,u_C,Jmax,freq_low,freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,num): # Generates full list from cat file

    int_writer(u_A,u_B,u_C,num, J_max=Jmax,freq=str((freq_high*.001)), temperature=temperature)
    var_writer(A,B,C,DJ,DJK,DK,dJ,dK,num)
    run_SPCAT(num)

    full_list = cat_reader(freq_high,freq_low,num)   # New code starts here
    full_list_length = len(full_list)

    return full_list,full_list_length


def generate_trans(u_A,u_B,u_C,Jmax,freq_low,freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,full_list,num): #Generates main transition peaks

    trans_1 = "" 
    trans_2 = ""
    trans_3 = ""

    (highest_uncert,trans_1,trans_2,trans_3) = triple_selection(full_list,A,B,C,DJ,DJK,DK,dJ,dK,temperature,freq_high,freq_low,u_A,u_B,u_C,Jmax,num)

    trans_1_uncert = float(trans_1[4])
    trans_2_uncert = float(trans_2[4])
    trans_3_uncert = float(trans_3[4])

    return trans_1,trans_2,trans_3

def generate_check(u_A,u_B,u_C,Jmax,freq_low,freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,trans_1,trans_2,trans_3,num): #Generates check list

    int_writer(u_A,u_B,u_C,num, J_max=Jmax,freq=str((freq_high*.001)), temperature=temperature)
    var_writer(A,B,C,DJ,DJK,DK,dJ,dK,num)
    run_SPCAT(num)
            
    top_peaks = cat_reader(freq_high, freq_low, num)[0:10] #grab the most intense peaks from the predicted spectrum
    
    top_peaks_3cut = []
    for entry in top_peaks:
        if (entry[2] == trans_1[2] and entry[3] == trans_1[3]) or (entry[2] == trans_2[2] and entry[3] == trans_2[3]) or (entry[2] == trans_3[2] and entry[3] == trans_3[3]):
            pass
        else:
            top_peaks_3cut.append(entry)

    return top_peaks_3cut

def dependence_test(A,B,C,DJ,DJK,DK,dJ,dK,trans_1,trans_2,trans_3,T,freq_high, freq_low,u_A,u_B,u_C,Jmax,num):
    int_writer(u_A,u_B,u_C,num, J_min="00", J_max=Jmax, inten="-10.0",Q_rot="300000",freq="100.0", temperature=T)

    var_writer(A+(2),B,C,DJ,DJK,DK,dJ,dK,num)
    run_SPCAT(num)
    high_peak_freq = trans_freq_reader(trans_1, trans_2, trans_3, num)

    var_writer(A-(2),B,C,DJ,DJK,DK,dJ,dK,num)
    run_SPCAT(num)
    low_peak_freq = trans_freq_reader(trans_1, trans_2, trans_3, num)

    dv1A = (float(high_peak_freq[0])-float(low_peak_freq[0]))/4
    dv2A = (float(high_peak_freq[1])-float(low_peak_freq[1]))/4
    dv3A = (float(high_peak_freq[2])-float(low_peak_freq[2]))/4

    var_writer(A,B+(2),C,DJ,DJK,DK,dJ,dK,num)
    run_SPCAT(num)
    high_peak_freq = trans_freq_reader(trans_1, trans_2, trans_3, num)

    var_writer(A,B-(2),C,DJ,DJK,DK,dJ,dK,num)
    run_SPCAT(num)
    low_peak_freq = trans_freq_reader(trans_1, trans_2, trans_3, num)

    dv1B = (float(high_peak_freq[0])-float(low_peak_freq[0]))/4
    dv2B = (float(high_peak_freq[1])-float(low_peak_freq[1]))/4
    dv3B = (float(high_peak_freq[2])-float(low_peak_freq[2]))/4

    var_writer(A,B,C+(2),DJ,DJK,DK,dJ,dK,num)
    run_SPCAT(num)
    high_peak_freq = trans_freq_reader(trans_1, trans_2, trans_3, num)

    var_writer(A,B,C-(2),DJ,DJK,DK,dJ,dK,num)
    run_SPCAT(num)
    low_peak_freq = trans_freq_reader(trans_1, trans_2, trans_3, num)

    dv1C = (float(high_peak_freq[0])-float(low_peak_freq[0]))/4
    dv2C = (float(high_peak_freq[1])-float(low_peak_freq[1]))/4
    dv3C = (float(high_peak_freq[2])-float(low_peak_freq[2]))/4

    var_writer(A,B,C,DJ,DJK,DK,dJ,dK,num)   # This re-runs SPCAT at the initial constants so that other things that read from default.cat are correct after this function is executed.
    run_SPCAT(num)

    matrix = numpy.array([(dv1A,dv1B,dv1C),(dv2A,dv2B,dv2C),(dv3A,dv3B,dv3C)])
    return numpy.linalg.det(matrix)


def triple_selection(full_list,A,B,C,DJ,DJK,DK,dJ,dK,temperature,freq_high,freq_low,u_A,u_B,u_C,Jmax,num):

    total_check_num = 10 # This is the number of peaks used to generate possible triples, ordered by intensity. 10 = 120 possibilities, 15 = 455 possibilities.
    triples_scores = []
    scaled_triples_scores = []
    max_dependence = 0
    max_RMS = 0
    max_intensity = 0
    margin = 750 # Should fix this later so it's not hard-coded, should be based on the uncertainty instead.

    for i in range(0,total_check_num-2):
        for j in range(i+1,total_check_num-1):
            for k in range(j+1,total_check_num):
                boundary_penalty = 0
                trans_1 = full_list[i]
                trans_2 = full_list[j]
                trans_3 = full_list[k]
                dependence = abs(dependence_test(float(A),float(B),float(C),float(DJ),float(DJK),float(DK),float(dJ),float(dK),trans_1,trans_2,trans_3,temperature,freq_high,freq_low,u_A,u_B,u_C,Jmax,num))
                worst_RMS = max(float(trans_1[4]),float(trans_2[4]),float(trans_3[4]))
                RMS_ratio = (worst_RMS/min(float(trans_1[4]),float(trans_2[4]),float(trans_3[4])))
                RMS_function = RMS_ratio*worst_RMS
                intensity_avg = abs(float(trans_1[0])+float(trans_2[0])+float(trans_3[0]))/3 # For all sane T and dipoles, intensities are negative, so the greatest sum of abs(intensity) is the smallest set of peaks.

                if (abs(float(trans_1[1])-freq_low) <= margin) or (abs(float(trans_1[1])-freq_high) <= margin):
                    boundary_penalty += 1
                if (abs(float(trans_2[1])-freq_low) <= margin) or (abs(float(trans_2[1])-freq_high) <= margin):
                    boundary_penalty += 1
                if (abs(float(trans_3[1])-freq_low) <= margin) or (abs(float(trans_3[1])-freq_high) <= margin):
                    boundary_penalty += 1

                if boundary_penalty < 2: # Only allow combinations with one transition past the boundary to be considered...
                    triples_scores.append((i,j,k,dependence,RMS_function,intensity_avg,worst_RMS,boundary_penalty))

                if dependence > max_dependence:
                    max_dependence = dependence
                if RMS_function > max_RMS:
                    max_RMS = RMS_function
                if intensity_avg > max_intensity:
                    max_intensity = intensity_avg

    for entry in triples_scores:
        scaled_dep = entry[3]/max_dependence # big dependence is good and should help the score, big values of RMS and intensity are bad and should hurt the score.
        scaled_RMS = 1 - entry[4]/max_RMS
        scaled_inten = 1 - entry[5]/max_intensity
        boundary_penalty_scale = 1 / (1 + entry[7])
        scaled_score = (30*scaled_dep + 60*scaled_RMS + 10*scaled_inten)*boundary_penalty_scale # Reduces score based on how many transitions are close to a spectrum edge.
        silly_easyGUI_hack = 1 - (scaled_score/100)    # EasyGUI does a sort before displaying choices, presenting them from least to greatest.  This is a way to get it to display triples choices in the order that I want it to, from best to worst.
        scaled_triples_scores.append((entry[0],entry[1],entry[2],entry[3],entry[4],entry[5],scaled_dep,scaled_RMS,scaled_inten,scaled_score,silly_easyGUI_hack,entry[6]))

    triples_choice_list = []
    for entry in scaled_triples_scores:
        trans_1 = full_list[entry[0]]
        trans_2 = full_list[entry[1]]
        trans_3 = full_list[entry[2]]
        triples_choice_list.append((entry[10],entry[9],entry[11],trans_1[1],trans_1[2],trans_1[3],trans_2[1],trans_2[2],trans_2[3],trans_3[1],trans_3[2],trans_3[3],trans_1[4],trans_2[4],trans_3[4],entry[0],entry[1],entry[2]))

    sorted_triples_choice_list = sorted(triples_choice_list, key=lambda x: x[1], reverse=True)
    choice = sorted_triples_choice_list[0]

    highest_uncert = float(choice[2])
    trans_1 = full_list[int(choice[-3])]
    trans_2 = full_list[int(choice[-2])]
    trans_3 = full_list[int(choice[-1])]

    return highest_uncert,trans_1,trans_2,trans_3


def trans_freq_reader(trans_1, trans_2, trans_3, num):

    peak_1_freq = 0
    peak_2_freq = 0
    peak_3_freq = 0

    pred_peaks = cat_reader(1000000, 0, num)
    for peak in pred_peaks:
        if trans_1[2] == peak[2] and trans_1[3] == peak[3]:
            peak_1_freq = peak[1]
        if trans_2[2] == peak[2] and trans_2[3] == peak[3]:
            peak_2_freq = peak[1]
        if trans_3[2] == peak[2] and trans_3[3] == peak[3]:
            peak_3_freq = peak[1]
    return peak_1_freq,peak_2_freq,peak_3_freq

def check_bounds(trans_1_center,trans_2_center,trans_3_center,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,freq_low,freq_high):
    bad_windows = 0
    bad_1 = 0
    bad_2 = 0
    bad_3 = 0

    if (trans_1_center-peak_1_uncertainty) < freq_low:
        bad_windows = 1
        bad_1 = -1
    if (trans_1_center+peak_1_uncertainty) > freq_high:
        bad_windows = 1
        bad_1 = 1
    if (trans_2_center-peak_2_uncertainty) < freq_low:
        bad_windows = 1
        bad_2 = -1
    if (trans_2_center+peak_2_uncertainty) > freq_high:
        bad_windows = 1
        bad_2 = 1
    if (trans_3_center-peak_3_uncertainty) < freq_low:
        bad_windows = 1
        bad_3 = -1
    if (trans_3_center+peak_3_uncertainty) > freq_high:
        bad_windows = 1
        bad_3 = 1
    return bad_windows,bad_1,bad_2,bad_3

def final_uncerts(trans_1_center,trans_2_center,trans_3_center,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,freq_low,freq_high,A,B,C,DJ,DJK,DK,dJ,dK,temperature,u_A,u_B,u_C,trans_1,trans_2,trans_3):
    
    (bad_windows,bad_1,bad_2,bad_3)=check_bounds(trans_1_center,trans_2_center,trans_3_center,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,freq_low,freq_high)

    while bad_windows ==1:
        while bad_1 == -1:
            peak_1_uncertainty = peak_1_uncertainty*0.95
            (bad_windows,bad_1,bad_2,bad_3)=check_bounds(trans_1_center,trans_2_center,trans_3_center,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,freq_low,freq_high)

        while bad_2 == -1:
            peak_2_uncertainty = peak_2_uncertainty*0.95
            (bad_windows,bad_1,bad_2,bad_3)=check_bounds(trans_1_center,trans_2_center,trans_3_center,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,freq_low,freq_high)

        while bad_3 == -1:
            peak_3_uncertainty = peak_3_uncertainty*0.95
            (bad_windows,bad_1,bad_2,bad_3)=check_bounds(trans_1_center,trans_2_center,trans_3_center,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,freq_low,freq_high)

        while bad_1 == 1:
            peak_1_uncertainty = peak_1_uncertainty*0.95
            (bad_windows,bad_1,bad_2,bad_3)=check_bounds(trans_1_center,trans_2_center,trans_3_center,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,freq_low,freq_high)

        while bad_2 == 1:
            peak_2_uncertainty = peak_2_uncertainty*0.95
            (bad_windows,bad_1,bad_2,bad_3)=check_bounds(trans_1_center,trans_2_center,trans_3_center,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,freq_low,freq_high)

        while bad_3 == 1:
            peak_3_uncertainty = peak_3_uncertainty*0.95
            (bad_windows,bad_1,bad_2,bad_3)=check_bounds(trans_1_center,trans_2_center,trans_3_center,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,freq_low,freq_high)

        if (trans_1 == trans_2) or (trans_2 == trans_3) or (trans_1 == trans_3):
            print('You do not have three distinct transitions.  Quitting.')
            quit()
            
    return trans_1,trans_2,trans_3,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty


def triples_gen(trans_1_uncert,trans_2_uncert,trans_3_uncert,freq_uncertainty,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,peaklist,freq_low,freq_high,A,B,C,DJ,DJK,DK,dJ,dK,temperature,u_A,u_B,u_C,trans_1,trans_2,trans_3):

    trans_1_center = float(trans_1[1])
    trans_2_center = float(trans_2[1])
    trans_3_center = float(trans_3[1])

    trans_1_peaks = []
    trans_2_peaks = []
    trans_3_peaks = []

    peak_1_uncertainty = freq_uncertainty
    peak_2_uncertainty = freq_uncertainty
    peak_3_uncertainty = freq_uncertainty

    while trans_1_peaks == [] or trans_2_peaks == [] or trans_3_peaks == []: #this loops until there are peaks around each member of the triple
        uncertainty_flag =1
        loop_counter = 0

        while uncertainty_flag ==1:            
            if freq_uncertainty==0.0:
                freq_uncertainty = 100.0
                peak_1_uncertainty = freq_uncertainty
                peak_2_uncertainty = freq_uncertainty
                peak_3_uncertainty = freq_uncertainty

            (trans_1,trans_2,trans_3,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty) = final_uncerts(trans_1_center,trans_2_center,trans_3_center,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,freq_low,freq_high,A,B,C,DJ,DJK,DK,dJ,dK,temperature,u_A,u_B,u_C,trans_1,trans_2,trans_3)
            trans_1_center = float(trans_1[1])
            trans_2_center = float(trans_2[1])
            trans_3_center = float(trans_3[1])

            trans_1_peaks = []
            trans_2_peaks = []
            trans_3_peaks = []

            for freq_p, inten_p in peaklist:
                if abs(float(trans_1_center)-float(freq_p))< peak_1_uncertainty:
                    trans_1_peaks.append((freq_p, inten_p))
                if abs(float(trans_2_center)-float(freq_p))< peak_2_uncertainty: #this bit finds peaks in the real spectrum that are near the predicted peaks
                    trans_2_peaks.append((freq_p, inten_p))
                if abs(float(trans_3_center)-float(freq_p))< peak_3_uncertainty:
                    trans_3_peaks.append((freq_p, inten_p))
            num_of_triples = len(trans_1_peaks)*len(trans_2_peaks)*len(trans_3_peaks) #this tells you how many entries there will be in the all_combo_list

            uncertainty_flag = 0
            loop_counter = loop_counter + 1

            if trans_1_peaks == [] or trans_2_peaks == [] or trans_3_peaks == []:
                peak_1_uncertainty = 2*peak_1_uncertainty
                peak_2_uncertainty = 2*peak_2_uncertainty
                peak_3_uncertainty = 2*peak_3_uncertainty
                uncertainty_flag = 1

            if (num_of_triples < 10000) and (loop_counter < 5):
                peak_1_uncertainty = 1.5*peak_1_uncertainty
                peak_2_uncertainty = 1.5*peak_2_uncertainty
                peak_3_uncertainty = 1.5*peak_3_uncertainty
                uncertainty_flag = 1

            if (num_of_triples > 4000000) and (loop_counter < 5): # This is in here for debugging purposes, thought it's not a bad idea to have some automated response if the number of triples gets to be too huge.
                peak_1_uncertainty = 0.8*peak_1_uncertainty
                peak_2_uncertainty = 0.8*peak_2_uncertainty
                peak_3_uncertainty = 0.8*peak_3_uncertainty
                uncertainty_flag = 1


    
    return trans_1,trans_2,trans_3,trans_1_peaks,trans_2_peaks,trans_3_peaks,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,num_of_triples


def gen_file(label,job_name,grid_counter,u_A,u_B,u_C,Jmax,freq_low,freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,full_list,trans_1_uncert,trans_2_uncert,trans_3_uncert,freq_uncertainty,peaklist,num,data_file,processors,inten_low,inten_high):

    (trans_1,trans_2,trans_3) = generate_trans(u_A,u_B,u_C,Jmax,freq_low,freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,full_list,num)
    top_peaks_3cut = generate_check(u_A,u_B,u_C,Jmax,freq_low,freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,trans_1,trans_2,trans_3,num)
    (trans_1,trans_2,trans_3,trans_1_peaks,trans_2_peaks,trans_3_peaks,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,num_of_triples) = triples_gen(trans_1_uncert,trans_2_uncert,trans_3_uncert,freq_uncertainty,0,0,0,peaklist,freq_low,freq_high,A,B,C,DJ,DJK,DK,dJ,dK,temperature,u_A,u_B,u_C,trans_1,trans_2,trans_3)

    job_file = ""
    str(top_peaks_3cut)
    str(trans_1)
    str(trans_2)
    str(trans_3)
    fitting_peaks_str = ""
    for entry in top_peaks_3cut:
        fitting_peaks_str+=str(entry)+"\n"

    suffix = job_name.split("/")[-1]

    #print "The job name near line 1275 is %s, and its suffix is %s"%(job_name,suffix)
    grid_file_name = "%s/%s_%s_g%s"%(job_name,suffix,label,str(grid_counter))

    job_file += "job_name: %s \n data_file: %s \n u_A: %s \n u_B: %s \n u_C: %s \n A: %s \n B: %s \n \
    C: %s \n DJ: %s \n DJK: %s \n DK: %s \n dJ: %s \n dK: %s \n processors: %s \n freq_high: %s \n freq_low: %s \n \
    inten_high: %s \n inten_low: %s \n Temp: %s \n Jmax: %s \n freq_uncertainty: %s \n number of triples: %s \n Check peaks:\n%s \n trans_1: %s \n trans_2: %s \n trans_3: %s "%(grid_file_name,data_file,u_A,u_B,u_C,A,B,C,DJ,DJK,DK,dJ,dK,str(processors),str(freq_high),str(freq_low),str(inten_high),str(inten_low),str(temperature),str(Jmax),str(peak_1_uncertainty),str(num_of_triples),fitting_peaks_str,str(trans_1),str(trans_2),str(trans_3))

    Job_fh = open("%s.txt"%(grid_file_name),"w")
    Job_fh.write(job_file) 
    Job_fh.close()


def grid_point_file_gen(q,obj_list,x,y,num,data_file,processors,inten_low,inten_high,dipole_string):

    sub_list = obj_list[x:y]
    #print num,x,y,len(sub_list)

    if "a" in dipole_string:
        a_flag = True
    else:
        a_flag = False

    if "b" in dipole_string:
        b_flag = True
    else:
        b_flag = False

    if "c" in dipole_string:
        c_flag = True
    else:
        c_flag = False

    a_full_list_length = 0
    b_full_list_length = 0
    c_full_list_length = 0
    ab_full_list_length = 0
    ac_full_list_length = 0
    bc_full_list_length = 0

    for i in range(len(sub_list)):
        (A, B, C, freq_uncertainty, freq_low, freq_high, Jmax, temperature, DJ, DJK, DK, dJ, dK, job_name, peaklist, grid_counter) = sub_list[i]
        #print num,i,grid_counter

        adj_freq_low = freq_low + freq_uncertainty
        adj_freq_high = freq_high - freq_uncertainty

        if a_flag:
            a_u_A = "1.0"
            a_u_B = "0.0"
            a_u_C = "0.0"
            (a_full_list,a_full_list_length) = gen_full_list(a_u_A,a_u_B,a_u_C,Jmax,adj_freq_low,adj_freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,num)

        if b_flag:
            b_u_A = "0.0"
            b_u_B = "1.0"
            b_u_C = "0.0"
            (b_full_list,b_full_list_length) = gen_full_list(b_u_A,b_u_B,b_u_C,Jmax,adj_freq_low,adj_freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,num)

        if c_flag:
            c_u_A = "0.0"
            c_u_B = "0.0"
            c_u_C = "1.0"
            (c_full_list,c_full_list_length) = gen_full_list(c_u_A,c_u_B,c_u_C,Jmax,adj_freq_low,adj_freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,num)

        if a_flag and b_flag:
            ab_u_A = "1.0"
            ab_u_B = "1.0"
            ab_u_C = "0.0"
            (ab_full_list,ab_full_list_length) = gen_full_list(ab_u_A,ab_u_B,ab_u_C,Jmax,adj_freq_low,adj_freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,num)

        if a_flag and c_flag:
            ac_u_A = "1.0"
            ac_u_B = "0.0"
            ac_u_C = "1.0"
            (ac_full_list,ac_full_list_length) = gen_full_list(ac_u_A,ac_u_B,ac_u_C,Jmax,adj_freq_low,adj_freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,num)

        if b_flag and c_flag:
            bc_u_A = "0.0"
            bc_u_B = "1.0"
            bc_u_C = "1.0"
            (bc_full_list,bc_full_list_length) = gen_full_list(bc_u_A,bc_u_B,bc_u_C,Jmax,adj_freq_low,adj_freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,num)

        trans_1_uncert = freq_uncertainty
        trans_2_uncert = freq_uncertainty
        trans_3_uncert = freq_uncertainty

        #print "The job name near line 1360 is %s"%job_name

        if a_full_list_length >= 10:
            label = "a"
            u_A = a_u_A
            u_B = a_u_B
            u_C = a_u_C
            full_list = a_full_list
            gen_file(label,job_name,grid_counter,u_A,u_B,u_C,Jmax,freq_low,freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,full_list,trans_1_uncert,trans_2_uncert,trans_3_uncert,freq_uncertainty,peaklist,num,data_file,processors,inten_low,inten_high)

        if b_full_list_length >= 10:
            label = "b"
            u_A = b_u_A
            u_B = b_u_B
            u_C = b_u_C
            full_list = b_full_list
            gen_file(label,job_name,grid_counter,u_A,u_B,u_C,Jmax,freq_low,freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,full_list,trans_1_uncert,trans_2_uncert,trans_3_uncert,freq_uncertainty,peaklist,num,data_file,processors,inten_low,inten_high)

        if c_full_list_length >= 10:
            label = "c"
            u_A = c_u_A
            u_B = c_u_B
            u_C = c_u_C
            full_list = c_full_list
            gen_file(label,job_name,grid_counter,u_A,u_B,u_C,Jmax,freq_low,freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,full_list,trans_1_uncert,trans_2_uncert,trans_3_uncert,freq_uncertainty,peaklist,num,data_file,processors,inten_low,inten_high)

        if ab_full_list_length >= 10:
            label = "ab"
            u_A = ab_u_A
            u_B = ab_u_B
            u_C = ab_u_C
            full_list = ab_full_list
            gen_file(label,job_name,grid_counter,u_A,u_B,u_C,Jmax,freq_low,freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,full_list,trans_1_uncert,trans_2_uncert,trans_3_uncert,freq_uncertainty,peaklist,num,data_file,processors,inten_low,inten_high)

        if ac_full_list_length >= 10:
            label = "ac"
            u_A = ac_u_A
            u_B = ac_u_B
            u_C = ac_u_C
            full_list = ac_full_list
            gen_file(label,job_name,grid_counter,u_A,u_B,u_C,Jmax,freq_low,freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,full_list,trans_1_uncert,trans_2_uncert,trans_3_uncert,freq_uncertainty,peaklist,num,data_file,processors,inten_low,inten_high)

        if bc_full_list_length >= 10:
            label = "bc"
            u_A = bc_u_A
            u_B = bc_u_B
            u_C = bc_u_C
            full_list = bc_full_list
            gen_file(label,job_name,grid_counter,u_A,u_B,u_C,Jmax,freq_low,freq_high,temperature,A,B,C,DJ,DJK,DK,dJ,dK,full_list,trans_1_uncert,trans_2_uncert,trans_3_uncert,freq_uncertainty,peaklist,num,data_file,processors,inten_low,inten_high)

        frac_output = (float(i+1)/float(len(sub_list)))
        #print grid_counter,(i+1),len(sub_list),frac_output,num

        q.put([grid_counter,frac_output,"Processing",num])
    q.put([grid_counter,frac_output,"Done",num])



if __name__ == '__main__': #multiprocessing imports script as module

    global processors

    processors = psutil.cpu_count(logical = False)

    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog_First_Window()
    ui.setupUi(Dialog)
    Dialog.show()
    
    sys.exit(app.exec_()) # Not convinced yet that I want to exit when the GUI window is closed...
