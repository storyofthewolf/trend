#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# trend.py
#
# Author Eric Wolf
# May 2023
#
# Purpose:  Analyze time-series data from NCAR CESM simulations. 
#           Used for evalulating time-dependent trends, energy balance, 
#           hydrological cycle balance, and equilibrium acceleration 
#           approaches.  
#
# Notes:    Presently it only works with monthly mean outputs (nhtfrq=0).
#           
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


import netCDF4 as nc
import numpy   as np
import os
import sys
import exocampy_tools  as exo
import trend_utils as trend
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('case_id'     , type=str,   nargs=1, default=' ',  help='Set simulation time series case name')
parser.add_argument('-y'          , type=float, default='1', help='Start year over which to loop timeseries')
parser.add_argument('-n'          , type=int,   default='6000', help='Number of months to integrate over')
parser.add_argument('-p'          , type=int,   default='10', help='Interval for screen output, in number of months')
parser.add_argument('--cam',        action='store_true', help='read atmosphere model data')
parser.add_argument('--cice',       action='store_true', help='read sea ice model data')
parser.add_argument('--clm',        action='store_true', help='read land model data')
parser.add_argument('--rundir',     action='store_true', help='read files from run directory instead of archive')
parser.add_argument('--noplots',    action='store_true', help='do not do lineplots at end of sequence')
parser.add_argument('--print2data', action='store_true', help='print to data file')
args = parser.parse_args()

# define case
case_id     = str(args.case_id[0])
START_YEAR  = int(args.y)
NT          = int(args.n)

read_rundir   = False
if args.rundir:  read_rundir = args.rundir

dir = '/gpfsm/dnb53/etwolf/cesm_scratch/'

# model prefixs
prefixA = '.cam.h0.'
prefixL = '.clm2.h0.'
prefixI = '.cice.h.'

# component models activated
do_atm = False 
do_ice = False 
do_lnd = False 
if args.cam: do_atm = True
if args.cice: do_ice = True
if args.clm:  do_lnd = True

# external functions
do_line_plot = True

# define time averaging intervals
# interval average 1 length
# one Earth year
int1 = 1 * 12   
# interval average 2 length
# ten Earth years
int2 = 10 * 12  
#  interval to print outputs to screen
print_int = int(args.p)


# Select variables to read

# modularize into packages, "2D energy", "Surface Ice", "T-structure"
# packages would include vars.in --> screen_outputs ---> plots, printing
#    all correlated for the package variables.  then there would be a custom option.
#    packages (2D energy) T, Tavg, net TOA, net Surface, dT/dt, dF/dt


# read variables strings from namelist file
atmvars_in, icevars_in = trend.read_request_var(do_atm, do_ice)

# data from atmosphere model
group1d = ['time', 'lon','lat','lev']
group2d = atmvars_in
nv1dA   = len(group1d)
vnamesA = np.concatenate((group1d, group2d))
nv2dA   = len(vnamesA)  - nv1dA
nvtotA  = len(vnamesA)

# data from ice model
group1d = ['time']
group2d = icevars_in
nv1dI   = len(group1d)
vnamesI = np.concatenate((group1d, group2d))
nv2dI   = len(vnamesI)  - nv1dI
nvtotI  = len(vnamesI)

#-----------------------------------------------------------------------------------------------------------------
# End User Specification Section
#-----------------------------------------------------------------------------------------------------------------

# Determine the root path based on CESM standard for
# $RUNDIR and $ARCHIVEDIR
if (read_rundir  == True):
    ext1 = "rundir/"
    ext2 = "/run"
    ext3 = "/run"
    ext4 = "/run"
else:
    ext1 = "archive/"
    ext2 = "/atm/hist"
    ext3 = "/lnd/hist"
    ext4 = "/ice/hist"

# set root paths
root_atm = dir + ext1 + case_id + ext2
root_atm = ' '.join(root_atm.split())

root_lnd = dir + ext1 + case_id + ext3
root_lnd = ' '.join(root_lnd.split())

root_ice = dir + ext1 + case_id + ext4
root_ice = ' '.join(root_ice.split())

#------------------------------------------
# Peak in first file to get lon, lat, lev
#------------------------------------------
if START_YEAR < 10:
    file_atm = root_atm + '/' + case_id + '.cam.h0.' + '000' + str(START_YEAR) + '-01.nc'
elif START_YEAR >= 10 and START_YEAR < 100:
    file_atm = root_atm + '/' + case_id + '.cam.h0.' + '00'  + str(START_YEAR) + '-01.nc'
elif START_YEAR >= 100:
    file_atm = root_atm + '/' + case_id + '.cam.h0.' + '0'   + str(START_YEAR) + '-01.nc'

ncid = nc.Dataset(file_atm, 'r')
lon = ncid.variables['lon'][:]
nlon = lon.size
lat = ncid.variables['lat'][:]
nlat = lat.size
lev = ncid.variables['lev'][:]
nlev = lev.size
ncid.close()


#------------------------------------------------------
# Define data arrays based on user inputs
#-------------------------------------------------------
# time vectors 
time_vecA = np.zeros(NT, dtype=float)                    
time_vecI = np.zeros(NT, dtype=float)
time_vecL = np.zeros(NT, dtype=float)

# global mean variables in time series
vavg_vecA = np.zeros((NT, nvtotA), dtype=float)          
vavg_vecI = np.zeros((NT, nvtotI), dtype=float)

# time-interval averages of global mean quantities
intavg1_vecA = np.zeros((NT, nvtotA), dtype=float)       
intavg1_vecI = np.zeros((NT, nvtotI), dtype=float)
intavg2_vecA = np.zeros((NT, nvtotA), dtype=float)       
intavg2_vecI = np.zeros((NT, nvtotI), dtype=float)

# spatial fields for variables read in
v2dA = np.zeros((nvtotA, nlat, nlon), dtype=float)       
v2dI = np.zeros((nvtotI, nlat, nlon), dtype=float)
v3dA = np.zeros((nvtotA, nlev, nlat, nlon), dtype=float)
v3dI = np.zeros((nvtotI, nlev, nlat, nlon), dtype=float)

# slopes
slope_intavg1_vecA = np.zeros((NT, nvtotA), dtype=float)
slope_intavg1_vecI = np.zeros((NT, nvtotI), dtype=float)
slope_intavg2_vecA = np.zeros((NT, nvtotA), dtype=float)
slope_intavg2_vecI = np.zeros((NT, nvtotI), dtype=float)

#------------------------------------------------------
# Print setup information to screen
#-------------------------------------------------------
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("~~~~~~~~~~~~~~~~~ ExoCAM trend analysis ~~~~~~~~~~~~~~~~")
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("=== File series descriptors ===")
print(case_id, " ", START_YEAR, " ", ext1)
if do_atm == False and do_ice == False and do_lnd == False: 
    print("must choose a source model; cam, cice, clm")
    quit()
if do_atm == True:
    print(prefixA)
if do_lnd == True:
    print(prefixL)
if do_ice == True:
    print(prefixI)

if do_atm == True:
    print("atmosphere model variables")
    print(atmvars_in)
    #print(nv2dA, nv1dA, nvtotA)
    #print(vnamesA)

if do_ice == True:
    print("ice model variables")
    print(icevars_in)
    #print(nv2dI, nv1dI, nvtotI)
    #print(vnamesI)

print("=== Resolution ===");
print("nlon  ", nlon)
print("nlat  ", nlat)
print("nlev  ", nlev)

print("========================================")
print("=========  starting time loop  =========")
print("========================================")
#-----------------------------------------------------------------------------------------------------------------
# Loop over file series
#-----------------------------------------------------------------------------------------------------------------
i=0
while True:
    if (i == NT):
        # Exit loop if equals specified length
        lastDate = str(year) + '-' + month
        print("Date of last data read =", lastDate)
        break

    it = i + 1
    yr_count = (it - 1) // 12
    month_i = it - (yr_count * 12)
    year = START_YEAR + yr_count
    if month_i <= 9:
        month = '0' + str(month_i)
        month = ''.join(month.split())
    elif month_i >= 10:
        month = str(month_i)

    if year < 10:
        file_atm = root_atm + '/' + case_id + prefixA + '000' + str(year) + '-' + month + '.nc'
        file_lnd = root_lnd + '/' + case_id + prefixL + '000' + str(year) + '-' + month + '.nc'
        file_ice = root_ice + '/' + case_id + prefixI + '000' + str(year) + '-' + month + '.nc'
    elif year >= 10 and year < 100:
        file_atm = root_atm + '/' + case_id + prefixA + '00' + str(year) + '-' + month + '.nc'
        file_lnd = root_lnd + '/' + case_id + prefixL + '00' + str(year) + '-' + month + '.nc'
        file_ice = root_ice + '/' + case_id + prefixI + '00' + str(year) + '-' + month + '.nc'
    elif year >= 100:
        file_atm = root_atm + '/' + case_id + prefixA + '0' + str(year) + '-' + month + '.nc'
        file_lnd = root_lnd + '/' + case_id + prefixL + '0' + str(year) + '-' + month + '.nc'
        file_ice = root_ice + '/' + case_id + prefixI + '0' + str(year) + '-' + month + '.nc'

    # Exit loop if there are no more files to scan through
    # I can probably condense this done to scanning 1 file set, even if its not the choosen file set
    if do_atm == True:
        file_present = os.path.isfile(file_atm)
        if file_present == False:
            lastDate = str(year) + '-' + month
            print("Date of last data read =", lastDate)
            break
        time_vecA[i] = it
    if do_lnd == True:
        file_present = os.path.isfile(file_lnd)
        if file_present == 0:
            lastDate = str(year) + '-' + month
            print("Date of last data read =", lastDate)
            break
        time_vecL[i] = it
    if do_ice == True:
        file_present = os.path.isfile(file_ice)
        if file_present == 0:
            lastDate = str(year) + '-' + month
            print("Date of last data read =", lastDate)
            break
        time_vecI[i] = it

    if i == 0:
        firstDate = str(year) + '-' + month
        print("Date of first data read =", firstDate)



    #------------------------------------------------------
    # Reading files and saving data to arrays
    #-------------------------------------------------------
    if do_atm == True:
        ncid = nc.Dataset(file_atm, 'r')
        for n in range(nv1dA, nv1dA + nv2dA):
            temp2D = ncid[vnamesA[n]][:]
#            temp2D = temp2D.transpose((2,1,0))
            v2dA[n,:,:] = temp2D[0,:,:]
        ncid.close()
    if do_ice == True:
        ncid = nc.Dataset(file_ice, 'r')
        for n in range(nv1dI, nv1dI + nv2dI):
            temp2D = ncid[vnamesI[n]][:]
#            temp2D = temp2D.transpose((2,1,0))
            v2dI[n,:,:] = temp2D[0,:,:]
        ncid.close()
    if do_lnd == True:
        ncid = nc.Dataset(file_lnd, 'r')
        for n in range(nv1dL, nv1dL + nv2dL):
            temp2D = ncid[vnamesL[n]][:]
#            temp2D = temp2D.transpose((2,1,0))
            v2dL[n,:,:] = temp2D[0,:,:]
        ncid.close()


    #------------------------------------------------------
    # Area Weighted Averaging
    #-------------------------------------------------------
    if do_atm == True:
        for n in range(nv1dA, nv1dA + nv2dA):
            temp2d = v2dA[n, :, :]
            temp_avg = exo.area_weighted_avg(lon, lat, temp2d)
            vavg_vecA[i, n] = temp_avg
    if do_ice == True:
        for n in range(nv1dI, nv1dI + nv2dI):
            temp2d = v2dI[n, :, :]
            temp_avg = exo.area_weighted_avg(lon, lat, temp2d)
            vavg_vecI[i, n] = temp_avg
    if do_lnd == True:
        for n in range(nv1dL, nv1dL + nv2dL):
            temp2d = v2dL[n, :, :]
            temp_avg = exo.area_weighted_avg(lon, lat, temp2d)
            vavg_vecL[i, n] = temp_avg

    #------------------------------------------------------
    # Time averaging and slope calculation
    #-------------------------------------------------------
    if do_atm == 1:
        for n in range(nv1dA, nv1dA+nv2dA):            
            if (i <  int1): intavg1_vecA[i, n] = np.mean(vavg_vecA[0:i+1, n])        
            if (i >= int1): intavg1_vecA[i, n] = np.mean(vavg_vecA[i-int1:i, n])   
            if (i <  int2): intavg2_vecA[i, n] = np.mean(vavg_vecA[0:i+1, n])        
            if (i >= int2): intavg2_vecA[i, n] = np.mean(vavg_vecA[i-int2:i, n])   
            if (i <  int1): slope_intavg1_vecA[i, n] = ((intavg1_vecA[i, n] - intavg1_vecA[0, n]))/(int1/12)         
            if (i >= int1): slope_intavg1_vecA[i, n] = ((intavg1_vecA[i, n] - intavg1_vecA[i-int1, n]))/(int1/12)    
            if (i <  int2): slope_intavg2_vecA[i, n] = ((intavg2_vecA[i, n] - intavg2_vecA[0, n]))/(int2/12)         
            if (i >= int2): slope_intavg2_vecA[i, n] = ((intavg2_vecA[i, n] - intavg2_vecA[i-int2, n]))/(int2/12)    

    if do_ice == 1:
        for n in range(nv1dI, nv1dI+nv2dI):            
            if (i <  int1): intavg1_vecI[i, n] = np.mean(vavg_vecI[0:i+1, n])        
            if (i >= int1): intavg1_vecI[i, n] = np.mean(vavg_vecI[i-int1:i, n])   
            if (i <  int2): intavg2_vecI[i, n] = np.mean(vavg_vecI[0:i+1, n])        
            if (i >= int2): intavg2_vecI[i, n] = np.mean(vavg_vecI[i-int2:i, n])   
            if (i <  int1): slope_intavg1_vecI[i, n] = ((intavg1_vecI[i, n] - intavg1_vecI[0, n]))/(int1/12)         
            if (i >= int1): slope_intavg1_vecI[i, n] = ((intavg1_vecI[i, n] - intavg1_vecI[i-int1, n]))/(int1/12)    
            if (i <  int2): slope_intavg2_vecI[i, n] = ((intavg2_vecI[i, n] - intavg2_vecI[0, n]))/(int2/12)         
            if (i >= int2): slope_intavg2_vecI[i, n] = ((intavg2_vecI[i, n] - intavg2_vecI[i-int2, n]))/(int2/12)    



    #------------------------------------------------------
    # Print to screen
    #-------------------------------------------------------
    if ((i+1) % print_int == 0):  
        trend.print2screen(do_atm, time_vecA[i], vavg_vecA[i,:], intavg1_vecA[i,:], intavg2_vecA[i,:], slope_intavg1_vecA[i,:], slope_intavg2_vecA[i,:], \
                           do_ice, time_vecI[i], vavg_vecI[i,:], intavg1_vecI[i,:], intavg2_vecI[i,:], slope_intavg1_vecI[i,:], slope_intavg2_vecI[i,:], i)
 
    i=i+1
#-----------------------------------------------------------------------------------------------------------------
# end loop over files
#-----------------------------------------------------------------------------------------------------------------
print("Last files read: ")
if (do_atm == True): print(file_atm)
if (do_ice == True): print(file_ice)
if (do_lnd == True): print(file_lnd)


#------------------------------------------------------
# Print data to text file
#-------------------------------------------------------    
if args.print2data == True:
  print('Printing to text file')
  trend.print2text(do_atm, vnamesA, time_vecA, vavg_vecA, intavg1_vecA, intavg2_vecA, slope_intavg1_vecA, slope_intavg2_vecA, \
                   do_ice, vnamesI, time_vecI, vavg_vecI, intavg1_vecI, intavg2_vecI, slope_intavg1_vecI, slope_intavg2_vecI, \
                   firstDate, lastDate, case_id)

#------------------------------------------------------
# Call line plotting script
#-------------------------------------------------------
if args.noplots == True:
  print('Plotting routine skipped per --noplots option')
else:
  trend.timeSeriesPlots(do_atm, time_vecA, vavg_vecA, intavg1_vecA, intavg2_vecA, slope_intavg1_vecA, slope_intavg2_vecA, \
                        do_ice, time_vecI, vavg_vecI, intavg1_vecI, intavg2_vecI, slope_intavg1_vecI, slope_intavg2_vecI, \
                        firstDate, lastDate, case_id)



