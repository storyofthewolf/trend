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

# input arguments and options
parser = argparse.ArgumentParser()
parser.add_argument('case_id'     , type=str,   nargs=1, default=' ',  help='Set simulation time series case name')
parser.add_argument('-y'          , type=int,   default='1', help='Start year over which to begin timeseries')
parser.add_argument('-n'          , type=int,   default='6000', help='Number of months to integrate over')
parser.add_argument('-p'          , type=int,   default='10', help='Interval for screen output, in number of months')
parser.add_argument('-a'          , type=int,   default='2',  help='Average frequency for screen output, 0:monthly, 1:yearly, 2:decadal')
parser.add_argument('--cam',        action='store_true', help='read atmosphere model data')
parser.add_argument('--cice',       action='store_true', help='read sea ice model data')
parser.add_argument('--clm',        action='store_true', help='read land model data')
parser.add_argument('--rundir',     action='store_true', help='read files from run directory instead of archive')
parser.add_argument('--plots',      action='store_true', help='do lineplots at end of sequence')
parser.add_argument('--data',       action='store_true', help='print to data file')
args = parser.parse_args()

# define case
case_id     = str(args.case_id[0])
START_YEAR  = int(args.y)
NT          = int(args.n)

# averaging interval for output
avgfreq     = int(args.a)

read_rundir   = False
if args.rundir:  read_rundir = args.rundir

# the root path to your working directory
dir = '/gpfsm/dnb53/etwolf/cesm_scratch/'

# model prefixs
prefixA = '.cam.h0.'
prefixL = '.clm2.h0.'
prefixI = '.cice.h.'

# component models activated
do_atm = False 
do_ice = False 
do_lnd = False 
if args.cam:  do_atm = True
if args.cice: do_ice = True
if args.clm:  do_lnd = True


# define time averaging intervals
# interval average 1 length
# one Earth year
int1 = 1 * 12   
# interval average 2 length
# ten Earth years
int2 = 10 * 12  
#  interval to print outputs to screen
print_int = int(args.p)


#
# read vars.in
#
atmvars_in, icevars_in, lndvars_in, atmprint_in, iceprint_in, lndprint_in, atmplot_in, iceplot_in, lndplot_in  = trend.read_request_var()

# data from atmosphere model
# include standard quartet of time and space indexes
group1d = ['time', 'lon','lat','lev']
group2d = atmvars_in
nv1dA   = len(group1d)
vnamesA = np.concatenate((group1d, group2d))
nv2dA   = len(vnamesA)  - nv1dA
nvtotA  = len(vnamesA)

# add two variables to atmosphere array if "energy" requested
# for print output
value_to_find = 'energy'
indexp = np.where(np.array(atmprint_in) == value_to_find)[0]
if len(indexp) > 0:
    nvtotA = nvtotA + 2

# data from ice model
group1d = ['time']
group2d = icevars_in
nv1dI   = len(group1d)
vnamesI = np.concatenate((group1d, group2d))
nv2dI   = len(vnamesI)  - nv1dI
nvtotI  = len(vnamesI)

# data from land model
group1d = ['time']
group2d = lndvars_in
nv1dL   = len(group1d)
vnamesL = np.concatenate((group1d, group2d))
nv2dL   = len(vnamesL)  - nv1dL
nvtotL  = len(vnamesL)

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
    ext3 = "/ice/hist"
    ext4 = "/lnd/hist"

# set root paths
root_atm = dir + ext1 + case_id + ext2
root_atm = ' '.join(root_atm.split())

root_ice = dir + ext1 + case_id + ext3
root_ice = ' '.join(root_ice.split())

root_lnd = dir + ext1 + case_id + ext4
root_lnd = ' '.join(root_lnd.split())

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
vavg_vecL = np.zeros((NT, nvtotL), dtype=float)

# time-interval averages of global mean quantities
intavg1_vecA = np.zeros((NT, nvtotA), dtype=float)       
intavg1_vecI = np.zeros((NT, nvtotI), dtype=float)
intavg1_vecL = np.zeros((NT, nvtotL), dtype=float)
intavg2_vecA = np.zeros((NT, nvtotA), dtype=float)       
intavg2_vecI = np.zeros((NT, nvtotI), dtype=float)
intavg2_vecL = np.zeros((NT, nvtotL), dtype=float)

# spatial fields for variables read in
v2dA = np.zeros((nvtotA, nlat, nlon), dtype=float)       
v2dI = np.zeros((nvtotI, nlat, nlon), dtype=float)
v2dL = np.zeros((nvtotL, nlat, nlon), dtype=float)
v3dA = np.zeros((nvtotA, nlev, nlat, nlon), dtype=float)
#v3dI = np.zeros((nvtotI, nlev, nlat, nlon), dtype=float)
#v3dL = np.zeros((nvtotL, nlev, nlat, nlon), dtype=float)

# slopes
slope_intavg1_vecA = np.zeros((NT, nvtotA), dtype=float)
slope_intavg1_vecI = np.zeros((NT, nvtotI), dtype=float)
slope_intavg1_vecL = np.zeros((NT, nvtotL), dtype=float)
slope_intavg2_vecA = np.zeros((NT, nvtotA), dtype=float)
slope_intavg2_vecI = np.zeros((NT, nvtotI), dtype=float)
slope_intavg2_vecL = np.zeros((NT, nvtotL), dtype=float)

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
if do_ice == True:
    print(prefixI)
if do_lnd == True:
    print(prefixL)

if do_atm == True:
    print("atmosphere model variables")
    print(atmvars_in)
    print("atmosphere print variables")
    print(atmprint_in)
    print("atmosphere plot variables")
    print(atmplot_in)

if do_ice == True:
    print("ice model variables")
    print(icevars_in)
    print("ice print variables")
    print(iceprint_in)
    print("ice plot variables")
    print(iceplot_in)

if do_lnd == True:
    print("land model variables")
    print(lndvars_in)
    print("land print variables")
    print(lndprint_in)
    print("land plot variables")
    print(lndplot_in)

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
firstPrintCall = True
i=0
while True:

    if (i == NT):
        # Exit loop if equals specified length
        lastDate = str(year) + '-' + month
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
        file_ice = root_ice + '/' + case_id + prefixI + '000' + str(year) + '-' + month + '.nc'
        file_lnd = root_lnd + '/' + case_id + prefixL + '000' + str(year) + '-' + month + '.nc'
    elif year >= 10 and year < 100:
        file_atm = root_atm + '/' + case_id + prefixA + '00' + str(year) + '-' + month + '.nc'
        file_ice = root_ice + '/' + case_id + prefixI + '00' + str(year) + '-' + month + '.nc'
        file_lnd = root_lnd + '/' + case_id + prefixL + '00' + str(year) + '-' + month + '.nc'
    elif year >= 100:
        file_atm = root_atm + '/' + case_id + prefixA + '0' + str(year) + '-' + month + '.nc'
        file_ice = root_ice + '/' + case_id + prefixI + '0' + str(year) + '-' + month + '.nc'
        file_lnd = root_lnd + '/' + case_id + prefixL + '0' + str(year) + '-' + month + '.nc'
    # Exit loop if there are no more files to scan through
    # I can probably condense this done to scanning 1 file set, even if its not the choosen file set
    if do_atm == True:
        file_present = os.path.isfile(file_atm)
        if file_present == False:
            lastDate = str(year) + '-' + month
            break
        time_vecA[i] = it
    if do_ice == True:
        file_present = os.path.isfile(file_ice)
        if file_present == False:
            lastDate = str(year) + '-' + month
            break
        time_vecI[i] = it
    if do_lnd == True:
        file_present = os.path.isfile(file_lnd)
        if file_present == False:
            lastDate = str(year) + '-' + month
            break
        time_vecL[i] = it
    if i == 0:
        firstDate = str(year) + '-' + month
        print("Date of first data read =", firstDate)


    #------------------------------------------------------
    # Reading files and saving data to arrays
    #-------------------------------------------------------
    if do_atm == True:
        ncid = nc.Dataset(file_atm, 'r')
        for n in range(nv1dA, nv1dA + nv2dA):
            if vnamesA[n] in ncid.variables:
                temp2D = ncid[vnamesA[n]][:]
                v2dA[n,:,:] = temp2D[0,:,:]
        ncid.close()
    if do_ice == True:
        ncid = nc.Dataset(file_ice, 'r')
        for n in range(nv1dI, nv1dI + nv2dI):
            if vnamesI[n] in ncid.variables:
                temp2D = ncid[vnamesI[n]][:]
                v2dI[n,:,:] = temp2D[0,:,:]
        ncid.close()
    if do_lnd == True:
        ncid = nc.Dataset(file_lnd, 'r')
        for n in range(nv1dL, nv1dL + nv2dL):
            if vnamesL[n] in ncid.variables:
                temp2D = ncid[vnamesL[n]][:]
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

    #-----------------------------------------------------
    # Calculate Energy Balance (if requested)
    #-----------------------------------------------------
    value_to_find = 'energy'
    indexp = np.where(np.array(atmprint_in) == value_to_find)[0]
    if len(indexp) > 0:
        if(do_atm == True):
            etop,ebot = trend.atm_energy_calc(atmvars_in, vavg_vecA[i,:])
            vavg_vecA[i,nvtotA-2] = etop
            vavg_vecA[i,nvtotA-1] = ebot


    #------------------------------------------------------
    # Time averaging and slope calculation
    #-------------------------------------------------------
    if do_atm == True:
        for n in range(nv1dA, nvtotA):            
            if (i <  int1): intavg1_vecA[i, n] = np.mean(vavg_vecA[0:i+1, n])        
            if (i >= int1): intavg1_vecA[i, n] = np.mean(vavg_vecA[i-int1:i, n])   
            if (i <  int2): intavg2_vecA[i, n] = np.mean(vavg_vecA[0:i+1, n])        
            if (i >= int2): intavg2_vecA[i, n] = np.mean(vavg_vecA[i-int2:i, n])   
            if (i <  int1): slope_intavg1_vecA[i, n] = ((intavg1_vecA[i, n] - intavg1_vecA[0, n]))/(int1/12)         
            if (i >= int1): slope_intavg1_vecA[i, n] = ((intavg1_vecA[i, n] - intavg1_vecA[i-int1, n]))/(int1/12)    
            if (i <  int2): slope_intavg2_vecA[i, n] = ((intavg2_vecA[i, n] - intavg2_vecA[0, n]))/(int2/12)         
            if (i >= int2): slope_intavg2_vecA[i, n] = ((intavg2_vecA[i, n] - intavg2_vecA[i-int2, n]))/(int2/12)    

    if do_ice == True:
        for n in range(nv1dI, nvtotI):            
            if (i <  int1): intavg1_vecI[i, n] = np.mean(vavg_vecI[0:i+1, n])        
            if (i >= int1): intavg1_vecI[i, n] = np.mean(vavg_vecI[i-int1:i, n])   
            if (i <  int2): intavg2_vecI[i, n] = np.mean(vavg_vecI[0:i+1, n])        
            if (i >= int2): intavg2_vecI[i, n] = np.mean(vavg_vecI[i-int2:i, n])   
            if (i <  int1): slope_intavg1_vecI[i, n] = ((intavg1_vecI[i, n] - intavg1_vecI[0, n]))/(int1/12)         
            if (i >= int1): slope_intavg1_vecI[i, n] = ((intavg1_vecI[i, n] - intavg1_vecI[i-int1, n]))/(int1/12)    
            if (i <  int2): slope_intavg2_vecI[i, n] = ((intavg2_vecI[i, n] - intavg2_vecI[0, n]))/(int2/12)         
            if (i >= int2): slope_intavg2_vecI[i, n] = ((intavg2_vecI[i, n] - intavg2_vecI[i-int2, n]))/(int2/12)    

    if do_lnd == True:
        for n in range(nv1dL, nvtotL):            
            if (i <  int1): intavg1_vecL[i, n] = np.mean(vavg_vecL[0:i+1, n])        
            if (i >= int1): intavg1_vecL[i, n] = np.mean(vavg_vecL[i-int1:i, n])   
            if (i <  int2): intavg2_vecL[i, n] = np.mean(vavg_vecL[0:i+1, n])        
            if (i >= int2): intavg2_vecL[i, n] = np.mean(vavg_vecL[i-int2:i, n])   
            if (i <  int1): slope_intavg1_vecL[i, n] = ((intavg1_vecL[i, n] - intavg1_vecL[0, n]))/(int1/12)         
            if (i >= int1): slope_intavg1_vecL[i, n] = ((intavg1_vecL[i, n] - intavg1_vecL[i-int1, n]))/(int1/12)    
            if (i <  int2): slope_intavg2_vecL[i, n] = ((intavg2_vecL[i, n] - intavg2_vecL[0, n]))/(int2/12)         
            if (i >= int2): slope_intavg2_vecL[i, n] = ((intavg2_vecL[i, n] - intavg2_vecL[i-int2, n]))/(int2/12)    



    #------------------------------------------------------
    # Print to screen
    #-------------------------------------------------------
    if ((i+1) % print_int == 0):  
        trend.print2screen(atmvars_in, icevars_in, lndvars_in, atmprint_in, iceprint_in, lndprint_in, firstPrintCall, avgfreq, \
                           do_atm, time_vecA[i], vavg_vecA[i,:], intavg1_vecA[i,:], intavg2_vecA[i,:], slope_intavg1_vecA[i,:], slope_intavg2_vecA[i,:], \
                           do_ice, time_vecI[i], vavg_vecI[i,:], intavg1_vecI[i,:], intavg2_vecI[i,:], slope_intavg1_vecI[i,:], slope_intavg2_vecI[i,:], \
                           do_lnd, time_vecL[i], vavg_vecL[i,:], intavg1_vecL[i,:], intavg2_vecL[i,:], slope_intavg1_vecL[i,:], slope_intavg2_vecL[i,:], \
                           i)
        firstPrintCall = False 
    i=i+1
#-----------------------------------------------------------------------------------------------------------------
# end loop over files
#-----------------------------------------------------------------------------------------------------------------
print("Concluding             ", case_id)
print("Number of files read:  ", i)
print("End date (year-month): ", lastDate)


#------------------------------------------------------
# Print data to text file
#-------------------------------------------------------    
if args.data == True:
  print('Printing to text file...')
  trend.print2text(do_atm, vnamesA, time_vecA, vavg_vecA, intavg1_vecA, intavg2_vecA, slope_intavg1_vecA, slope_intavg2_vecA, \
                   do_ice, vnamesI, time_vecI, vavg_vecI, intavg1_vecI, intavg2_vecI, slope_intavg1_vecI, slope_intavg2_vecI, \
                   firstDate, lastDate, case_id)

#------------------------------------------------------
# Call line plotting script
#-------------------------------------------------------
if args.plots == True:
  print('Plotting...')
  trend.timeSeriesPlots(atmvars_in, lndvars_in, icevars_in, atmplot_in, lndplot_in, iceplot_in, \
                        do_atm, time_vecA, vavg_vecA, intavg1_vecA, intavg2_vecA, slope_intavg1_vecA, slope_intavg2_vecA, \
                        do_ice, time_vecI, vavg_vecI, intavg1_vecI, intavg2_vecI, slope_intavg1_vecI, slope_intavg2_vecI, \
                        do_lnd, time_vecL, vavg_vecL, intavg1_vecL, intavg2_vecL, slope_intavg1_vecL, slope_intavg2_vecL, \
                        firstDate, lastDate, case_id)

sys.exit()
