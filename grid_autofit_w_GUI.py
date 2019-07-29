from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial

import subprocess
import os
import psutil
import sys
import string
import shutil
import autofit_cluster_v3w_GUI
import numpy
import copy
from scipy.interpolate import *
import math
import time

""""
Grid Autofit

This script will run autofit repeatedly on all appropriate input files within a given directory.

"""

class Ui_Dialog_First_Window(object):
    def setupUi(self, Dialog):

        Dialog.setObjectName("Dialog")
        Dialog.resize(275, 145)

        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.font_plus_button = QtWidgets.QPushButton(Dialog)
        self.font_plus_button.setObjectName = "font_plus_button"
        self.font_plus_button.clicked.connect(partial(self.font_plus,Dialog))
        self.gridLayout.addWidget(self.font_plus_button, 0, 0, 1, 1)
        self.font_minus_button = QtWidgets.QPushButton(Dialog)
        self.font_minus_button.setObjectName = "font_minus_button"
        self.font_minus_button.clicked.connect(partial(self.font_minus,Dialog))
        self.gridLayout.addWidget(self.font_minus_button, 0, 1, 1, 1)

        self.file_import_label = QtWidgets.QLabel(Dialog)
        self.file_import_label.setObjectName("file_import_label")
        self.gridLayout.addWidget(self.file_import_label, 1, 0, 1, 3)
        self.file_import_input = QtWidgets.QLineEdit(Dialog)
        self.file_import_input.setObjectName("file_import_input")
        self.file_import_input.setToolTip("The directory containing input files for grid Autofit.")
        self.gridLayout.addWidget(self.file_import_input, 1, 3, 1, 4)
        self.browse_import_button = QtWidgets.QPushButton(Dialog)
        self.browse_import_button.setObjectName("browse_import_button")
        self.browse_import_button.clicked.connect(self.browse)
        self.gridLayout.addWidget(self.browse_import_button, 1, 7, 1, 1)

        self.gridLayout.addWidget(QHLine(), 2, 0, 1, 8)

        self.addl_options_label = QtWidgets.QLabel(Dialog)
        self.addl_options_label.setObjectName("addl_options_label")
        self.gridLayout.addWidget(self.addl_options_label, 3, 0, 1, 3)

        self.change_procs_cb = QtWidgets.QCheckBox(Dialog)
        self.change_procs_cb.setObjectName("change_procs_cb")
        self.change_procs_cb.setText("Change # of Processors?")
        self.change_procs_cb.setToolTip("If checked, you can change the number of processors to use from the value that was previously set.")
        self.change_procs_cb.setChecked(False) # Leave unchecked by default.
        self.change_procs_cb.stateChanged.connect(self.change_procs_display)
        self.gridLayout.addWidget(self.change_procs_cb, 4, 0, 1, 3)

        self.num_procs_label = QtWidgets.QLabel(Dialog)
        self.num_procs_label.setObjectName("num_procs_label")
        self.gridLayout.addWidget(self.num_procs_label, 4, 3, 1, 2)
        self.num_procs_input = QtWidgets.QLineEdit(Dialog)
        self.num_procs_input.setObjectName("num_procs_input")
        self.num_procs_input.setToolTip("The number of processors to use.")
        self.gridLayout.addWidget(self.num_procs_input, 4, 5, 1, 1)
        self.num_procs_input.hide()
        self.num_procs_label.hide()

        self.choose_files_cb = QtWidgets.QCheckBox(Dialog)
        self.choose_files_cb.setObjectName("choose_files_cb")
        self.choose_files_cb.setText("Choose specific files (instead of a full directory)?")
        self.choose_files_cb.setToolTip("If checked, you can choose specific files to run Autofit on instead of a full directory.")
        self.choose_files_cb.setChecked(False) # Leave unchecked by default
        self.choose_files_cb.stateChanged.connect(self.choose_files_display)
        self.gridLayout.addWidget(self.choose_files_cb, 5, 0, 1, 3)

        self.select_import_input = QtWidgets.QLineEdit(Dialog)
        self.select_import_input.setObjectName("select_import_input")
        self.select_import_input.setToolTip("Selected files for grid Autofit.")
        self.gridLayout.addWidget(self.select_import_input, 5, 3, 1, 3)
        self.browse_select_import_button = QtWidgets.QPushButton(Dialog)
        self.browse_select_import_button.setObjectName("browse_select_import_button")
        self.browse_select_import_button.clicked.connect(self.browse_select)
        self.gridLayout.addWidget(self.browse_select_import_button, 5, 6, 1, 1)
        self.select_import_input.hide()
        self.browse_select_import_button.hide()

        self.select_peaklist_input = QtWidgets.QLineEdit(Dialog)
        self.select_peaklist_input.setObjectName("select_peaklist_input")
        self.select_peaklist_input.setToolTip("Selected peaklist file for grid Autofit.")
        self.gridLayout.addWidget(self.select_peaklist_input, 6, 3, 1, 3)
        self.browse_peaklist_button = QtWidgets.QPushButton(Dialog)
        self.browse_peaklist_button.setObjectName("browse_peaklist_button")
        self.browse_peaklist_button.clicked.connect(self.browse_peaklist)
        self.gridLayout.addWidget(self.browse_peaklist_button, 6, 6, 1, 1)
        self.select_peaklist_input.hide()
        self.browse_peaklist_button.hide()

        self.gridLayout.addWidget(QHLine(), 7, 0, 1, 8)

        self.run_autofit_button = QtWidgets.QPushButton(Dialog) # Needs to be updated to a "do the thing" for a specific, not FT thing.
        self.run_autofit_button.setObjectName("run_autofit_button")
        self.run_autofit_button.clicked.connect(self.run_autofit)
        self.gridLayout.addWidget(self.run_autofit_button, 8, 0, 1, 4)
        self.run_autofit_button.setEnabled(False)
        self.exit_button = QtWidgets.QPushButton(Dialog)
        self.exit_button.setObjectName("exit_button")
        self.exit_button.clicked.connect(app.quit) # Probably should interrupt if haven't saved yet
        self.gridLayout.addWidget(self.exit_button, 8, 4, 1, 3)

        self.gridLayout.addWidget(QHLine(), 9, 0, 1, 8)

        self.status_window = QtWidgets.QTextEdit(Dialog)
        self.status_window.setObjectName("status_window")
        self.gridLayout.addWidget(self.status_window, 10, 0, 5, 8) # make it big!!!!
        self.status_window.setReadOnly(True)

        self.sub_progress_label = QtWidgets.QLabel(Dialog)
        self.sub_progress_label.setObjectName("sub_progress_label")
        self.gridLayout.addWidget(self.sub_progress_label, 15, 0, 1, 1)
        self.sub_progress = QtWidgets.QProgressBar(Dialog)
        self.sub_progress.setObjectName("sub_progress")
        self.gridLayout.addWidget(self.sub_progress, 15, 1, 1, 7)
        self.sub_progress.setValue(0)

        self.progress_label = QtWidgets.QLabel(Dialog)
        self.progress_label.setObjectName("progress_label")
        self.gridLayout.addWidget(self.progress_label, 16, 0, 1, 1)
        self.progress = QtWidgets.QProgressBar(Dialog)
        self.progress.setObjectName("progress")
        self.gridLayout.addWidget(self.progress, 16, 1, 1, 7)
        self.progress.setValue(0)

        self.font_plus_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl++"), self.font_plus_button)
        self.font_plus_button.shortcut.activated.connect(partial(self.font_plus,Dialog))
        self.font_minus_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+-"), self.font_minus_button)
        self.font_minus_button.shortcut.activated.connect(partial(self.font_minus,Dialog))
        self.browse_import_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+D"), self.browse_import_button)
        self.browse_import_button.shortcut.activated.connect(self.browse)
        self.run_autofit_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+R"), self.run_autofit_button)
        self.run_autofit_button.shortcut.activated.connect(self.run_autofit)
        self.exit_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self.exit_button)
        self.exit_button.shortcut.activated.connect(app.quit)

        self.font_plus_button.setWhatsThis("Shortcut: Ctrl++")
        self.font_minus_button.setWhatsThis("Shortcut: Ctrl+-")
        self.browse_import_button.setWhatsThis("Shortcut: Ctrl+D")
        self.run_autofit_button.setWhatsThis("Shortcut: Ctrl+R")
        self.exit_button.setWhatsThis("Shortcut: Ctrl+Q")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Grid Autofit"))
        self.font_plus_button.setText(_translate("Dialog", "Increase Font"))
        self.font_minus_button.setText(_translate("Dialog", "Decrease Font"))
        self.file_import_label.setText(_translate("Dialog", "Directory with files to be run"))
        self.browse_import_button.setText(_translate("Dialog", "Select Directory"))
        self.addl_options_label.setText(_translate("Dialog", "Additional Options"))
        self.num_procs_label.setText(_translate("Dialog", "# of Processors"))
        self.browse_select_import_button.setText(_translate("Dialog", "Select Files"))
        self.browse_peaklist_button.setText(_translate("Dialog", "Select Peaklist"))
        self.run_autofit_button.setText(_translate("Dialog", "Run Autofit!"))
        self.exit_button.setText(_translate("Dialog", "Exit"))
        self.sub_progress_label.setText(_translate("Dialog", "Job Progress"))
        self.progress_label.setText(_translate("Dialog", "Total Progress"))

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

    def change_procs_display(self):
        change_procs = self.change_procs_cb.isChecked()

        if change_procs:
            self.num_procs_input.show()
            self.num_procs_label.show()
        else:
            self.num_procs_input.hide()
            self.num_procs_label.hide()

    def choose_files_display(self):
        choose_files = self.choose_files_cb.isChecked()

        if choose_files:
            self.select_import_input.show()
            self.browse_select_import_button.show()
            self.select_peaklist_input.show()
            self.browse_peaklist_button.show()
            self.file_import_input.setEnabled(False)
            self.browse_import_button.setEnabled(False)
        else:
            self.select_import_input.hide()
            self.browse_select_import_button.hide()
            self.select_peaklist_input.hide()
            self.browse_peaklist_button.hide()
            self.file_import_input.setEnabled(True)
            self.browse_import_button.setEnabled(True)

    def browse(self): # Fix me
        dirName = QtWidgets.QFileDialog.getExistingDirectory()
        if dirName:
            self.file_import_input.setText(dirName)
            self.are_we_there_yet()

    def browse_select(self): # Fix me to choose multiple
        fileNames, _ = QtWidgets.QFileDialog.getOpenFileNames()
        if fileNames:
            self.filelist = fileNames
            temp_str = ""
            for entry in fileNames:
                temp_str = temp_str + "\"%s\" "%entry
            self.select_import_input.setText(temp_str)
            self.are_we_there_yet()

    def browse_peaklist(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Location of Peaklist file", "", "peaklist (peaklist.txt)")
        if fileName:
            self.select_peaklist_input.setText(fileName)
            self.are_we_there_yet() # Need to build in these hooks also

    def are_we_there_yet(self):

        if self.file_import_input.text() != '':
            have_file_dir = True
        else:
            have_file_dir = False

        if self.select_import_input.text() != '':
            have_selected_files = True
        else:
            have_selected_files = False

        if self.change_procs_cb.isChecked():
            if self.num_procs_input.text() == "":
                self.num_procs_input.setFocus()
                self.run_autofit_button.setEnabled(False)
                return False

        if (have_file_dir == False) and (have_selected_files == False):
            if choose_files_cb.isChecked():
                self.browse_select_import_button.setFocus()
                self.run_autofit_button.setEnabled(False)
                return False
            else:
                self.browse_import_button.setFocus()
                self.run_autofit_button.setEnabled(False)
                return False
        else: # we have a directory with files to be run or a set of selected files
            if have_selected_files == True:
                if self.select_peaklist_input.text() == "":
                    self.browse_peaklist_button.setFocus()
                    self.run_autofit_button.setEnabled(False)
                    return False

            self.run_autofit_button.setEnabled(True)
            self.run_autofit_button.setFocus()
            return True        

    def raise_error(self):
        self.are_we_there_yet()
        self.error_dialog = QtWidgets.QMessageBox()
        self.error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        self.error_dialog.setWindowTitle("Something's Wrong!")
        self.error_dialog.setText(self.error_message)
        self.error_dialog.show()

    def run_autofit(self): # It should do a thing...

        job_name = self.file_import_input.text()

        if self.change_procs_cb.isChecked():
            num_procs = self.num_procs_input.text()
            if num_procs == "":
                self.error_message = "The number of processors to be used needs to be specified!"
                self.raise_error()
                self.num_procs_input.setFocus()
                self.run_autofit_button.setEnabled(False)
                return 0

            try: 
                num_procs = int(num_procs)
            except:
                self.error_message = "The number of processors should be an integer!"
                self.raise_error()
                self.num_procs_input.setFocus()
                self.run_autofit_button.setEnabled(False)
                return 0

            total_processors = psutil.cpu_count(logical = False)

            if num_procs > total_processors:
                self.error_message = "The number of processors you've set is greater than the number of physical cores on your machine. This will lead to significant performance degradation; please reduce the number of processors."
                self.raise_error()
                self.num_procs_input.setFocus()
                return 0


        else:
            num_procs = 0 # A thing we'll check for later in the worker thread to decide what to do. This value says to use whatever's in the input file.

        if self.choose_files_cb.isChecked():
            if self.select_import_input.text() == "":
                self.error_message = "Files to run Autofit on need to be selected or the checkbox for using specific files should be unchecked!"
                self.raise_error()
                self.browse_select_import_button.setFocus()
                self.run_autofit_button.setEnabled(False)
                return 0

            x = self.filelist # I *think* this will work, but we may need to do some additional parsing on the file list.

            if self.select_peaklist_input.text() == "":
                self.error_message = "Please select a peaklist file to proceed."
                self.raise_error()
                self.browse_peaklist_button.setFocus()
                self.run_autofit_button.setEnabled(False)
                return 0

            peaklist_location = self.select_peaklist_input.text()

        else: # Using a directory instead of a list of files
            if job_name == "":
                self.error_message = "A directory containing input files needs to be selected!"
                self.raise_error()
                self.file_import_input.setFocus()
                self.run_autofit_button.setEnabled(False)
                return 0

            peaklist_location = "" # Using as a flag later.

            os.chdir(job_name)
            suffix = job_name.split("/")[-1]

            x = subprocess.Popen("dir /b %s*.txt"%suffix, stdout=subprocess.PIPE, shell=True)
            x = x.stdout.read().split()

        # x contains the full list of files that we'll run Autofit on. Before doing that we should spline and peakpick and save in global variables so we're only doing it *once*.

        # worker/threading stuff starts here
        thread = self.thread = QtCore.QThread()
        worker = self.worker = Worker(x,num_procs,peaklist_location) # will want to give it whatever arguments it needs
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.subprogress.connect(self.subprogress_update)
        worker.reset_subprogress.connect(self.reset_job_bar)
        worker.progress.connect(self.progress_update)
        worker.status.connect(self.status_update)
        worker.done.connect(self.exit_update)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        worker.finished.connect(thread.quit)
        thread.start()

    def progress_update(self,value):
        self.progress.setValue(value)

    def subprogress_update(self,value):
        self.sub_progress.setValue(value)

    def reset_job_bar(self,value):
        if value:
            self.sub_progress.setValue(0)

    def status_update(self,value):
        self.status_window.append(value) # Force this update!

    def exit_update(self,value):
        if value:
            self.status_window.append("Complete!")
            self.exit_button.setFocus()

class QHLine(QtWidgets.QFrame): # Using this: https://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)

class Worker(QtCore.QObject): # looks like we need to use threading in order to get progress bars to update!
# Thanks go to this thread: https://gis.stackexchange.com/questions/64831/how-do-i-prevent-qgis-from-being-detected-as-not-responding-when-running-a-hea
    def __init__(self, list_of_files, number_of_processors, peaklist_location, *args, **kwargs):
        QtCore.QObject.__init__(self, *args, **kwargs)
        self.percentage = 0
        self.sub_percentage = 0
        self.list_of_files = list_of_files
        self.num_procs = number_of_processors
        self.peaklist_location = peaklist_location

    def run(self): # should actually do a thing
        global peaklist

        list_of_files = self.list_of_files
        num_procs = self.num_procs
        peaklist_location = self.peaklist_location

        total_num_files = len(list_of_files)

        if peaklist_location == '': # This means everything's all in the same directory, and we're already in it
            peaklist_input = open("peaklist.txt")
        else:
            peaklist_input = open("%s"%peaklist_location)

        row_counter = 0
        for line in peaklist_input:
            temp_str = line.strip()
            if temp_str.split(", ") != []:
                row_counter += 1

        peaklist_input.close()

        temp_peaklist = numpy.zeros((row_counter,2))

        if peaklist_location == '':
            peaklist_input = open("peaklist.txt")
        else:
            peaklist_input = open("%s"%peaklist_location)

        temp_counter = 0
        for line in peaklist_input:
            temp_str = line.strip()
            if temp_str.split(", ") != []:
                temp_x = temp_str.split(", ")[0]
                temp_y = temp_str.split(", ")[1]
                temp_peaklist[temp_counter,0] = temp_x
                temp_peaklist[temp_counter,1] = temp_y
                temp_counter += 1

        peaklist_input.close()

        peaklist = temp_peaklist

        self.status.emit("Finished reading peaks from the peaklist file!")

        progress_counter = 0

        start_time = time.time()

        # More stuff gets done here
        for input_file in list_of_files:
            if progress_counter == 0:
                temp_string = "Starting calculations on first file; this may take a while. A time estimate will be available once the first job finishes."
                self.status.emit(temp_string)
                temp_string = "Note: time estimates will be less reliable until several jobs complete since jobs can be of very different sizes."
                self.status.emit(temp_string)
            self.sub_percentage = 0
            autofit_cluster_v3w_GUI.triples_calc(self,input_file,peaklist,num_procs)
            progress_counter += 1
            percentage = int(math.floor(100.0*(float((progress_counter)/float(total_num_files)))))
            self.calculate_progress(percentage)
            current_time = time.time()
            elapsed_time = current_time - start_time
            remaining_time = (elapsed_time*100/percentage) - elapsed_time
            elapsed_time_string = time_formatting(elapsed_time)
            remaining_time_string = time_formatting(remaining_time)
            temp_string = "%s percent complete by file number! Taken %s so far, about %s remaining."%(percentage,elapsed_time_string,remaining_time_string)
            self.status.emit(temp_string)
            self.reset_subprogress_bar()

        self.done.emit(True)
        self.finished.emit(True)

    def calculate_progress(self,percentage_new):

        if percentage_new > self.percentage:
            self.percentage = percentage_new
            self.progress.emit(self.percentage)

    def calculate_subprogress(self,percentage_new):

        if percentage_new > self.sub_percentage:
            self.sub_percentage = percentage_new
            self.subprogress.emit(self.sub_percentage)

    def reset_subprogress_bar(self):
        self.reset_subprogress.emit(True)

    progress = QtCore.pyqtSignal(int)
    subprogress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(bool)
    done = QtCore.pyqtSignal(bool)
    reset_subprogress = QtCore.pyqtSignal(bool)
    status = QtCore.pyqtSignal(str)


def time_formatting(time_in_seconds):
    if time_in_seconds <= 60:
        time_string = "%s seconds"%int(math.ceil(time_in_seconds))
        return time_string

    if time_in_seconds > 60 and time_in_seconds <= 3600:
        num_minutes = float(time_in_seconds)/60.0
        time_string = "%s minutes"%int(math.ceil(num_minutes))
        return time_string

    if time_in_seconds > 3600:
        num_hours = int(math.floor(float(time_in_seconds)/3600.0))
        temp_num_seconds = time_in_seconds % 3600
        temp_string = time_formatting(temp_num_seconds)
        time_string = "%s hours, %s"%(num_hours,temp_string)
        return time_string

if __name__ == '__main__': #multiprocessing imports script as module
    global xdata
    global ydata

    xdata = []
    ydata = []

    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog_First_Window()
    ui.setupUi(Dialog)
    Dialog.show()
    
    sys.exit(app.exec_()) # Not convinced yet that I want to exit when the GUI window is closed...
