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
        self.font_plus_button = QtWidgets.QPushButton(Dialog)
        self.font_plus_button.setObjectName = "font_plus_button"
        self.font_plus_button.clicked.connect(partial(self.font_plus,Dialog))
        self.gridLayout.addWidget(self.font_plus_button, 0, 0, 1, 1)
        self.font_minus_button = QtWidgets.QPushButton(Dialog)
        self.font_minus_button.setObjectName = "font_minus_button"
        self.font_minus_button.clicked.connect(partial(self.font_minus,Dialog))
        self.gridLayout.addWidget(self.font_minus_button, 0, 1, 1, 1)

        self.parse_results_button = QtWidgets.QPushButton(Dialog) # Needs to be updated to a "do the thing" for a specific, not FT thing.
        self.parse_results_button.setObjectName("parse_results_button")
        self.parse_results_button.clicked.connect(self.parse_results)
        self.gridLayout.addWidget(self.parse_results_button, 2, 0, 1, 4)
        self.parse_results_button.setEnabled(False)
        self.exit_button = QtWidgets.QPushButton(Dialog)
        self.exit_button.setObjectName("exit_button")
        self.exit_button.clicked.connect(app.quit) # Probably should interrupt if haven't saved yet
        self.gridLayout.addWidget(self.exit_button, 2, 4, 1, 3)

        self.status_window = QtWidgets.QTextEdit(Dialog)
        self.status_window.setObjectName("status_window")
        self.gridLayout.addWidget(self.status_window, 3, 0, 5, 7) # make it big!!!!
        self.status_window.setReadOnly(True)

        self.progress = QtWidgets.QProgressBar(Dialog)
        self.progress.setObjectName("progress")
        self.gridLayout.addWidget(self.progress, 9, 0, 1, 7)
        self.progress.setValue(0)

        self.font_plus_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl++"), self.font_plus_button)
        self.font_plus_button.shortcut.activated.connect(partial(self.font_plus,Dialog))
        self.font_minus_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+-"), self.font_minus_button)
        self.font_minus_button.shortcut.activated.connect(partial(self.font_minus,Dialog))
        self.browse_import_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+O"), self.browse_import_button)
        self.browse_import_button.shortcut.activated.connect(self.browse)
        self.parse_results_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+R"), self.parse_results_button)
        self.parse_results_button.shortcut.activated.connect(self.parse_results)
        self.exit_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self.exit_button)
        self.exit_button.shortcut.activated.connect(app.quit)

        self.font_plus_button.setWhatsThis("Shortcut: Ctrl++")
        self.font_minus_button.setWhatsThis("Shortcut: Ctrl+-")
        self.browse_import_button.setWhatsThis("Shortcut: Ctrl+O")
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

    def parse_results(self): # should actually do a thing later
        job_name = self.file_import_input.text()
        suffix = job_name.split("/")[-1]

        os.chdir(job_name)

        x = subprocess.Popen("dir /b | findstr %s"%suffix, stdout=subprocess.PIPE, shell=True)
        x = x.stdout.read().split()
        # x is the list of everything in the directory containing the suffix, this will be both input files and directories.

        self.status_window.append("Starting to parse grid autofit output results!")


        # send things off to a worker thread
        thread = self.thread = QtCore.QThread()
        worker = self.worker = Worker(x,suffix) # will want to give it whatever arguments it needs
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

class Worker(QtCore.QObject): # looks like we need to use threading in order to get progress bars to update!
# Thanks go to this thread: https://gis.stackexchange.com/questions/64831/how-do-i-prevent-qgis-from-being-detected-as-not-responding-when-running-a-hea
    def __init__(self, list_of_jobs, suffix, *args, **kwargs):
        QtCore.QObject.__init__(self, *args, **kwargs)
        self.percentage = 0
        self.list_of_jobs = list_of_jobs
        self.suffix = suffix

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

                (flag,more_results) = parse_best100(entry)
                if flag == 1:
                    jobs_with_interesting_output += 1
                    best_results += more_results

                os.chdir(os.pardir)
                jobs_done += 1
                percentage = int(math.floor(100.0*(float((jobs_done)/float(total_num_jobs)))))
                self.calculate_progress(percentage)
                current_time = time.time()
                elapsed_time = current_time - start_time
                remaining_time = (elapsed_time*100/percentage) - elapsed_time
                temp_string = "%s percent complete by file number! Taken %s seconds so far, about %s seconds remaining."%(percentage,int(math.ceil(elapsed_time)),int(math.ceil(remaining_time)))
                self.status.emit(temp_string)

        temp_string = "Of the %s jobs, %s of them had output with results of OMC < 2.0 MHz that will be written to file."%(total_num_jobs,jobs_with_interesting_output)
        self.status.emit(temp_string)

        if best_results == '':
            best_results = "Sadly, none of the jobs had results with OMC < 2.0 MHz."

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


def parse_best100(dir_name):
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

            if float(omc) <= 2.0:
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
