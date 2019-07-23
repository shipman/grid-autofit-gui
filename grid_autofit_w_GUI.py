from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial

import subprocess
import os
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
        self.data_import_label = QtWidgets.QLabel(Dialog)
        self.data_import_label.setObjectName("data_import_label")
        self.gridLayout.addWidget(self.data_import_label, 1, 0, 1, 1)
        self.data_import_input = QtWidgets.QLineEdit(Dialog)
        self.data_import_input.setObjectName("data_import_input")
        self.data_import_input.setToolTip("The data file of the experimental spectrum.")
        self.gridLayout.addWidget(self.data_import_input, 1, 1, 1, 3)
        self.browse_data_button = QtWidgets.QPushButton(Dialog)
        self.browse_data_button.setObjectName("browse_data_button")
        self.browse_data_button.clicked.connect(self.browse_data)
        self.gridLayout.addWidget(self.browse_data_button, 1, 4, 1, 1)
        self.load_button = QtWidgets.QPushButton(Dialog)
        self.load_button.setObjectName("load_button")
        self.load_button.clicked.connect(self.load_data)
        self.gridLayout.addWidget(self.load_button, 1, 5, 1, 1)
        self.load_button.setEnabled(False)

        self.file_import_label = QtWidgets.QLabel(Dialog)
        self.file_import_label.setObjectName("file_import_label")
        self.gridLayout.addWidget(self.file_import_label, 2, 0, 1, 3)
        self.file_import_input = QtWidgets.QLineEdit(Dialog)
        self.file_import_input.setObjectName("file_import_input")
        self.file_import_input.setToolTip("The directory containing input files for grid Autofit.")
        self.gridLayout.addWidget(self.file_import_input, 2, 3, 1, 3)
        self.browse_import_button = QtWidgets.QPushButton(Dialog)
        self.browse_import_button.setObjectName("browse_import_button")
        self.browse_import_button.clicked.connect(self.browse)
        self.gridLayout.addWidget(self.browse_import_button, 2, 6, 1, 1)
        self.font_plus_button = QtWidgets.QPushButton(Dialog)
        self.font_plus_button.setObjectName = "font_plus_button"
        self.font_plus_button.clicked.connect(partial(self.font_plus,Dialog))
        self.gridLayout.addWidget(self.font_plus_button, 0, 0, 1, 1)
        self.font_minus_button = QtWidgets.QPushButton(Dialog)
        self.font_minus_button.setObjectName = "font_minus_button"
        self.font_minus_button.clicked.connect(partial(self.font_minus,Dialog))
        self.gridLayout.addWidget(self.font_minus_button, 0, 1, 1, 1)

        self.run_autofit_button = QtWidgets.QPushButton(Dialog) # Needs to be updated to a "do the thing" for a specific, not FT thing.
        self.run_autofit_button.setObjectName("run_autofit_button")
        self.run_autofit_button.clicked.connect(self.run_autofit)
        self.gridLayout.addWidget(self.run_autofit_button, 3, 0, 1, 4)
        self.run_autofit_button.setEnabled(False)
        self.exit_button = QtWidgets.QPushButton(Dialog)
        self.exit_button.setObjectName("exit_button")
        self.exit_button.clicked.connect(app.quit) # Probably should interrupt if haven't saved yet
        self.gridLayout.addWidget(self.exit_button, 3, 4, 1, 3)

        self.status_window = QtWidgets.QTextEdit(Dialog)
        self.status_window.setObjectName("status_window")
        self.gridLayout.addWidget(self.status_window, 4, 0, 5, 7) # make it big!!!!
        self.status_window.setReadOnly(True)

        self.progress = QtWidgets.QProgressBar(Dialog)
        self.progress.setObjectName("progress")
        self.gridLayout.addWidget(self.progress, 9, 0, 1, 7)
        self.progress.setValue(0)

        self.font_plus_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl++"), self.font_plus_button)
        self.font_plus_button.shortcut.activated.connect(partial(self.font_plus,Dialog))
        self.font_minus_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+-"), self.font_minus_button)
        self.font_minus_button.shortcut.activated.connect(partial(self.font_minus,Dialog))
        self.browse_data_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+D"), self.browse_data_button)
        self.browse_data_button.shortcut.activated.connect(self.browse_data)
        self.browse_import_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+O"), self.browse_import_button)
        self.browse_import_button.shortcut.activated.connect(self.browse)
        self.load_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+L"), self.load_button)
        self.load_button.shortcut.activated.connect(self.load_data)
        self.run_autofit_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+R"), self.run_autofit_button)
        self.run_autofit_button.shortcut.activated.connect(self.run_autofit)
        self.exit_button.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self.exit_button)
        self.exit_button.shortcut.activated.connect(app.quit)

        self.font_plus_button.setWhatsThis("Shortcut: Ctrl++")
        self.font_minus_button.setWhatsThis("Shortcut: Ctrl+-")
        self.browse_data_button.setWhatsThis("Shortcut: Ctrl+D")
        self.browse_import_button.setWhatsThis("Shortcut: Ctrl+O")
        self.load_button.setWhatsThis("Shortcut: Ctrl+L")
        self.run_autofit_button.setWhatsThis("Shortcut: Ctrl+R")
        self.exit_button.setWhatsThis("Shortcut: Ctrl+Q")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Grid Autofit"))
        self.data_import_label.setText(_translate("Dialog", "Spectrum File"))
        self.browse_data_button.setText(_translate("Dialog", "Select Data"))
        self.load_button.setText(_translate("Dialog", "Load Data"))
        self.font_plus_button.setText(_translate("Dialog", "Increase Font"))
        self.font_minus_button.setText(_translate("Dialog", "Decrease Font"))
        self.file_import_label.setText(_translate("Dialog", "Directory with files to be run"))
        self.browse_import_button.setText(_translate("Dialog", "Select Directory"))
        self.run_autofit_button.setText(_translate("Dialog", "Run Autofit!"))
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
            self.are_we_there_yet()

    def browse_data(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName()
        if fileName:
            self.data_import_input.setText(fileName)
            self.load_button.setEnabled(True)
            self.load_button.setFocus()
            self.are_we_there_yet()

    def load_data(self):
        global xdata
        global ydata
        global low_intensity
        global high_intensity

        data_file = self.data_import_input.text()

        self.status_window.append("Loading data file! (This may take 20-30 seconds.)") # Force this update!
        QtWidgets.QApplication.processEvents()
        # Would be nice to add some status indicator since this can take a long time.

        # Spectra-containing files are big - need to spin this off to a separate thread so it doesn't freeze app.

        try:
            fh = numpy.loadtxt(data_file,delimiter=',') #loads full experimental data file, not just list of peaks. Should be in directory this script is run from (same as input file).
        except:
            self.error_message = "%s couldn't be properly loaded. Try again with a different file or check the file for issues."%(data_file) # will probably want to try a whole bunch of things and then only raise an error if none of them work.
            self.raise_error()
            return 0

        xdata = copy.copy(fh[:,0]) # Need to handle both of these, just in case it's like an empty file (or has wrong number of columns or something)
        ydata = copy.copy(fh[:,1]) 
        low_intensity = numpy.mean(ydata)*2 # does this work? seems too easy. Probably not bad for semi-sparse spectra
        high_intensity = max(ydata)*1.05 # later actually read it in, but this isn't a bad guess
        self.status_window.append("Data file loaded successfully!")
        self.are_we_there_yet()

    def are_we_there_yet(self):
        global xdata
        global ydata

        if self.data_import_input.text() != '':
            have_data_file = True
        else:
            have_data_file = False

        if self.file_import_input.text() != '':
            have_file_dir = True
        else:
            have_file_dir = False

        if xdata != []:
            data_loaded = True
        else:
            data_loaded = False

        if have_data_file == False:
            self.browse_data_button.setFocus()
            self.load_button.setEnabled(False)
            self.run_autofit_button.setEnabled(False)
            xdata = []
            ydata = []
            return False
        else: # we have a data file
            if data_loaded == False:
                self.load_button.setEnabled(True)
                self.load_button.setFocus()
                self.run_autofit_button.setEnabled(False)
                return False
            else: # the data file has been loaded
                if have_file_dir == False:
                    self.browse_import_button.setFocus()
                    self.run_autofit_button.setEnabled(False)
                    return False
                else: # we have a directory with files to be run
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

        if job_name == "":
            self.error_message = "A directory containing input files needs to be selected!"
            self.raise_error()
            self.file_import_input.setFocus()
            self.run_autofit_button.setEnabled(False)
            return 0

        a = subprocess.Popen("copy SPFIT.EXE \"%s\SPFIT.EXE\""%(job_name), stdout=subprocess.PIPE, shell=True) # Windows specific, need to have SPFIT.EXE already
        a.stdout.read()

        a = subprocess.Popen("copy SPCAT.EXE \"%s\SPCAT.EXE\""%(job_name), stdout=subprocess.PIPE, shell=True) # Windows specific, need to have SPCAT.EXE already
        a.stdout.read()

        os.chdir(job_name)
        suffix = job_name.split("/")[-1]

        x = subprocess.Popen("dir /b %s*.txt"%suffix, stdout=subprocess.PIPE, shell=True)
        x = x.stdout.read().split()

        #total_num_files = len(x)
        # x contains the full list of files that we'll run Autofit on. Before doing that we should spline and peakpick and save in global variables so we're only doing it *once*.

        # worker/threading stuff starts here
        thread = self.thread = QtCore.QThread()
        worker = self.worker = Worker(x) # will want to give it whatever arguments it needs
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self.progress_update)
        worker.status.connect(self.status_update)
        worker.done.connect(self.exit_update)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        worker.finished.connect(thread.quit)
        thread.start()

        #for file1 in x:
            #print "Running autofit on %s"%file1
            #autofit_cluster_v3w.triples_calc(file1)

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
    def __init__(self, list_of_files, *args, **kwargs):
        QtCore.QObject.__init__(self, *args, **kwargs)
        self.percentage = 0
        self.list_of_files = list_of_files
        self.resolution = 2 # hardcoded for now, this will eventually pull from previous step in fully integrated tool
        self.inten_low = 0.0315 # hardcoded for now, this will eventually pull from previous step in fully integrated tool
        self.inten_high = 5.74687 # hardcoded for now, this will eventually pull from previous step in fully integrated tool

    def run(self): # should actually do a thing
        global peaklist

        list_of_files = self.list_of_files
        total_num_files = len(list_of_files)

        splined_spectrum = cubic_spline(self.resolution) # Interpolates experimental spectrum to a 2 kHz resolution with a cubic spline.  Gives better peak-pick values.
        (peaklist, freq_low, freq_high) = peakpicker(splined_spectrum,self.inten_low,self.inten_high) # Calls slightly modified version of Cristobal's routine to pick peaks instead of forcing user to do so.
        self.status.emit("Finished picking peaks from the spectrum file!")

        progress_counter = 0

        start_time = time.time()

        # More stuff gets done here
        for input_file in list_of_files:
            if progress_counter == 0:
                temp_string = "Starting calculations on first file; this may take a bit of time. A remaining time estimate will be available once the first job finishes."
                self.status.emit(temp_string)
            autofit_cluster_v3w_GUI.triples_calc(input_file,peaklist)
            progress_counter += 1
            percentage = int(math.floor(100.0*(float((progress_counter)/float(total_num_files)))))
            self.calculate_progress(percentage)
            current_time = time.time()
            elapsed_time = current_time - start_time
            remaining_time = (elapsed_time*100/percentage) - elapsed_time
            temp_string = "%s percent complete by file number! Taken %s seconds so far, about %s seconds remaining."%(percentage,int(math.ceil(elapsed_time)),int(math.ceil(remaining_time)))
            self.status.emit(temp_string)

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