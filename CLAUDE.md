# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`trend` is a Python tool for producing time-series outputs from NCAR CESM (CAM/ExoCAM) climate model simulations. It reads monthly-mean NetCDF output files, computes area-weighted global means, calculates running 1-year and 10-year averages and trend slopes, then optionally prints results to screen, writes text files, and/or generates line plots. The primary use case is diagnosing model convergence and residual trends.

## Dependencies

- `netCDF4` (grid peek only), `numpy`, `matplotlib`
- `xarray`, `dask` (for parallel file loading and global mean computation)
- `exocampy_tools` is no longer required

## Running

```bash
python trend.py <case_id> --cam [--cice] [--clm] [-y START_YEAR] [-n N_MONTHS] [-p PRINT_INTERVAL] [-a AVG_FREQ] [--plots] [--data] [--rundir]
```

**Example:**
```bash
python trend.py $my_case_name --cam -p 100 -y 10 --plots
```

`trend.py` must be run from the repository root (it opens `vars.in` by relative path). Output text files go to `data/`, plots to `plots/`.

The hardcoded base directory `dir` near the top of `trend.py` must point to the CESM scratch space (e.g., `/gpfsm/dnb53/etwolf/cesm_scratch/`). Adjust this for your system.

## Architecture

**`trend.py`** — main driver. The execution model is: (1) file-scan pass to determine `N_actual`, date strings, and `time_vec*` arrays without reading data; (2) load all data at once with xarray+dask and compute global means in one vectorized pass; (3) compute energy balance and running statistics over all timesteps upfront; (4) a post-processing loop that only handles screen output.

**`trend_core.py`** — core computation functions (no I/O beyond file loading):
- `build_area_weights(lon, lat)` — staggered-grid normalized area weights, shape `(nlat, nlon)`, called once at startup.
- `load_dataset(root_path, case_id, prefix, varnames)` — opens all matching monthly files via `xarray.open_mfdataset` with dask parallel loading; returns a lazy Dataset (no data read yet).
- `global_mean_dataset(ds, weights)` — replaces -999.0 sentinels, applies `ds.weighted().mean(['lat','lon'])`, calls `.compute()` to trigger dask execution; returns an in-memory Dataset of 1D time series.
- `compute_running_means(vavg_vec, int1, int2)` — O(N) causal rolling mean via cumsum; returns `(intavg1, intavg2, slope1, slope2)` for annual (int1=12) and decadal (int2=120) windows.

**`trend_utils.py`** — all I/O and plotting functions:
- `read_request_var()` — parses `vars.in` into 9 lists (read/print/plot × atm/ice/lnd) and validates that print/plot variables are a subset of read variables.
- `print2screen()` — tabular running output controlled by `-a` (0=monthly, 1=yearly, 2=decadal value).
- `print2text()` — writes `data/<case_id>_<firstDate>-<lastDate>_cam.txt` (and `_cice.txt`); currently only writes index + one variable (index 4), not fully implemented.
- `timeSeriesPlots()` — renders matplotlib line plots per requested variable; ice/land plotting is marked incomplete.
- `atm_energy_calc()` — derives TOA energy balance (`etop = FSNT - FLNT`) and surface energy balance (`ebot = FSNS - FLNS - LHFLX - SHFLX`) from already-averaged values. Requires FSNT, FLNT, FSNS, FLNS, LHFLX, SHFLX in the read list.

**`vars.in`** — plain-text namelist with three blocks (read / print / plot), each with one line per component model (atm, ice, lnd). The special token `energy` is recognized in print/plot blocks and triggers `atm_energy_calc` rather than direct variable lookup.

## Array indexing conventions

Variable arrays carry a leading offset of coordinate dimensions: atmosphere arrays have offset 4 (`time, lon, lat, lev`); ice arrays have offset 1 (`time`). `atm_vars_offset = 4` and `ice_vars_offset = 1` are module-level constants in `trend_utils.py`. When indexing into `vavg_vecA`, add `atm_vars_offset` to the 0-based index into `atmvars_in`. The derived `energy` variables are appended at the very end of the atmosphere array (`nvtotA-1` = ebot, `nvtotA-2` = etop).

## File naming

CESM archive NetCDF files are expected at:
```
<dir>/archive/<case_id>/atm/hist/<case_id>.cam.h0.<YYYY>-<MM>.nc
```
Years are zero-padded to 4 digits (e.g., `0010`). The loop exits cleanly when the next expected file is absent.

## Known limitations / incomplete areas

- `print2text` is only partially implemented (writes a single hardcoded variable).
- `timeSeriesPlots` only handles atmosphere variables; ice/land branches are noted as incomplete.
- Only 2D (surface/column-integrated) variables are supported; 3D fields are not yet implemented.
- Only monthly-mean cadence (`nhtfrq=0`) is supported.
- Auto y-axis bounds for temperature plots (`auto_t_bound`) use the start/end of the 10-year average to decide increasing vs. decreasing, then set limits based on min/max — check `trend_utils.py:351-359` if plots look clipped.
