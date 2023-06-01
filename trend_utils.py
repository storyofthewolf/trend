# trend_utils.py
#
#
#
#  Contains functions for inputs, outputs, and basic plotting
#

import sys
import matplotlib.pyplot as plt
import numpy as np


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# // read_request_var //
# script to read in text files containing the string-type variable
# names requeted from the models.  lon, lat, lev, time ar always included and thus hardcoded.
# file out one formated text file. atm, lnd, ice
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def read_request_var(do_atm, do_ice):

    with open('vars.in', 'r') as f:
        atmstr = f.readline()
        atmvars= atmstr.split()
        icestr = f.readline()
        icevars= icestr.split()

    return atmvars, icevars

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# // print2screen //
# prints text to screen for running output
# not saved
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def print2screen(do_atm, time_vecA, vavg_vecA, intavg1_vecA, intavg2_vecA, slope_intavg1_vecA, slope_intavg2_vecA, \
                 do_ice, time_vecI, vavg_vecI, intavg1_vecI, intavg2_vecI, slope_intavg1_vecI, slope_intavg2_vecI, i):

    i=i+1
    if (i <  10): istr = '    '
    if (i >= 10):  istr = '   '
    if (i >= 100):  istr = '  '
    if (i >= 1000):  istr = ' '
    if (i >= 10000):  istr = ''

    if (do_atm == True): 
        p1 = [vavg_vecA[4], intavg1_vecA[4], intavg2_vecA[4]]  # temperatures
        p2 = [slope_intavg2_vecA[1], slope_intavg2_vecA[4]]    # temperature time derivatives
        v1 = intavg2_vecA[6]-intavg2_vecA[5]                   # TOA energy balance
        v2 = intavg2_vecA[8]-intavg2_vecA[7] - intavg2_vecA[9] - intavg2_vecA[10] #Surface Energy Balance
        print(istr, i, "{:.3f} {:.3f} {:.3f}".format(*p1), v1, v2)

    if (do_ice == True):
        p1 = intavg2_vecI[1]   # temperatures
        p2 = intavg2_vecI[6]   # ice height
        p3 = intavg2_vecI[7]   # snow height
        p4 = slope_intavg2_vecI[6]
        p5 = slope_intavg2_vecI[7]
        p6 = intavg2_vecI[4]   # ice energy
        p7 = intavg2_vecI[5]   # snow energy
        p8 = slope_intavg2_vecI[4]
        p9 = slope_intavg2_vecI[5]
        print(istr, i, p1, p2, p3, p6, p7, p8, p9)

    return


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# // print2text //
# prints output data to text file
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def print2text(do_atm, vnamesA, time_vecA, vavg_vecA, intavg1_vecA, intavg2_vecA, slope_intavg1_vecA, slope_intavg2_vecA, \
               do_ice, vnamesI, time_vecI, vavg_vecI, intavg1_vecI, intavg2_vecI, slope_intavg1_vecI, slope_intavg2_vecI, \
               firstDate, lastDate, case_id):

    a = np.where(time_vecA != 0)
    a=np.squeeze(a)
    na = len(a)-1

    outfile = "data/" + case_id +"_" + firstDate + "-" + lastDate + "_cam.txt"
    if (do_atm == True):
        with open(outfile,"w") as f:
            for i in time_vecA[0:na]:
               i=int(i)
               print(i, vavg_vecA[i,4], file=f)


    outfile = "data/" + case_id +"_" + firstDate + "-" + lastDate + "_cice.txt"
    if (do_ice == True):
        with open(outfile,"w") as f:
            for i in time_vecI[0:na]:
               i=int(i)
               print(i, vavg_vecI[i,4], file=f)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# // timeSeriesPlots //
# makes time-series plots at runtime
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def timeSeriesPlots(do_atm, time_vecA, vavg_vecA, intavg1_vecA, intavg2_vecA, slope_intavg1_vecA, slope_intavg2_vecA, \
                    do_ice, time_vecI, vavg_vecI, intavg1_vecI, intavg2_vecI, slope_intavg1_vecI, slope_intavg2_vecI, \
                    firstDate, lastDate, case_id):

    
    time_vecA          = np.array(time_vecA)
    vavg_vecA          = np.array(vavg_vecA)
    intavg1_vecA       = np.array(intavg1_vecA)
    intavg2_vecA       = np.array(intavg2_vecA)
    slope_intavg1_vecA = np.array(slope_intavg1_vecA)
    slope_intavg2_vecA = np.array(slope_intavg2_vecA)
    time_vecI          = np.array(time_vecI)
    vavg_vecI          = np.array(vavg_vecI)
    intavg1_vecI       = np.array(intavg1_vecI)
    intavg2_vecI       = np.array(intavg2_vecI)
    slope_intavg1_vecI = np.array(slope_intavg1_vecI)
    slope_intavg2_vecI = np.array(slope_intavg2_vecI)

    
    a = np.where(time_vecA != 0)
    i = np.where(time_vecI != 0)
    if (do_atm == True):
        print("Entering atmosphere model plot sequence...")
         
        ##### Temperatures Plots #####
        # Define the x and y data
        x    = time_vecA[a]
        var1 = vavg_vecA[a,4]    ; var1 = np.squeeze(var1)
        var2 = intavg1_vecA[a,4] ; var2 = np.squeeze(var2)
        var3 = intavg2_vecA[a,4] ; var3 = np.squeeze(var3)

        auto_t_bound = True
        y1=200
        y2=210
        a=np.squeeze(a)
        na = len(a)-1
        if auto_t_bound == True:
            if vavg_vecA[0, 4] > vavg_vecA[na, 4]:
                # cooling curve
                y1 = min(vavg_vecA[0:na, 4]) * 0.98
                y2 = min(vavg_vecA[0:na, 4]) * 1.05
            elif vavg_vecA[0, 4] <= vavg_vecA[na, 4]:
                # warming curve
                y1 = max(vavg_vecA[0:na, 4]) * 0.95
                y2 = max(vavg_vecA[0:na, 4]) * 1.02
        # Create the plot
        print('    creating temperature time series plot')
        plt.plot(x, var1, linestyle='-', color='b', label='T')
        plt.plot(x, var2, linestyle='-', color='g', label='T int1')
        plt.plot(x, var2, linestyle='-', color='r', label='T int2')
        plt.xlim([np.min(x), np.max(x)])
        plt.ylim([y1, y2])
        plt.title('Temperatures')
        plt.legend()
        plt.show()
        outfile = "plots/" + case_id +"_" + firstDate + "-" + lastDate + "_TS.eps"    
        plt.savefig(outfile)

        ##### Temperature Plot #####
        # Define the x and y data
        x    = time_vecA[a]
        var1 = slope_intavg1_vecA[a,4] ; var1 = np.squeeze(var2)
        var2 = slope_intavg2_vecA[a,4] ; var2 = np.squeeze(var3)

        auto_t_bound = True
        y1=-0.2
        y2=0.2
        a=np.squeeze(a)
        na = len(a)-1
        if auto_t_bound == True:
            y1 = min(slope_intavg1_vecA[0:na, 4]) * 0.98
            y2 = max(slope_intavg2_vecA[0:na, 4]) * 1.02

        # Create the plot
        print('    creating temperature slopes time series plot')
        plt.plot(x, var2, linestyle='-', color='g', label='T slope int1')
        plt.plot(x, var2, linestyle='-', color='r', label='T slope int2')
        plt.xlim([np.min(x), np.max(x)])
        plt.ylim([y1, y2])
        plt.title('Temperatures Slopes')
        plt.legend()
        plt.show()
        outfile = "plots/" + case_id +"_" + firstDate + "-" + lastDate + "_TS.eps"    
        plt.savefig(outfile)


        ##### Flux Plot #####
        # Define the x and y data
        x = time_vecA[a]
        var1 = vavg_vecA[a,6]-vavg_vecA[a,5]
        var2 = intavg2_vecA[a,6]-intavg2_vecA[a,5]
        var3 = vavg_vecA[a,8]-vavg_vecA[a,7] - vavg_vecA[a,9] - vavg_vecA[a,10]
        var4 = intavg2_vecA[a,8]-intavg2_vecA[a,7] - intavg2_vecA[a,9] - intavg2_vecA[a,10]

        var1 = np.squeeze(var1)
        var2 = np.squeeze(var2)
        var3 = np.squeeze(var3)
        var4 = np.squeeze(var4)

        y1=-3
        y2=1
        # Create the plot
        print('    creating net flux time series plot')
        plt.plot(x, var1, linestyle='-' , color='b', label='LW')
        plt.plot(x, var2, linestyle='--', color='b' )
        plt.plot(x, var3, linestyle='-' , color='r', label='SW')
        plt.plot(x, var4, linestyle='--', color='r')
        plt.xlim([np.min(x), np.max(x)])
        plt.ylim([y1, y2])
        plt.title('Fluxes')
        plt.legend()
        plt.show()
        outfile = "plots/" + case_id +"_" + firstDate + "-" + lastDate + "_NetFluxes.eps"    
        plt.savefig(outfile)

    i = np.where(time_vecI != 0)
    if (do_ice == True):
        print("Entering atmosphere ice plot sequence...")

        # ice internal energy
        x    = time_vecI[i]
        var1 = vavg_vecI[i,4]    ; var1 = np.squeeze(var1)
        var2 = intavg1_vecI[i,4] ; var2 = np.squeeze(var2)
        var3 = intavg2_vecI[i,4] ; var3 = np.squeeze(var3)

        auto_ie_bound = True
        y1=0
        y2=-35
        i=np.squeeze(i)
        ni = len(i)-1
        if auto_ie_bound == True:
            y1 = min(vavg_vecI[0:ni, 4]) * 1.05
            y2 = max(vavg_vecI[0:ni, 4]) * 0.95
        print(y1,y2)
        # Create the plot
        print('    creating ice energy time series plot')
        plt.plot(x, var1, linestyle='-', color='b', label='T')
        plt.plot(x, var2, linestyle='-', color='g', label='T int1')
        plt.plot(x, var2, linestyle='-', color='r', label='T int2')
        plt.xlim([np.min(x), np.max(x)])
        plt.ylim([y1, y2])
        plt.title('Ice Sheet Energy')
        plt.legend()
        plt.show()
