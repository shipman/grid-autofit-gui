import subprocess
import os
import sys
import multiprocessing
from multiprocessing import Process, Queue
import re
import numpy
import random
import string
import math
import time
#import shutil
from scipy.interpolate import *

""""
Python Triples Fitter

Written by Ian Finneran, Steve Shipman at NCF

based on previous work by the Pate Lab at UVa

Please comment any changes you make to the code here:

version cluster:

-Made a number of changes from v15c so that there is no user input required, just reading things in from an input file.
For the time being, this means that some functionality has been removed (isotopologues, fit refining).

version cluster_v2:

-Modularized this so it can be called repeatedly by another script.

version cluster_v3:

-Time for some code cleanup! Removing all of the isotopologue stuff.

version 15c:

-Fixed an issue with reading var files that depended on which version of SPCAT was in use.  Also added a line to fix an 
unusual edge case with omc_inten that would occasionally lead to a crash for particularly poor combinations of predicted
and actual peak positions.

version 15b:

-Added a time estimate to the length of a job based on the number of triples to fit, the estimated time it takes to run
SPCAT 25 times, and the number of cores detected on the user's machine.  Time estimate assumes that the user will run the
job on all available cores.

-Dialogue boxes now give quantum numbers of transitions as well.

-Also fixed a bug in the final_uncerts function and shaved a few seconds off of the cubic_spline routine.

version 15:

-Added an intensity penalty to the scoring of potential fits.  Good fits need to have maximum intensity ratios and unitless
standard deviations of the intensity over all of the check peaks within 50 percent of theoretical values to avoid being
penalized.  Output stored the previous way is still stored in sorted-omc-cat.txt, output sorted the new way is in
sorted-inten-omc-cat.txt.  The "best 100" files are taken from the intensity sorted output.

version-14b:

-Added in manual selection of fitting peaks (rather than only choosing from the automatically-generated list).  Testing of this
revealed underlying bugs in isotopic substitution when transitions could leave the bounds after isotope scaling, requiring new
code to be written to allow the fitting transitions to be updated at various points in the overall algorithm.  The current
situation is still a bit ugly (functions requiring many, many input parameters) - this should be cleaned up in the future.

-Added in a "boundary penalty" to the score of triples in the automatically generated list based on how many are within 100 MHz
of a spectral boundary.

-Provided a user-dependent scale factor to filter acceptable transitions when searching for isotopolgoues.  The factor is used
to require that NS transitions be a certain minimum height (relative to the lower intensity threshold) in the experimental 
spectrum before they can be used as fitting or scoring transitions in the isotopologues.  If the user does not believe that
transitions from the NS isotopologue will be in their spectrum (e.g. pure compound of a synthetically produced isotopically-substituted 
species), they should set this factor to 0.

version-14:

-Merges v13 and v13-isotopes together into a single program.  Some code-tidying has been done to partially de-duplicate things.

-There is now more flexibility on coordinate input for isotopologue searches.  It can handle XYZ file format or either of the
primary formats that come from Gaussian output (5 column or 6 column).  It also shouldn't care if atom_labels are in atomic
number or in chemical symbol ("6" or "C").  Format detection is based on the number of entries in the first row.  If the first 
row contains 1 entry, it assumes XYZ format (which means line 2 is a comment and line 3 is the first line containing information 
about atom type and position).  If the first row contains either 5 or 6 entries, it assumes it is the appopriate format from 
Gaussian output.

version 13-isotopes:

Uses version 13 code as base, with isotopologue constant generator slapped on top.  Later will merge into v14, most likely.
Will run separate triples fitter runs on each isotopologue selected by user.  Right now behavior is that user selects one or
more atom types (list automatically determined from an ab initio structure input), and the triples fitter will examine all
singly-substituted species of those types.  Each fit is saved in a separate sub-directory.

Format of structure file is from Gaussian output (below for EEO):

      1          6           0       -2.670317    0.571148    0.159988
      2          1           0       -2.434542    1.571170   -0.210325
      3          1           0       -2.719870    0.603794    1.250293
      4          1           0       -3.650729    0.279198   -0.226138
      5          6           0       -1.617736   -0.419313   -0.289709
      6          1           0       -1.854133   -1.429010    0.076941
      7          1           0       -1.565139   -0.462200   -1.387392
      8          8           0       -0.364732   -0.006000    0.230899
      9          6           0        0.682634   -0.891655   -0.124503
     10          1           0        0.539846   -1.873119    0.351947
     11          1           0        0.711070   -1.021547   -1.215745
     12          6           0        1.972157   -0.256104    0.344429
     13          1           0        2.816465   -0.900076    0.088216
     14          1           0        1.939463   -0.136824    1.434893
     15          8           0        2.193845    0.987588   -0.298292
     16          1           0        1.384241    1.491448   -0.164781


version 13 features:

-after the fitting has completed, the user can select individual results to further refine by fitting
distortion constants and adding additional transitions.  Any number of the top 100 fits can be refined 
in this fashion.  The fit files thus generated are copied and are available for use with other programs 
(such as AABS).

-User-supplied spectrum is interpolated to 2 kHz resolution with a cubic spline prior to peakpicking.
This currently happens automatically, regardless of actual resolution of user-file.  Should probably check
to make sure that we're not actually downgrading the resolution of the data.

-Some code & comment tidying / compaction.

version 12 features:

-peaks are found from spectral data; user no longer supplies a list of picked peaks first.  High and low 
frequency ranges are automatically determined from the spectrum file.

-only physically reasonable results are saved to file (A >= B >= C, all rotational constants are positive)

-More flexibility with choosing search windows; fixed width for each transition, different for different
transitions, or based on 3x the estimated SPCAT uncertainty.  (The SPCAT uncertainties assume errors of 
2 percent on A, 1 percent on B and C, 10 percent on DJ, DJK, and DK, and 30 percent on dJ, dK.  These may 
need to be revisited.)  Also, this should later be expanded to allow for the selection of isotopic windows
based on ab initio scaling.

-Program alerts user if search windows will exceed bounds of the spectrum and prompts them for new uncertainties
or lets them accept the consequences of their choices.  The user can also elect to quit at this point if they realize
they have a transition far too close to one of the bounds of the spectrum.

version 11 features:

-sorting of triples list to evaluate most promising candidates first

-interim output of good fit results to unsorted file


version 10 features:

-minor bugfixes in displays of numbers in choice boxes and linear-dependence code

-automatic score calculation and ranking of possible triples fitting combinations


version 9 features:

-memory handling


-can use any number of processors, I left the code for my old method of multiprocessing commented out at the bottom
just in case there are bugs with the new version

-input files
if you leave out the "check peaks" or trans_x area it will prompt you for transitions...

example input file:


Job Name conf_I_#2 
 u_A: 0.0 
 u_B: 1.0 
 u_C: 0.0 
 A: 0.98187789E+04 
 B: 0.87351235E+03 
 C: 0.82235840E+03 
 DJ: -0.46322711E-04 
 DJK: 0.80645742E-03 
 DK: -0.23482420E-01 
 dJ: -0.49333549E-05 
 dK: 0.11644082E-03 
 processors: 8 
 freq_high: 18000.0 
 freq_low: 8000.0 
 inten_high: 100000.0 
 inten_low: 0.0 
 Temp: 2.0 
 Jmax: 30.0 
 freq_uncertainty: 900.0 
 number of triples: 7106688 
 Check peaks:
('-6.1163', ' 9360.6137', ' 5 1 4', ' 5 0 5')
('-6.1236', ' 9229.3112', ' 4 1 3', ' 4 0 4')
('-6.1397', ' 9519.9682', ' 6 1 5', ' 6 0 6')
('-6.1689', ' 9125.2491', ' 3 1 2', ' 3 0 3')
('-6.1896', ' 9708.3423', ' 7 1 6', ' 7 0 7')
('-6.2029', '12285.8335', ' 2 1 2', ' 1 0 1')
('-6.2633', ' 9926.8555', ' 8 1 7', ' 8 0 8')
('-6.2672', ' 9047.7751', ' 2 1 1', ' 2 0 2')
 
 trans_1: ('-5.8815', '15499.0588', ' 4 1 4', ' 3 0 3') 
 trans_2: ('-6.0131', '13905.0568', ' 3 1 3', ' 2 0 2') 
 trans_3: ('-6.7334', '15777.1423', ' 6 2 4', ' 7 1 7')





"""
def fifth(templist):
    return templist[4]

def int_writer(u_A,u_B,u_C, J_min="00", J_max="20", inten="-10.0",Q_rot="300000",freq="25.8", temperature="298"):#generates SPCAT input file
    input_file = ""
    input_file += "Molecule \n"
    input_file += "0  91  %s  %s  %s  %s  %s %s  %s\n"%(Q_rot, J_min, J_max,inten,inten,freq, temperature)
    input_file += " 001  %s \n" % u_A
    input_file += " 002  %s \n" % u_B
    input_file += " 003  %s \n" % u_C

    fh_int = open("default.int", "w")

    fh_int.write(input_file)
    fh_int.close()


def var_writer(A,B,C,DJ,DJK,DK,dJ,dK):#generates SPCAT input file

    dA = str(0.2*float(A))  #These are very rough estimates of the uncertainty on the rotational constants.  May need to be considerably refined.
    dB = str(0.2*float(B))
    dC = str(0.2*float(C))
    dDJ = str(0.5*float(DJ))
    dDJK = str(0.5*float(DJK))
    dDK = str(0.5*float(DK))
    ddJ = str(0.5*float(dJ))
    ddK = str(0.5*float(dK))

    fh_var = open("default.var",'w')

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

def cubic_spline(spectrum,new_resolution): # Cubic spline of spectrum to new_resolution; used pre-peak-picking.  Assumes spectrum is already in order of increasing frequency.

    x = spectrum[:,0]
    y = spectrum[:,1]

    old_resolution = (x[-1]-x[0]) / len(spectrum)
    scale_factor = old_resolution / new_resolution

    new_length = int(math.floor(scale_factor*len(spectrum)))

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

def run_SPCAT(): 
    a = subprocess.Popen("SPCAT default", stdout=subprocess.PIPE, shell=False)
    a.stdout.read()#seems to be best way to get SPCAT to finish. I tried .wait(), but it outputted everything to screen
 
def cat_reader(freq_high,freq_low): #reads output from SPCAT

    fh = open("default.cat")

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

def final_uncerts(trans_1_center,trans_2_center,trans_3_center,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,freq_low,freq_high,full_list,A,B,C,DJ,DJK,DK,dJ,dK,temperature,u_A,u_B,u_C,trans_1,trans_2,trans_3):
    
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
            print 'You do not have three distinct transitions.  Quitting.'
            quit()
            
    return trans_1,trans_2,trans_3,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty


def triples_gen(trans_1_uncert,trans_2_uncert,trans_3_uncert,freq_uncertainty,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,peaklist,freq_low,freq_high,full_list,A,B,C,DJ,DJK,DK,dJ,dK,temperature,u_A,u_B,u_C,trans_1,trans_2,trans_3):

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

        while uncertainty_flag ==1:            
            if freq_uncertainty==0.0:
                freq_uncertainty = 100.0
                peak_1_uncertainty = freq_uncertainty
                peak_2_uncertainty = freq_uncertainty
                peak_3_uncertainty = freq_uncertainty
            
            (trans_1,trans_2,trans_3,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty) = final_uncerts(trans_1_center,trans_2_center,trans_3_center,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,freq_low,freq_high,full_list,A,B,C,DJ,DJK,DK,dJ,dK,temperature,u_A,u_B,u_C,trans_1,trans_2,trans_3)
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
            
            if trans_1_peaks == [] or trans_2_peaks == [] or trans_3_peaks == []:
                peak_1_uncertainty = 2*peak_1_uncertainty
                peak_2_uncertainty = 2*peak_2_uncertainty
                peak_3_uncertainty = 2*peak_3_uncertainty

            uncertainty_flag = 0
    
    return trans_1,trans_2,trans_3,trans_1_peaks,trans_2_peaks,trans_3_peaks,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,num_of_triples

def fit_triples(q,list_a,list_b,list_c,trans_1,trans_2,trans_3,top_17,peaklist,file_num,A,B,C,DJ,DJK,DK,dJ,dK):
    
    all_combo_file = "all_combo_list%s.txt"%(str(file_num)) 
    
    all_combo_list_file  = open(all_combo_file,"a")
    
    temp_list_a = []
    temp_list_b = []
    temp_list_c = []

    peak_list_1 = peaklist[0:int(len(peaklist)/4)]#splits peaks into 4 parts to speed up processing
    peak_list_2 = peaklist[int(len(peaklist)/4):int(len(peaklist)/2)]
    peak_list_3 = peaklist[int(len(peaklist)/2):int(len(peaklist)*0.75)]
    peak_list_4 = peaklist[int(len(peaklist)*0.75):len(peaklist)]

    p_1 = float(peak_list_1[0][0])
    p_2 = float(peak_list_1[-1][0])
    p_3 = float(peak_list_2[0][0])
    p_4 = float(peak_list_2[-1][0])
    p_5 = float(peak_list_3[0][0])
    p_6 = float(peak_list_3[-1][0])
    p_7 = float(peak_list_4[0][0])
    p_8 = float(peak_list_4[-1][0])


    pred_ratio = pow(10,max(float(trans_1[0]),float(trans_2[0]),float(trans_3[0]))-min(float(trans_1[0]),float(trans_2[0]),float(trans_3[0])))

    for freq_1,inten_1 in list_a:
      temp_diff = abs(float(trans_1[1])-float(freq_1))
      temp_list_a.append((freq_1,inten_1,temp_diff))

    for freq_2,inten_2 in list_b:
      temp_diff = abs(float(trans_2[1])-float(freq_2))
      temp_list_b.append((freq_2,inten_2,temp_diff))

    for freq_3,inten_3 in list_c:
      temp_diff = abs(float(trans_3[1])-float(freq_3))
      temp_list_c.append((freq_3,inten_3,temp_diff))

    unsorted_full_list = []

    for freq_1,inten_1,diff_1 in temp_list_a:
        for freq_2,inten_2,diff_2 in temp_list_b:
            for freq_3,inten_3,diff_3 in temp_list_c:
                real_ratio = max(float(inten_1),float(inten_2),float(inten_3))/min(float(inten_1),float(inten_2),float(inten_3))
                avg_diff = (diff_1+diff_2+diff_3)/3
                scaled_diff = avg_diff*(abs(real_ratio-pred_ratio)+1) # Freq. difference scaled by deviation of intensity ratio from predicted
                unsorted_full_list.append((freq_1,inten_1,freq_2,inten_2,freq_3,inten_3,scaled_diff))

    sorted_full_list = sorted(unsorted_full_list, key=lambda entry: entry[6])

    line_counter = 0
    for freq_1,inten_1,freq_2,inten_2,freq_3,inten_3,total_diff in sorted_full_list:
        all_combo_list_file.write(str(freq_1)+","+str(inten_1)+","+str(freq_2)+","+str(inten_2)+","+str(freq_3)+","+str(inten_3)+", \n")
        line_counter += 1

    #for freq_1,inten_1,diff_1 in sorted_list_a:#generates all combinations of three peaks from three peaklists
    #    for freq_2,inten_2,diff_2 in sorted_list_b:
    #        for freq_3,inten_3,diff_3 in sorted_list_c:
    #            all_combo_list_file.write(str(freq_1)+","+str(inten_1)+","+str(freq_2)+","+str(inten_2)+","+str(freq_3)+","+str(inten_3)+", \n")
    
    all_combo_list_file.close()
    
    all_combo_list_file = open(all_combo_file)
    
    final_omc = []
    triples_counter = 0
    output_file = ""
    regular_counter = 0
    total_counter = 0
    #error_counter = 0



    for all_combo_line in all_combo_list_file:
        all_combo_line = all_combo_line.split(",")
        peaks_triple= [(all_combo_line[0],all_combo_line[1]),(all_combo_line[2],all_combo_line[3]),(all_combo_line[4],all_combo_line[5])]
        

        input_file = ""
        input_file += "anisole                                         Wed Mar Thu Jun 03 17:45:45 2010\n"
        input_file += "   8  500   5    0    0.0000E+000    1.0000E+005    1.0000E+000 1.0000000000\n" # don't choose more than 497 check transitions or it will crash.
        input_file +="a   1  1  0  50  0  1  1  1  1  -1   0\n"
        input_file += "           10000  %s 1.0E+004 \n" % A
        input_file += "           20000  %s 1.0E+004 \n" % B
        input_file += "           30000  %s 1.0E+004 \n" % C
        input_file += "             200  %s 1.0E-025 \n" % DJ
        input_file += "            1100  %s 1.0E-025 \n" % DJK
        input_file += "            2000  %s 1.0E-025 \n" % DK
        input_file += "           40100  %s 1.0E-025 \n" % dJ
        input_file += "           41000  %s 1.0E-025 \n" % dK
        fh_par = open("default%s.par"%(str(file_num)),'w')
        fh_par.write(input_file)
        fh_par.close()

        input_file = ""#the next part adds in the three peaks to be fit
        input_file += trans_1[2][0:2]+' '+trans_1[2][2:4]+' '+trans_1[2][4:6]+' '+\
                      trans_1[3][0:2]+' '+trans_1[3][2:4]+' '+trans_1[3][4:6]+'                      '+peaks_triple[0][0]+' 0.50 1.0000\n' 
        input_file += trans_2[2][0:2]+' '+trans_2[2][2:4]+' '+trans_2[2][4:6]+' '+\
                      trans_2[3][0:2]+' '+trans_2[3][2:4]+' '+trans_2[3][4:6]+'                      '+peaks_triple[1][0]+' 0.50 1.0000\n' 
        input_file += trans_3[2][0:2]+' '+trans_3[2][2:4]+' '+trans_3[2][4:6]+' '+\
                      trans_3[3][0:2]+' '+trans_3[3][2:4]+' '+trans_3[3][4:6]+'                      '+peaks_triple[2][0]+' 0.50 1.0000\n'
        counter = 0
        for line in top_17:#the hack that adds in the check transitions but doesn't use them in the fit
            input_file += line[2][0:2]+' '+line[2][2:4]+' '+line[2][4:6]+' '+\
                      line[3][0:2]+' '+line[3][2:4]+' '+line[3][4:6]+'                      '+'%s.0'%(str(counter))+' 0.00 1.0000\n'
            counter += 1
        fh_lin = open("default%s.lin"%(str(file_num)), "w")
        fh_lin.write(input_file)
        fh_lin.close()        
        a = subprocess.Popen("SPFIT%s default%s"%(str(file_num),str(file_num)), stdout=subprocess.PIPE, shell=False)
        a.stdout.read()#used to let SPFIT finish

        const_list = []

        fh_var = open("default%s.var"%(str(file_num)))
        for line in fh_var:
            if line.split()[0] == "10000":
                temp_A = float(line.split()[1])
                const_list.append("%.3f" %temp_A)
            if line.split()[0] == "20000":
                temp_B = float(line.split()[1])
                const_list.append("%.3f" %temp_B)
            if line.split()[0] == "30000":
                temp_C = float(line.split()[1])
                const_list.append("%.3f" %temp_C)

        fh_fit = open("default%s.fit"%(str(file_num)))
        file_list = []
        for line in fh_fit:
                file_list.append(line)

        freq_list = []
        for x in range(len(file_list)):
            if file_list[-x][11:14] == "RMS":
                rms_fit = float(file_list[-x][22:32]) #note - assumes RMS fit error is less than 1 GHz.  Change 22 to 21 if this is a problem.
            if file_list[-x][5:6] == ":" and int(file_list[-x][3:5])>3:
                freq_list.append(file_list[-x][60:71])
            if file_list[-x][40:64]=="EXP.FREQ.  -  CALC.FREQ.":
                break
        read_fit = (const_list[0],const_list[1], const_list[2],freq_list)
        triples_counter +=1
        total_counter +=1
        constants = read_fit[0:3]
        freq_17 = read_fit[3]
        freq_17.reverse()
        A_1 = float(constants[0])
        B_1 = float(constants[1])
        C_1 = float(constants[2])
        omc_list = []
        
        theor_inten_list = []
        for x in range(len(top_17)):
            temp_inten = 10**float(top_17[x][0])
            theor_inten_list.append(temp_inten)

        theor_inten_ratio = (max(theor_inten_list)/min(theor_inten_list))
        theor_inten_avg = (sum(theor_inten_list)/len(theor_inten_list))
        theor_inten_unitless_stdev = numpy.std(theor_inten_list)/theor_inten_avg

        for x in range(len(top_17)): #matches peaks in the top 17 to peaks in experimental peak list <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            qnum_up = top_17[x][2]
            qnum_low = top_17[x][3]
            real_omc = 1.0
            current_peak = float(freq_17[x])
            if current_peak>p_1 and current_peak<p_2:#conditionals to find proper portion of experimental peak list to loop through
                peaks_section = peak_list_1
                peak = p_2
                regular_counter +=1
            elif current_peak>p_3 and current_peak<p_4:
                peaks_section = peak_list_2
                peak = p_4
                regular_counter +=1
            elif current_peak>p_5 and current_peak<p_6:
                peaks_section = peak_list_3
                peak = p_6
                regular_counter +=1
            elif current_peak>p_7 and current_peak<p_8:
                peaks_section = peak_list_4
                peak = p_8
                regular_counter +=1
            elif current_peak>p_8 or current_peak<p_1:
                peaks_section = peaklist
                peak = p_8
                #error_counter +=1
                real_omc = 0.0# this is the omc if you throw out peaks that go over the edge of the spectrum
            else:
                peaks_section = peaklist
                peak = p_8
                regular_counter +=1
            old_omc = 100000.0
            omc_inten = 100000.0
            for peak_freq,peak_inten in peaks_section: #find nearest peak in actual spectrum to the given top 20 peak
                omc = abs(current_peak-float(peak_freq))
                omc_low = abs(current_peak-float(peak))
                if omc>old_omc:
                    omc_low = old_omc
                    omc_inten = temp_inten                    
                    break
                old_omc = omc
                temp_inten = peak_inten
            if real_omc == 1.0:
                real_omc = omc_low
            omc_list.append((omc_low, real_omc, omc_inten))# current_peak,qnum_up,qnum_low)) you can add in this extra output, but its slower
        omc_avg = [float(omc) for omc, real_omc, omc_inten in omc_list]
        real_omc_avg = [float(real_omc) for omc, real_omc, omc_inten in omc_list]
        omc_inten_scoring = [float(omc_inten) for omc, real_omc, omc_inten in omc_list]
        score = str(len([omc for omc in omc_avg if omc<2.0])) #scores the accuracy of the fit, currently based on a peak being within 2 MHz which may be too coarse
        avg = (sum(omc_avg)/len(omc_avg))+rms_fit
        real_avg = (sum(real_omc_avg)/len(real_omc_avg))+rms_fit

        omc_inten_ratio = (max(omc_inten_scoring)/min(omc_inten_scoring))
        omc_inten_avg = (sum(omc_inten_scoring)/len(omc_inten_scoring))
        omc_inten_unitless_stdev = numpy.std(omc_inten_scoring)/omc_inten_avg

        score_inten_penalty = 1

        if (omc_inten_ratio <= 0.5*theor_inten_ratio) or (omc_inten_ratio >= 1.5*theor_inten_ratio):
            score_inten_penalty += 1

        if (omc_inten_unitless_stdev <= 0.5*theor_inten_unitless_stdev) or (omc_inten_unitless_stdev >= 1.5*theor_inten_unitless_stdev):
            score_inten_penalty += 1
        
        penalized_avg = avg*score_inten_penalty

        if float(A_1)>=float(B_1) and float(B_1)>=float(C_1) and float(C_1)>0:
            if int(score)<10: #makes sorting work properly later
                score = '0'+score  
            output_file += 'score = '+' '+score+' '+"Const = "+str(A_1)+' '+str(B_1)+' '+str(C_1)+' '+"average omc = "+str(avg)+'  '+"avg w/out peaks over edge = "+str(real_avg)+' '+"avg w/ inten penalty = "+str(penalized_avg)+"\n"

            if real_avg <= 0.2: #appends good finds (RMS < 0.2 MHz, ignoring peaks over edge) to interim file for each processor
                interim_output = 'score = '+' '+score+' '+"Const = "+str(A_1)+' '+str(B_1)+' '+str(C_1)+' '+"average omc = "+str(avg)+'  '+"avg w/out peaks over edge = "+str(real_avg)+' '+"avg w/ inten penalty = "+str(penalized_avg)+"\n"
                fh_interim_good = open("interim_good_output%s.txt"%(str(file_num)), "a")
                fh_interim_good.write(interim_output)
                fh_interim_good.close()

            if triples_counter == 100000: #appends to file after every 100000 triples
                fh_final = open("final_output%s.txt"%(str(file_num)), "a")
                fh_final.write(output_file)
                fh_final.close()
                triples_counter = 0
                output_file = ""

            if triples_counter != 0 and (triples_counter % 1000 == 0): # Update progress bar every 1000; this may be too frequent, but is fine for testing
                frac_output = float(total_counter)/float(line_counter)
                q.put([frac_output,"Processing",file_num])

    fh_final = open("final_output%s.txt"%(str(file_num)), "a")#writes separate file for each processor
    fh_final.write(output_file)
    fh_final.close()
    os.system("sort /r final_output%s.txt /o sorted_final_out%s.txt"%(str(file_num),str(file_num)))#sorts output by score

    if line_counter != 0:
        frac_output = float(total_counter)/float(line_counter)
    else: # not any triples because list was so short, this processor didn't have anything to do!
        frac_output = 1.0
    q.put([frac_output,"Done",file_num])
    

def triples_calc(worker,param_file,peaklist):
    x = subprocess.Popen("dir /b", stdout=subprocess.PIPE, shell=True)
    x = x.stdout.read().split()

    fitting_peaks_flag =0
    
    check_peaks_list = []
    fit_peaks_list = []
    freq_uncertainty = 0.0

    fh_input = open(param_file)
    job_name = ""
        
    for line in fh_input:
            
        if line.split() != []:
                                
            if line.split()[0] == "u_A:":
                u_A = line.split()[1] 
            if line.split()[0] == "u_B:":
                u_B = line.split()[1] 
            if line.split()[0] == "u_C:":
                u_C = line.split()[1] 
            if line.split()[0] == "A:":
                A = line.split()[1] 
            if line.split()[0] == "B:":
                B = line.split()[1]
            if line.split()[0] == "C:":
                C = line.split()[1]
            if line.split()[0] == "DJ:":
                DJ = line.split()[1]
            if line.split()[0] == "DK:":
                DK = line.split()[1]
            if line.split()[0] == "DJK:":
                DJK = line.split()[1] 
            if line.split()[0] == "dJ:":
                dJ = line.split()[1]
            if line.split()[0] == "dK:":
                dK = line.split()[1]
            if line.split()[0] == "freq_high:":
                freq_high = float(line.split()[1])  
            if line.split()[0] == "freq_low:":
                freq_low = float(line.split()[1])  
            if line.split()[0] == "inten_high:":
                inten_high = float(line.split()[1]) 
            if line.split()[0] == "inten_low:":
                inten_low = float(line.split()[1])
            if line.split()[0] == "processors:":
                processors = int(line.split()[1])
            if line.split()[0] == "Temp:":
                temperature = float(line.split()[1])
            if line.split()[0] == "Jmax:":
                Jmax = float(line.split()[1])
            if line.split()[0] == "freq_uncertainty:":
                freq_uncertainty = float(line.split()[1])                    
            if line.split()[0] == "job_name:":
                job_name = str(line.split()[1])                    
            if line.split()[0] == "data_file:":
                data_file = str(line.split()[1])                    

            if line.split()[0] == "trans_1:" or line.split()[0] == "trans_2:" or line.split()[0] == "trans_3:":
                fitting_peaks_flag = 0
                clean = line[12:53]
                re_split = clean.split("', '")
                tuples = tuple(re_split)
                fit_peaks_list.append(tuples)
                  
                    
            if fitting_peaks_flag == 1:
                clean = line[2:43]
                re_split = clean.split("', '")
                tuples = tuple(re_split)
                check_peaks_list.append(tuples)
            if line.split()[0] == "Check":
                fitting_peaks_flag = 1
                                    
    file_flag = 1

    if job_name == "":
        # We accidentally read a file that's not really an input file; let's just return instead
        return
    
    while file_flag==1:
        marker1 = 0
        for file1 in x:
            if job_name ==file1:
                marker1 = 1
                job_name += 'a' # Need to do something cleverer than this later, but this will be fine for now.  I also like that doing this repeatedly will make a file name that screams at you. 
        if marker1 ==0:
            file_flag =0
        
    a = subprocess.Popen("mkdir \"%s\""%job_name, shell=True)
    a.wait()

    for number in range(processors): # This may need extensive changing for the cluster...
        y = subprocess.Popen("copy SPFIT.EXE \"%s\SPFIT%s.EXE\""%(job_name,number), stdout=subprocess.PIPE, shell=True)
        y.stdout.read()     

    y = subprocess.Popen("copy SPCAT.EXE \"%s\SPCAT.EXE\""%(job_name), stdout=subprocess.PIPE, shell=True)
    y.stdout.read() 
    
    os.chdir(job_name)
    
    trans_1 = fit_peaks_list[0]
    trans_2 = fit_peaks_list[1]
    trans_3 = fit_peaks_list[2]

    int_writer(u_A,u_B,u_C, J_max=Jmax,freq=str((freq_high*.001)), temperature=temperature)
    var_writer(A,B,C,DJ,DJK,DK,dJ,dK)
    run_SPCAT()

    full_list = cat_reader(freq_high,freq_low)	# New code starts here

    trans_1_center = float(trans_1[1])
    trans_2_center = float(trans_2[1])
    trans_3_center = float(trans_3[1])

    trans_1_uncert = freq_uncertainty
    trans_2_uncert = freq_uncertainty
    trans_3_uncert = freq_uncertainty

    user_flag = 0
    est_unc_flag = 0
    same_flag = 0
    bad_windows = 0

    peak_1_uncertainty = 0
    peak_2_uncertainty = 0
    peak_3_uncertainty = 0

    (trans_1,trans_2,trans_3,trans_1_peaks,trans_2_peaks,trans_3_peaks,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,num_of_triples) = triples_gen(trans_1_uncert,trans_2_uncert,trans_3_uncert,freq_uncertainty,peak_1_uncertainty,peak_2_uncertainty,peak_3_uncertainty,peaklist,freq_low,freq_high,full_list,A,B,C,DJ,DJK,DK,dJ,dK,temperature,u_A,u_B,u_C,trans_1,trans_2,trans_3)

    top_peaks = check_peaks_list

    top_peaks_3cut = []
    for entry in top_peaks:
        if (entry[2] == trans_1[2] and entry[3] == trans_1[3]) or (entry[2] == trans_2[2] and entry[3] == trans_2[3]) or (entry[2] == trans_3[2] and entry[3] == trans_3[3]):
            pass
        else:
            top_peaks_3cut.append(entry)

    job_file = ""
    str(top_peaks_3cut)
    str(trans_1)
    str(trans_2)
    str(trans_3)
    fitting_peaks_str = ""
    for entry in top_peaks_3cut:
        fitting_peaks_str+=str(entry)+"\n"
            
    job_file += "job_name: %s \n data_file: %s \n u_A: %s \n u_B: %s \n u_C: %s \n A: %s \n B: %s \n \
    C: %s \n DJ: %s \n DJK: %s \n DK: %s \n dJ: %s \n dK: %s \n processors: %s \n freq_high: %s \n freq_low: %s \n \
    inten_high: %s \n inten_low: %s \n Temp: %s \n Jmax: %s \n freq_uncertainty: %s \n number of triples: %s \n Check peaks:\n%s \n trans_1: %s \n trans_2: %s \n trans_3: %s "%(job_name,data_file,u_A,u_B,u_C,A,B,C,DJ,DJK,DK,dJ,dK,str(processors),str(freq_high),\
        str(freq_low),str(inten_high),str(inten_low),str(temperature),str(Jmax),str(freq_uncertainty),str(num_of_triples),fitting_peaks_str,str(trans_1),str(trans_2),str(trans_3))

    suffix = job_name.split("/")[-1]
    Job_fh = open("input_data_%s.txt"%(suffix),"w")
    Job_fh.write(job_file) 
    Job_fh.close()

    new_list = []

    new_list = [(len(trans_1_peaks),"trans_1_peaks"),(len(trans_2_peaks),"trans_2_peaks"),(len(trans_3_peaks),"trans_3_peaks")]
    new_list.sort()

    flag123 = 0
    flag132 = 0
    flag213 = 0
    flag231 = 0
    flag312 = 0
    flag321 = 0

    if (len(trans_1_peaks) >= len(trans_2_peaks)) and (len(trans_1_peaks) >= len(trans_3_peaks)):
    	list_a_peaks = trans_1_peaks
    	if len(trans_2_peaks) >= len(trans_3_peaks):
    		list_b_peaks = trans_2_peaks
    		list_c_peaks = trans_3_peaks
    		flag123 = 1
    	elif len(trans_3_peaks) >= len(trans_2_peaks):
    		list_b_peaks = trans_3_peaks
    		list_c_peaks = trans_2_peaks
    		flag132 = 1
    elif (len(trans_2_peaks) >= len(trans_1_peaks)) and (len(trans_2_peaks) >= len(trans_3_peaks)):
        list_a_peaks = trans_2_peaks
        if len(trans_1_peaks) >= len(trans_3_peaks):
        	list_b_peaks = trans_1_peaks
        	list_c_peaks = trans_3_peaks
        	flag213 = 1
        elif len(trans_3_peaks) >= len(trans_1_peaks):
        	list_b_peaks = trans_3_peaks
        	list_c_peaks = trans_1_peaks
        	flag231 = 1
    elif (len(trans_3_peaks) >= len(trans_1_peaks)) and (len(trans_3_peaks) >= len(trans_2_peaks)):
        list_a_peaks = trans_3_peaks
        if len(trans_1_peaks) >= len(trans_2_peaks):
        	list_b_peaks = trans_1_peaks
        	list_c_peaks = trans_2_peaks
        	flag312 = 1
        elif len(trans_2_peaks) >= len(trans_1_peaks):
        	list_b_peaks = trans_2_peaks
        	list_c_peaks = trans_1_peaks
        	flag321 = 1


    random.shuffle(list_c_peaks)  # Shuffle so that each processor gets a range of values for the third peak, not processor 0 getting only the lowest frequencies.  

    list_c_list = []
    for num in range(processors):
        processors = float(processors)
        num = float(num)
        x = int((num)*(len(list_c_peaks)/processors))
        y = int(len(list_c_peaks)*((num+1)/processors))
        list_c_list.append(list_c_peaks[x:y])
    list_c_list.append("marker")

    if flag123 == 1:
        trans_1_peaks = list_a_peaks
        trans_2_peaks = list_b_peaks
        trans_3_peaks = list_c_list
    if flag213 == 1:
        trans_1_peaks = list_b_peaks
        trans_2_peaks = list_a_peaks
        trans_3_peaks = list_c_list
    if flag312 == 1:
        trans_1_peaks = list_b_peaks
        trans_2_peaks = list_c_list
        trans_3_peaks = list_a_peaks
    if flag132 == 1:
        trans_1_peaks = list_a_peaks
        trans_2_peaks = list_c_list
        trans_3_peaks = list_b_peaks
    if flag231 == 1:
        trans_1_peaks = list_c_list
        trans_2_peaks = list_a_peaks
        trans_3_peaks = list_b_peaks
    if flag321 == 1:
        trans_1_peaks = list_c_list
        trans_2_peaks = list_b_peaks
        trans_3_peaks = list_a_peaks

    processors = int(processors)

    q = Queue()
    finished_tracker = numpy.zeros(processors, dtype=int)
    counter_tracker = numpy.zeros(processors)

    for num in range(processors):

        if trans_1_peaks[-1]=="marker":
            trans_x_peaks = trans_1_peaks[num]
            trans_y_peaks = trans_2_peaks
            trans_z_peaks = trans_3_peaks
            
        if trans_2_peaks[-1]=="marker":
            trans_x_peaks = trans_1_peaks
            trans_y_peaks = trans_2_peaks[num]
            trans_z_peaks = trans_3_peaks

        if trans_3_peaks[-1]=="marker":
            trans_x_peaks = trans_1_peaks
            trans_y_peaks = trans_2_peaks
            trans_z_peaks = trans_3_peaks[num]
            
        vars()["p%s"%str(num)] = Process(target=fit_triples, args=(q,trans_x_peaks,trans_y_peaks,trans_z_peaks,trans_1,trans_2,trans_3,top_peaks_3cut,peaklist,num,A,B,C,DJ,DJK,DK,dJ,dK))

    #start_time = time.time()

    for num in range(processors):
        vars()["p%s"%str(num)].start()

    while True: # have it break when it receives a "done" from everyone
        try:
            [frac_counter,message,which_proc] = q.get()
            counter_tracker[which_proc] = frac_counter
            total_progress = sum(counter_tracker)
            percentage = int(math.floor(100.0*(float((total_progress)/float(processors)))))
            worker.calculate_subprogress(percentage)
            if message == "Done":
                finished_tracker[which_proc] = 1
        except:
            pass
        # if everything is done, then break
        if (all(value != 0 for value in finished_tracker)):
            #worker.subdone.emit(True)
            break

    for num in range(processors):
        vars()["p%s"%str(num)].join()
            
    a = subprocess.Popen('type sorted_final_out*.txt > all_output.txt 2>NUL', shell=True) # This is not currently sorted, need to fix for Windows
    a.wait()

    fh = open("all_output.txt")

    linelist = []

    for line in fh:
        new_line = line.strip('\r\n').split('=')
        new_new_line = []
        for element in new_line:
            temp = element.strip(' ').split()
            new_new_line.append(temp)

        score = int(new_new_line[1][0])
        A = float(new_new_line[2][0])
        B = float(new_new_line[2][1])
        C = float(new_new_line[2][2])
        avg_omc = float(new_new_line[3][0])
        avg_omc_no_edge = float(new_new_line[4][0])
        avg_omc_inten = float(new_new_line[5][0])

        linelist.append((score,A,B,C,avg_omc_inten,avg_omc,avg_omc_no_edge))

    fh.close()
    linelist.sort(key=fifth)

    output_file = ""

    for line in linelist:
        output_file += "Score: %s A = %s B = %s C = %s OMC_inten = %s OMC = %s OMC_no_edge = %s\n"%(line[0],line[1],line[2],line[3],line[4],line[5],line[6])

    fh_out = open("sorted_inten_omc_cat.txt","w")
    fh_out.write(output_file)
    fh_out.close()

    f = open('sorted_inten_omc_cat.txt','r')
    fits = []

    for i in range(100):
        r = f.readline()

        if i < 10:
            number = '0'+str(i)
        else:
            number = i

        temp = str(number) + ' ' + r
        fits.append(temp)

    f.close()

    OMC_char_buffer = ""
    for i in (fits):
        OMC_char_buffer += i+''

    f100=open('best100.txt','w')
    f100.write(OMC_char_buffer)
    f100.close()
    os.chdir(os.pardir)


if __name__ == '__main__': #multiprocessing imports script as module

    # Called directly from the command line, do stuff.
    triples_calc(str(sys.argv[1]))    