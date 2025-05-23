#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# trend_utils.py
#
#  Author: Wolf, E.T.
#
#  Contains functions for reading namelist (vars.in), 
#  screen output, text outputs, and runtime plotting
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import sys
import matplotlib.pyplot as plt
import numpy as np

# global variable settings
# offset for variable read in. value of 4 for lon, lat, lev, time
atm_vars_offset = 4 
ice_vars_offset = 1
auto_t_bound = True    # automatically set the temperature plot y-axis
auto_e_bound = True    # automatically set the energy balance y-axis

# manually set energy plot bounds if desired
ey1 = -3.0
ey2 = 3.0
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# // read_request_var //
# script to read in text files containing the string-type variable
# names requeted from the models.  lon, lat, lev, time ar always included and thus hardcoded.
# file out one formated text file. atm, lnd, ice
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def read_request_var():

    with open('vars.in', 'r') as f:
        
        blank1   = f.readline()
        atmRstr  = f.readline()
        atmRvars = atmRstr.split()
        iceRstr  = f.readline()
        iceRvars = iceRstr.split()
        lndRstr  = f.readline()
        lndRvars = lndRstr.split()

        blank2   = f.readline()
        atmPstr  = f.readline()
        atmPvars = atmPstr.split()
        icePstr  = f.readline()
        icePvars = icePstr.split()
        lndPstr  = f.readline()
        lndPvars = lndPstr.split()

        blank3    = f.readline()
        atmPLstr  = f.readline()
        atmPLvars = atmPLstr.split()
        icePLstr  = f.readline()
        icePLvars = icePLstr.split()
        lndPLstr  = f.readline()
        lndPLvars = lndPLstr.split()

    # atm error checking
    for var in atmPvars:
        if (var != 'energy'):
            indexr = np.where(np.array(atmRvars) == var)[0]
            if (indexr >= 0):
                pass
            else:
                print("ERROR: ",var, " requested to print, not on variable list")
                sys.exit()

    for var in atmPLvars:
        if (var != 'energy'):
            indexr = np.where(np.array(atmRvars) == var)[0]
            if (indexr >= 0):
                pass
            else:
                print("ERROR: ",var, " requested to plot, not on variable list")
                sys.exit()

    # ice error checking
    for var in icePvars:
        if (var != 'energy'):
            indexr = np.where(np.array(iceRvars) == var)[0]
            if (indexr >= 0):
                pass
            else:
                print("ERROR: ",var, " requested to print, not on variable list")
                sys.exit()

    for var in icePLvars:
        if (var != 'energy'):
            indexr = np.where(np.array(iceRvars) == var)[0]
            if (indexr >= 0):
                pass
            else:
                print("ERROR: ",var, " requested to plot, not on variable list")
                sys.exit()

    # lnd error checking
    for var in lndPvars:
        if (var != 'energy'):
            indexr = np.where(np.array(lndRvars) == var)[0]
            if (indexr >= 0):
                pass
            else:
                print("ERROR: ",var, " requested to print, not on variable list")
                sys.exit()

    for var in lndPLvars:
        if (var != 'energy'):
            indexr = np.where(np.array(lndRvars) == var)[0]
            if (indexr >= 0):
                pass
            else:
                print("ERROR: ",var, " requested to plot, not on variable list")
                sys.exit()
         
    return atmRvars, iceRvars, lndRvars, atmPvars, icePvars, lndPvars, atmPLvars, icePLvars, lndPLvars


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# // print2screen //
# prints text to screen for running output
# not saved
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def print2screen(atmvars_in, icevars_in, lndvars_in, atmprint_in, iceprint_in, lndprint_in, firstCall, avgfreq, \
                 do_atm, time_vecA, vavg_vecA, intavg1_vecA, intavg2_vecA, slope_intavg1_vecA, slope_intavg2_vecA, \
                 do_ice, time_vecI, vavg_vecI, intavg1_vecI, intavg2_vecI, slope_intavg1_vecI, slope_intavg2_vecI, \
                 do_lnd, time_vecL, vavg_vecL, intavg1_vecL, intavg2_vecL, slope_intavg1_vecL, slope_intavg2_vecL, \
                 i):
  
    print_offset = 0
    if (avgfreq == 0): print_offset = 2
    if (avgfreq == 1): print_offset = 1
    if (avgfreq == 2): print_offset = 0

    i=i+1
    if (i <  10): istr = '    '
    if (i >= 10):  istr = '   '
    if (i >= 100):  istr = '  '
    if (i >= 1000):  istr = ' '
    if (i >= 10000):  istr = ''

    # contains all data read in
    atmout       = np.zeros(1, dtype=int)  
    iceout       = np.zeros(1, dtype=int)  
    lndout       = np.zeros(1, dtype=int)  
    # contains only the data to print to screen
    atmprint_out = np.zeros(1, dtype=int)  
    iceprint_out = np.zeros(1, dtype=int)  
    lndprint_out = np.zeros(1, dtype=int)  

    if (do_atm == True): 

        # include everything else in a general loop
        for var in atmprint_in:
            if (var != 'energy'): 
                indexr = np.where(np.array(atmvars_in) == var)[0]
                if (indexr >= 0):
                    xi = indexr + atm_vars_offset
                    temp = np.array([vavg_vecA[xi], intavg1_vecA[xi], intavg2_vecA[xi]])
                    temp = np.squeeze(temp)
                    atmout[0] = i
                    atmout = np.hstack((atmout, temp)).flatten()
                    atmout = np.squeeze(atmout)

        # energy goes at the end
        value_to_find = 'energy'
        indexr = np.where(np.array(atmprint_in) == value_to_find)[0]
        if (indexr > 0):
            N = len(vavg_vecA)
            xi = N-1
            temp = np.array([vavg_vecA[xi], intavg1_vecA[xi], intavg2_vecA[xi]])
            temp = np.squeeze(temp)
            atmout = np.hstack((atmout, temp)).flatten()
            atmout = np.squeeze(atmout)
            xi = N-2
            temp = np.array([vavg_vecA[xi], intavg1_vecA[xi], intavg2_vecA[xi]])
            temp = np.squeeze(temp)
            atmout = np.hstack((atmout, temp)).flatten()
            atmout = np.squeeze(atmout)       

        if (firstCall == True):                  
            format_string = "{%s}"
            print("i     ", end=' ',flush=True)
            for x in atmprint_in:
                print(x, end='   ',flush=True)
            print()        
         
        # Define the desired formatting
        format_string = "{:.3f}"
        
        print(int(atmout[0]), end='  ',flush=True)
        N=len(atmout)
        for x in range(int((N-1)/3)):
            y=int(3*(x+1)-print_offset)
            print(format_string.format(atmout[y]), end='  ',flush=True)
        print()


    if (do_ice == True):       

        # include everything else in a general loop
        for var in iceprint_in:
            if (var != 'energy'): 
                indexr = np.where(np.array(icevars_in) == var)[0]
                if (indexr >= 0):
                    xi = indexr + ice_vars_offset
                    temp = np.array([vavg_vecI[xi], intavg1_vecI[xi], intavg2_vecI[xi]])
                    temp = np.squeeze(temp)
                    iceout[0] = i
                    iceout = np.hstack((iceout, temp)).flatten()
                    iceout = np.squeeze(iceout)

        if (firstCall == True):
            format_string = "{%s}"
            print("i  ", end=' ',flush=True)
            for x in iceprint_in:
                print(x, end=' ',flush=True)
            print()


        # Define the desired formatting
        format_string = "{:.3f}"
        
        print(int(iceout[0]), end='  ',flush=True)
        N=len(iceout)
        for x in range(int((N-1)/3)):
            y=int(3*(x+1)-print_offset)
            print(format_string.format(iceout[y]), end='  ',flush=True)
        print()


    if (do_lnd == True): 
        # include everything else in a general loop
        for var in lndprint_in:
            if (var != 'energy'): 
                indexr = np.where(np.array(lndvars_in) == var)[0]
                if (indexr >= 0):
                    xi = indexr + lnd_vars_offset
                    temp = np.array([vavg_vecL[xi], intavg1_vecL[xi], intavg2_vecL[xi]])
                    temp = np.squeeze(temp)
                    lndout[0] = i
                    lndout = np.hstack((iceout, temp)).flatten()
                    lndout = np.squeeze(iceout)

        # Define the desired formatting
        format_string = "{:.3f}"
        
        print(int(lndout[0]), end='  ',flush=True)
        N=len(lndout)
        for x in range(int((N-1)/3)):
            y=int(3*(x+1)-print_offset)
            print(format_string.format(lndout[y]), end='  ',flush=True)
        print()

    return
 

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# // print2text //
# prints output data to text file
# text file outputs are verbose, i.e. instaneous, 1 year, and
# 10 year average are plotted for each variable
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def print2text(atmvars_in, lndvars_in, icevars_in, atmprint_in, lndprint_in, iceprint_in, \
               do_atm, vnamesA, time_vecA, vavg_vecA, intavg1_vecA, intavg2_vecA, slope_intavg1_vecA, slope_intavg2_vecA, \
               do_ice, vnamesI, time_vecI, vavg_vecI, intavg1_vecI, intavg2_vecI, slope_intavg1_vecI, slope_intavg2_vecI, \
               do_lnd, vnamesL, time_vecL, vavg_vecL, intavg1_vecL, intavg2_vecL, slope_intavg1_vecL, slope_intavg2_vecL, \
               firstDate, lastDate, case_id):

    a = np.where(time_vecA != 0)
    a = np.squeeze(a)
    na = len(a)-1

    if (do_atm == True):
        outfile = "data/" + case_id +"_" + firstDate + "-" + lastDate + "_cam.txt"
        if (do_atm == True):
            with open(outfile,"w") as f:
                for i in time_vecA[0:na]:
                    i=int(i)
                    # sort out printing variables
                    print(i, vavg_vecA[i,4], file=f)



#if (firstCall == True):
#            format_string = "{%s}"
#            print("i  ", end=' ',flush=True)
#            for x in atmprint_in:
#                print(x, end=' ',flush=True)
#            print()
#
#        # Define the desired formatting
#
#        format_string = "{:.3f}"
#
#        print(int(atmout[0]), end='  ',flush=True)
#        N=len(atmout)
#        for x in range(int((N-1)/3)):
#            y=int(3*(x+1)-print_offset)
#            print(format_string.format(atmout[y]), end='  ',flush=True)
#        print()
#


#  for var in atmprint_in:
#            if (var != 'energy'):
#                indexr = np.where(np.array(atmvars_in) == var)[0]
#                if (indexr >= 0):
#                    xi = indexr + vars_offset


    if (do_ice == True):
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
def timeSeriesPlots(atmvars_in, lndvars_in, icevars_in, atmplot_in, lndplot_in, iceplot_in, \
                    do_atm, time_vecA, vavg_vecA, intavg1_vecA, intavg2_vecA, slope_intavg1_vecA, slope_intavg2_vecA, \
                    do_ice, time_vecI, vavg_vecI, intavg1_vecI, intavg2_vecI, slope_intavg1_vecI, slope_intavg2_vecI, \
                    do_lnd, time_vecL, vavg_vecL, intavg1_vecL, intavg2_vecL, slope_intavg1_vecL, slope_intavg2_vecL, \
                    firstDate, lastDate, case_id):
#!! routine is incomplete !!
#!! needs land and ice model plotting !!

    if (do_atm == True):
        print("Entering atmosphere model plot sequence...")
        a   = np.where(time_vecA != 0) 
        a   = np.squeeze(a)
        na  = len(a)-1     

        # include everything else in a general loop
        for var in atmplot_in:
            print(var)
            if (var != 'energy'):
                indexr = np.where(np.array(atmvars_in) == var)[0]
                if (indexr >= 0):
                    xa = indexr + atm_vars_offset
                    x    = time_vecA[a]
                    var1 = vavg_vecA[a,xa]    ; var1 = np.squeeze(var1)
                    var2 = intavg1_vecA[a,xa] ; var2 = np.squeeze(var2)
                    var3 = intavg2_vecA[a,xa] ; var3 = np.squeeze(var3)

                    if auto_t_bound == True:
                        if intavg2_vecA[0, xa] > intavg2_vecA[na, xa]:
                        # decreasing curve
                            y1 = min(intavg2_vecA[0:na, xa]) * 0.98
                            y2 = min(intavg2_vecA[0:na, xa]) * 1.05
                        elif intavg2_vecA[0, xa] <= intavg2_vecA[na, xa]:
                        # increasing curve
                            y1 = max(intavg2_vecA[0:na, xa]) * 0.95
                            y2 = max(intavg2_vecA[0:na, xa]) * 1.02
                    else:
                        # set your own limits, however these won't be correct for every variable
                        y1=0
                        y2=100
                    plt.plot(x, var1, linestyle='-', color='b', label='monthly avg')
                    plt.plot(x, var2, linestyle='-', color='g', label='1 year avg')
                    plt.plot(x, var3, linestyle='-', color='r', label='10 year avg')
                    plt.xlim([np.min(x), np.max(x)])
                    plt.ylim([y1, y2])
                    plt.title(var)
                    plt.legend()
                    plt.show()

            # energy balance is a special case
            if (var == 'energy'):
                x    = time_vecA[a]
                N = len(vavg_vecA[0,:])
                xa = N-1                
                var1 = vavg_vecA[a,xa]    ; var1 = np.squeeze(var1)
                var2 = intavg1_vecA[a,xa] ; var2 = np.squeeze(var2)
                var3 = intavg2_vecA[a,xa] ; var3 = np.squeeze(var3)
                xa = N-2
                var4 = vavg_vecA[a,xa]    ; var4 = np.squeeze(var4)
                var5 = intavg1_vecA[a,xa] ; var5 = np.squeeze(var5)
                var6 = intavg2_vecA[a,xa] ; var6 = np.squeeze(var6)

                # found some cases where this isn't working properly                
                if auto_e_bound == True:
                    bottom_arr = [var1, var2, var3, var4, var5, var6]
                    top_arr = [var1, var2, var3, var4, var5, var6]
                    y11 = np.minimum.reduce(bottom_arr)
                    y22 = np.maximum.reduce(top_arr)
                    y1  = np.minimum.reduce(y11)
                    y2  = np.maximum.reduce(y22)
                else:      
                    # set your own limits
                    y1=ey1
                    y2=ey2

                plt.plot(x, var1, linestyle='-', color='b', label='monthly avg')
                plt.plot(x, var2, linestyle='-', color='g', label='1 year avg')
                plt.plot(x, var3, linestyle='-', color='r', label='10 year avg')

                plt.plot(x, var4, linestyle='--', color='b', label='monthly avg')
                plt.plot(x, var5, linestyle='--', color='g', label='1 year avg')
                plt.plot(x, var6, linestyle='--', color='r', label='10 year avg')

                plt.xlim([np.min(x), np.max(x)])
                plt.ylim([y1, y2])
                plt.title(var)
                plt.legend()
                plt.show()


    if (do_ice == True):
        print("Entering ice model plot sequence...")
        a   = np.where(time_vecI != 0) 
        a   = np.squeeze(a)
        na  = len(a)-1     

        # include everything else in a general loop
        for var in iceplot_in:
            print(var)
            indexr = np.where(np.array(icevars_in) == var)[0]
            if (indexr >= 0):
                xa = indexr + ice_vars_offset
                x    = time_vecI[a]
                var1 = vavg_vecI[a,xa]    ; var1 = np.squeeze(var1)
                var2 = intavg1_vecI[a,xa] ; var2 = np.squeeze(var2)
                var3 = intavg2_vecI[a,xa] ; var3 = np.squeeze(var3)

                if auto_t_bound == True:
                    if intavg2_vecI[0, xa] > intavg2_vecI[na, xa]:
                    # decreasing curve
                        y1 = min(intavg2_vecI[0:na, xa]) * 0.98
                        y2 = min(intavg2_vecI[0:na, xa]) * 1.05
                    elif intavg2_vecA[0, xa] <= intavg2_vecA[na, xa]:
                     # increasing curve
                        y1 = max(intavg2_vecI[0:na, xa]) * 0.95
                        y2 = max(intavg2_vecI[0:na, xa]) * 1.02
                else:
                    # set your own limits, however these won't be correct for every variable
                    y1=0
                    y2=100
                plt.plot(x, var1, linestyle='-', color='b', label='monthly avg')
                plt.plot(x, var2, linestyle='-', color='g', label='1 year avg')
                plt.plot(x, var3, linestyle='-', color='r', label='10 year avg')
                plt.xlim([np.min(x), np.max(x)])
                plt.ylim([y1, y2])
                plt.title(var)
                plt.legend()
                plt.show()

            

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# // atm_energy_calc //
# calculate atmosphere model energy balance from primary vars
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def atm_energy_calc(atmvars, vavg_vecA):

    value_to_find = 'FSNT'
    indexr = np.where(np.array(atmvars) == value_to_find)[0]
    xfsnt = indexr + atm_vars_offset
    if len(indexr) == 0: print("Error: FSNT required for energy calc")

    value_to_find = 'FLNT'
    indexr = np.where(np.array(atmvars) == value_to_find)[0]
    xflnt = indexr + atm_vars_offset
    if len(indexr) == 0: print("Error: FLNT required for energy calc")

    value_to_find = 'FSNS'
    indexr = np.where(np.array(atmvars) == value_to_find)[0]
    xfsns = indexr + atm_vars_offset
    if len(indexr) == 0: print("Error: FSNS required for energy calc")

    value_to_find = 'FLNS'
    indexr = np.where(np.array(atmvars) == value_to_find)[0]
    xflns = indexr + atm_vars_offset
    if len(indexr) == 0: print("Error: FLNS required for energy calc")

    value_to_find = 'LHFLX'
    indexr = np.where(np.array(atmvars) == value_to_find)[0]
    xlhflx = indexr + atm_vars_offset
    if len(indexr) == 0: print("Error: LHFLX required for energy calc")

    value_to_find = 'SHFLX'
    indexr = np.where(np.array(atmvars) == value_to_find)[0]
    xshflx = indexr + atm_vars_offset
    if len(indexr) == 0: print("Error: SHFLX required for energy calc")

    etop = np.array( [vavg_vecA[xfsnt]-vavg_vecA[xflnt] ])
    etop = np.squeeze(etop)

    ebot = np.array( [vavg_vecA[xfsns]-vavg_vecA[xflns] - vavg_vecA[xlhflx] - vavg_vecA[xshflx] ])
    ebot = np.squeeze(ebot)
  
    return etop, ebot
