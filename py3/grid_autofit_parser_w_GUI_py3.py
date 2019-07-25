from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial

import subprocess
import os
import sys
import string
import shutil
import time
import math

""""
Grid Autofit Parser

This script will parse output files on a successful run of grid_autofit, making a summary file from the best results from all of the runs.

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
        self.gridLayout.addWidget(self.file_import_input, 1, 3, 1, 3)
        self.browse_import_button = QtWidgets.QPushButton(Dialog)
        self.browse_import_button.setObjectName("browse_import_button")
        self.browse_import_button.clicked.connect(self.browse)
        self.gridLayout.addWidget(self.browse_import_button, 1, 6, 1, 1)

        self.OMC_label = QtWidgets.QLabel(Dialog)
        self.OMC_label.setObjectName("OMC_label")
        self.gridLayout.addWidget(self.OMC_label, 2, 0, 1, 3)
        self.OMC_input = QtWidgets.QLineEdit(Dialog)
        self.OMC_input.setObjectName("OMC_input")
        self.OMC_input.setToolTip("Results with an OMC (in MHz) less than this will be saved in the summary file.")
        self.gridLayout.addWidget(self.OMC_input, 2, 3, 1, 1)
        self.OMC_input.setText("2.0") # default value

        self.gridLayout.addWidget(QHLine(), 3, 0, 1, 7)

        self.parse_results_button = QtWidgets.QPushButton(Dialog) # Needs to be updated to a "do the thing" for a specific, not FT thing.
        self.parse_results_button.setObjectName("parse_results_button")
        self.parse_results_button.clicked.connect(self.parse_results)
        self.gridLayout.addWidget(self.parse_results_button, 4, 0, 1, 4)
        self.parse_results_button.setEnabled(False)
        self.exit_button = QtWidgets.QPushButton(Dialog)
        self.exit_button.setObjectName("exit_button")
        self.exit_button.clicked.connect(app.quit) # Probably should interrupt if haven't saved yet
        self.gridLayout.addWidget(self.exit_button, 4, 4, 1, 3)

        self.status_window = QtWidgets.QTextEdit(Dialog)
        self.status_window.setObjectName("status_window")
        self.gridLayout.addWidget(self.status_window, 5, 0, 5, 7) # make it big!!!!
        self.status_window.setReadOnly(True)

        self.progress = QtWidgets.QProgressBar(Dialog)
        self.progress.setObjectName("progress")
        self.gridLayout.addWidget(self.progress, 10, 0, 1, 7)
        self.progress.setValue(0)

        self.font_plus_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl++"), self.font_plus_button)
        self.font_plus_button.shortcut.activated.connect(partial(self.font_plus,Dialog))
        self.font_minus_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+-"), self.font_minus_button)
        self.font_minus_button.shortcut.activated.connect(partial(self.font_minus,Dialog))
        self.browse_import_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+D"), self.browse_import_button)
        self.browse_import_button.shortcut.activated.connect(self.browse)
        self.parse_results_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+R"), self.parse_results_button)
        self.parse_results_button.shortcut.activated.connect(self.parse_results)
        self.exit_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self.exit_button)
        self.exit_button.shortcut.activated.connect(app.quit)

        self.font_plus_button.setWhatsThis("Shortcut: Ctrl++")
        self.font_minus_button.setWhatsThis("Shortcut: Ctrl+-")
        self.browse_import_button.setWhatsThis("Shortcut: Ctrl+D")
        self.parse_results_button.setWhatsThis("Shortcut: Ctrl+R")
        self.exit_button.setWhatsThis("Shortcut: Ctrl+Q")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Grid Autofit Results Parser"))
        self.font_plus_button.setText(_translate("Dialog", "Increase Font"))
        self.font_minus_button.setText(_translate("Dialog", "Decrease Font"))
        self.file_import_label.setText(_translate("Dialog", "Directory containing completed jobs"))
        self.browse_import_button.setText(_translate("Dialog", "Select Directory"))
        self.OMC_label.setText(_translate("Dialog", "OMC (MHz) of worst result to keep"))
        self.parse_results_button.setText(_translate("Dialog", "Summarize Results!"))
        self.exit_button.setText(_translate("Dialog", "Exit"))

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

    def browse(self): # Fix me
        dirName = QtWidgets.QFileDialog.getExistingDirectory()
        if dirName:
            self.file_import_input.setText(dirName)
            self.parse_results_button.setEnabled(True)

    def raise_error(self):
        self.error_dialog = QtWidgets.QMessageBox()
        self.error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        self.error_dialog.setWindowTitle("Something's Wrong!")
        self.error_dialog.setText(self.error_message)
        self.error_dialog.show()

    def parse_results(self): # should actually do a thing later

        try:
            OMC_thresh = float(self.OMC_input.text())
        except:
            self.error_message = "The OMC threshold should be a number!"
            self.raise_error()
            self.OMC_input.setFocus()
            return 0

        job_name = self.file_import_input.text()

        if job_name == "":
            self.error_message = "Please select a directory containing results and try again."
            self.raise_error()
            self.browse_import_button.setFocus()
            return 0

        suffix = job_name.split("/")[-1]

        os.chdir(job_name)

        x = subprocess.Popen("dir /b | findstr %s"%suffix, stdout=subprocess.PIPE, shell=True, encoding='utf-8')
        x = x.stdout.read().split()
        # x is the list of everything in the directory containing the suffix, this will be both input files and directories.

        self.status_window.append("Starting to parse grid autofit output results!")


        # send things off to a worker thread
        thread = self.thread = QtCore.QThread()
        worker = self.worker = Worker(x,suffix,OMC_thresh) # will want to give it whatever arguments it needs
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self.progress_update)
        worker.status.connect(self.status_update)
        worker.done.connect(self.exit_update)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        worker.finished.connect(thread.quit)
        thread.start()

    def progress_update(self,value):
        self.progress.setValue(value)

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
    def __init__(self, list_of_jobs, suffix, OMC_thresh, *args, **kwargs):
        QtCore.QObject.__init__(self, *args, **kwargs)
        self.percentage = 0
        self.list_of_jobs = list_of_jobs
        self.suffix = suffix
        self.OMC_thresh = OMC_thresh

    def run(self): # should actually do a thing instead of just saying it does
        best_results = ''

        jobs_done = 0
        start_time = time.time()
        total_num_jobs = 0
        jobs_with_interesting_output = 0

        for entry in self.list_of_jobs:
            if os.path.isdir(entry):
                total_num_jobs += 1

        for entry in self.list_of_jobs:
            if os.path.isdir(entry):
                os.chdir(entry)

                (flag,more_results) = parse_best100(entry,self.OMC_thresh)
                if flag == 1:
                    jobs_with_interesting_output += 1
                    best_results += more_results

                os.chdir(os.pardir)
                jobs_done += 1
                percentage = int(math.floor(100.0*(float((jobs_done)/float(total_num_jobs)))))
                self.calculate_progress(percentage)
                current_time = time.time()
                elapsed_time = current_time - start_time
                if percentage >= 1: # fix divide by zero issue if too many jobs (making percentage = 0 because of int(math.floor))
                    remaining_time = (elapsed_time*100/percentage) - elapsed_time
                    temp_string = "%s percent complete by file number! Taken %s seconds so far, about %s seconds remaining."%(percentage,int(math.ceil(elapsed_time)),int(math.ceil(remaining_time)))
                    self.status.emit(temp_string)

        temp_string = "Of the %s jobs, %s of them had output with results of OMC < %s MHz that will be written to file."%(total_num_jobs,jobs_with_interesting_output,self.OMC_thresh)
        self.status.emit(temp_string)

        if best_results == '':
            best_results = "Sadly, none of the jobs had results with OMC < %s MHz."%(self.OMC_thresh)

        f_summary = open('%s_summary.txt'%(self.suffix),'w')
        f_summary.write(best_results)
        f_summary.close()

        self.done.emit(True)
        self.finished.emit(True)

    def calculate_progress(self,percentage_new):

        if percentage_new > self.percentage:
            self.percentage = percentage_new
            self.progress.emit(self.percentage)

    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(bool)
    done = QtCore.pyqtSignal(bool)
    status = QtCore.pyqtSignal(str)


def parse_best100(dir_name,OMC_thresh):
    flag = 0
    new_results = ''

    try:
        f = open('best100.txt')
    except:
        return flag, new_results

    for line in f:
        temp_line = line.split()
        if temp_line != []:
            score = temp_line[2]
            A = temp_line[5]
            B = temp_line[8]
            C = temp_line[11]
            omc = temp_line[20]

            if float(omc) <= OMC_thresh:
                flag = 1
                result = str(dir_name) + ' ' + str(score) + ' ' + str(omc) + ' ' + str(A) + ' ' + str(B) + ' ' + str(C) + '\n'
                new_results += result

    return flag, new_results

if __name__ == '__main__': #multiprocessing imports script as module
    
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog_First_Window()
    ui.setupUi(Dialog)
    Dialog.show()
    
    sys.exit(app.exec_()) # Not convinced yet that I want to exit when the GUI window is closed...
