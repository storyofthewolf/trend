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
import time
import trend_utils as trend
import trend_core  as core
import argparse

def print_timing(label, elapsed):
    print(f"  {label:<40} {elapsed:6.1f}s")

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
# dir = '/discover/nobackup/tfauchez/cesm_scratch/'

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
energy_requested = len(indexp) > 0
if energy_requested:
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
timing = {}
print("========================================")
print("=========  file peek               ======")
print("========================================")
t0 = time.time()

file_atm = f"{root_atm}/{case_id}.cam.h0.{START_YEAR:04d}-01.nc"

ncid = nc.Dataset(file_atm, 'r')
lon = ncid.variables['lon'][:]
nlon = lon.size
lat = ncid.variables['lat'][:]
nlat = lat.size
lev = ncid.variables['lev'][:]
nlev = lev.size
ncid.close()

timing['file peek'] = time.time() - t0
print_timing('file peek', timing['file peek'])


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

#-----------------------------------------------------------------------------------------------------------------
# File scan: determine N_actual, populate time vectors and date strings
# No data is read here; this pass only checks file existence.
#-----------------------------------------------------------------------------------------------------------------
print("========================================")
print("=========  scanning file series ========")
print("========================================")
t0 = time.time()
firstDate = None
lastDate  = None
i = 0
while True:

    if i == NT:
        lastDate = f"{year:04d}-{month}"
        break

    it       = i + 1
    yr_count = (it - 1) // 12
    month_i  = it - (yr_count * 12)
    year     = START_YEAR + yr_count
    month    = f"{month_i:02d}"

    file_atm = f"{root_atm}/{case_id}{prefixA}{year:04d}-{month}.nc"
    file_ice = f"{root_ice}/{case_id}{prefixI}{year:04d}-{month}.nc"
    file_lnd = f"{root_lnd}/{case_id}{prefixL}{year:04d}-{month}.nc"

    if do_atm == True:
        if not os.path.isfile(file_atm):
            lastDate = f"{year:04d}-{month}"
            break
        time_vecA[i] = it
    if do_ice == True:
        if not os.path.isfile(file_ice):
            lastDate = f"{year:04d}-{month}"
            break
        time_vecI[i] = it
    if do_lnd == True:
        if not os.path.isfile(file_lnd):
            lastDate = f"{year:04d}-{month}"
            break
        time_vecL[i] = it

    if i == 0:
        firstDate = f"{year:04d}-{month}"
        print("Date of first data read =", firstDate)

    i += 1

N_actual = i
timing['file scan'] = time.time() - t0
print("Scan complete. Timesteps found:", N_actual)
print_timing('file scan', timing['file scan'])

#-----------------------------------------------------------------------------------------------------------------
# Load all data upfront with xarray + dask, then compute global means in one pass.
#
# Assumptions verified against CAM output:
#   - open_mfdataset sorts files by CF time coordinate; year-0001..9999 ordering is correct.
#   - CAM, CICE, and CLM output on regular lat/lon grids use 'lat' and 'lon' dimension names.
#   - Files exist continuously from year 1 through the end of the run, so
#     time_offset = (START_YEAR - 1) * 12 correctly skips pre-START_YEAR months in the dataset.
#   - vavg_vec columns match the variable index offsets used by trend_utils
#     (atm: cols 4.., ice/lnd: cols 1..).
#-----------------------------------------------------------------------------------------------------------------
print("========================================")
print("=========  loading and averaging  ======")
print("========================================")

weights      = core.build_area_weights(lon, lat)
time_offset  = (START_YEAR - 1) * 12   # months before START_YEAR present in the archive glob

if do_atm == True:
    t0 = time.time()
    ds_atm  = core.load_dataset(root_atm, case_id, prefixA, list(atmvars_in))
    timing['load_dataset (atm)'] = time.time() - t0
    print_timing('load_dataset (atm)', timing['load_dataset (atm)'])

    t0 = time.time()
    gm_atm  = core.global_mean_dataset(ds_atm, weights)
    timing['global_mean_dataset (atm)'] = time.time() - t0
    print_timing('global_mean_dataset (atm)', timing['global_mean_dataset (atm)'])

    for n, vname in enumerate(atmvars_in):
        if vname in gm_atm:
            vavg_vecA[:N_actual, nv1dA + n] = gm_atm[vname].values[time_offset:time_offset + N_actual]

if do_ice == True:
    t0 = time.time()
    ds_ice  = core.load_dataset(root_ice, case_id, prefixI, list(icevars_in))
    timing['load_dataset (ice)'] = time.time() - t0
    print_timing('load_dataset (ice)', timing['load_dataset (ice)'])

    t0 = time.time()
    gm_ice  = core.global_mean_dataset(ds_ice, weights)
    timing['global_mean_dataset (ice)'] = time.time() - t0
    print_timing('global_mean_dataset (ice)', timing['global_mean_dataset (ice)'])

    for n, vname in enumerate(icevars_in):
        if vname in gm_ice:
            vavg_vecI[:N_actual, nv1dI + n] = gm_ice[vname].values[time_offset:time_offset + N_actual]

if do_lnd == True:
    t0 = time.time()
    ds_lnd  = core.load_dataset(root_lnd, case_id, prefixL, list(lndvars_in))
    timing['load_dataset (lnd)'] = time.time() - t0
    print_timing('load_dataset (lnd)', timing['load_dataset (lnd)'])

    t0 = time.time()
    gm_lnd  = core.global_mean_dataset(ds_lnd, weights)
    timing['global_mean_dataset (lnd)'] = time.time() - t0
    print_timing('global_mean_dataset (lnd)', timing['global_mean_dataset (lnd)'])

    for n, vname in enumerate(lndvars_in):
        if vname in gm_lnd:
            vavg_vecL[:N_actual, nv1dL + n] = gm_lnd[vname].values[time_offset:time_offset + N_actual]

#------------------------------------------------------
# Energy balance for all timesteps (if requested).
# Must be computed before running means so energy columns
# are populated when the stats loop reads vavg_vecA.
#------------------------------------------------------
if energy_requested and do_atm == True:
    for i in range(N_actual):
        etop, ebot = trend.atm_energy_calc(atmvars_in, vavg_vecA[i, :])
        vavg_vecA[i, nvtotA - 2] = etop
        vavg_vecA[i, nvtotA - 1] = ebot

#------------------------------------------------------
# Running means and slopes -- O(N) via cumsum, computed
# once per variable column over the full filled series.
#------------------------------------------------------
print("========================================")
print("=========  running means            ======")
print("========================================")
t0 = time.time()

if do_atm == True:
    for n in range(nv1dA, nvtotA):
        r1, r2, s1, s2 = core.compute_running_means(vavg_vecA[:N_actual, n], int1, int2)
        intavg1_vecA[:N_actual, n]       = r1
        intavg2_vecA[:N_actual, n]       = r2
        slope_intavg1_vecA[:N_actual, n] = s1
        slope_intavg2_vecA[:N_actual, n] = s2

if do_ice == True:
    for n in range(nv1dI, nvtotI):
        r1, r2, s1, s2 = core.compute_running_means(vavg_vecI[:N_actual, n], int1, int2)
        intavg1_vecI[:N_actual, n]       = r1
        intavg2_vecI[:N_actual, n]       = r2
        slope_intavg1_vecI[:N_actual, n] = s1
        slope_intavg2_vecI[:N_actual, n] = s2

if do_lnd == True:
    for n in range(nv1dL, nvtotL):
        r1, r2, s1, s2 = core.compute_running_means(vavg_vecL[:N_actual, n], int1, int2)
        intavg1_vecL[:N_actual, n]       = r1
        intavg2_vecL[:N_actual, n]       = r2
        slope_intavg1_vecL[:N_actual, n] = s1
        slope_intavg2_vecL[:N_actual, n] = s2

timing['running means'] = time.time() - t0
print_timing('running means', timing['running means'])

#-----------------------------------------------------------------------------------------------------------------
# Post-processing loop: print to screen at requested interval.
# All global means and statistics are already computed; this loop only handles output.
#-----------------------------------------------------------------------------------------------------------------
print("========================================")
print("=========  starting output loop  =======")
print("========================================")
t0 = time.time()
firstPrintCall = True
for i in range(N_actual):
    if (i + 1) % print_int == 0:
        trend.print2screen(atmvars_in, icevars_in, lndvars_in,
                           atmprint_in, iceprint_in, lndprint_in,
                           firstPrintCall, avgfreq,
                           do_atm, time_vecA[i], vavg_vecA[i,:],
                           intavg1_vecA[i,:], intavg2_vecA[i,:],
                           slope_intavg1_vecA[i,:], slope_intavg2_vecA[i,:],
                           do_ice, time_vecI[i], vavg_vecI[i,:],
                           intavg1_vecI[i,:], intavg2_vecI[i,:],
                           slope_intavg1_vecI[i,:], slope_intavg2_vecI[i,:],
                           do_lnd, time_vecL[i], vavg_vecL[i,:],
                           intavg1_vecL[i,:], intavg2_vecL[i,:],
                           slope_intavg1_vecL[i,:], slope_intavg2_vecL[i,:],
                           i)
        firstPrintCall = False

timing['print output'] = time.time() - t0
print_timing('print output', timing['print output'])

#-----------------------------------------------------------------------------------------------------------------
# end output loop
#-----------------------------------------------------------------------------------------------------------------
print("Concluding             ", case_id)
print("Number of files read:  ", N_actual)
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

print("========================================")
print("=========  timing summary          ======")
print("========================================")
total = sum(timing.values())
for label, elapsed in timing.items():
    print_timing(label, elapsed)
print_timing('total', total)

sys.exit()
