# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`trend` is a Python tool for producing time-series diagnostics from NCAR CESM (CAM/ExoCAM) climate model simulations. It reads monthly-mean NetCDF output files, computes area-weighted global means, calculates running 1-year and 10-year averages and trend slopes, then optionally prints results to screen, writes text files, and/or generates line plots. The primary use case is diagnosing model convergence and residual trends.

## Dependencies

- `netCDF4`, `numpy`, `matplotlib`, `tqdm`
- `xarray` and `exocampy_tools` are not used

## Running

```bash
python trend.py <case_id> --cam [--cice] [--clm] [-y START_YEAR] [-n N_MONTHS] [-p PRINT_INTERVAL] [-a AVG_FREQ] [--plots] [--data] [--rundir] [--testdir PATH]
```

**Example:**
```bash
python trend.py $my_case_name --cam -p 100 -y 10 --plots
```

`trend.py` must be run from the repository root (it opens `vars.in` by relative path). Output text files go to `data/`, plots to `plots/`.

The hardcoded base directory `dir` near the top of `trend.py` must point to the CESM scratch space. Adjust this for your system before running.

### File path modes

Three modes control where files are read from, checked in this order:

| Mode | Flag | Path |
|------|------|------|
| Test/local | `--testdir PATH` | `PATH/` flat directory, all components |
| Run directory | `--rundir` | `$dir/rundir/<case_id>/run/` |
| Archive (default) | _(none)_ | `$dir/archive/<case_id>/atm/hist/` etc. |

In `--testdir` mode, files must still follow CAM naming conventions (`case_id.cam.h0.YYYY-MM.nc`); no subdirectory structure is expected.

## Architecture

**`trend.py`** — main driver. Execution proceeds in five phases:
1. **File scan** — iterates month-by-month checking file existence to determine `N_actual`, `firstDate`, `lastDate`, and `time_vec*` arrays. No data is read here.
2. **Read and average** — calls `core.read_monthly_files()` once per active component to read all monthly files sequentially and compute area-weighted global means.
3. **Energy balance** — if `energy` is in the print list, computes TOA and surface energy balance for all `N_actual` timesteps from the averaged flux variables.
4. **Running statistics** — calls `core.compute_running_means()` once per variable column over the full filled series (O(N) via cumsum).
5. **Output loop** — post-processing pass over already-computed arrays: prints to screen at the `-p` interval, then optionally writes text files and generates plots.

**`trend_core.py`** — core computation functions:
- `build_area_weights(lon, lat)` — staggered-grid normalized area weights, shape `(nlat, nlon)`, called once at startup. Cell edges are midpoints between adjacent lat values, with ±90° at the poles.
- `global_mean_2d(var2d, weights)` — area-weighted mean of a single 2D field via `np.ma.average`; masked cells (including -999.0 sentinels) are excluded from both numerator and denominator.
- `read_monthly_files(root_path, case_id, prefix, varnames, start_year, n_months, weights)` — globs and date-filters all matching files, slices to `start_year` and `n_months`, reads each file with netCDF4, calls `global_mean_2d` per variable, and returns a `(n_months, len(varnames))` numpy array plus the file list. Progress shown via `tqdm`. Missing variables are warned once per prefix/varname pair.
- `compute_running_means(vavg_vec, int1, int2)` — O(N) causal rolling mean via cumsum; returns `(intavg1, intavg2, slope1, slope2)` for annual (`int1=12`) and decadal (`int2=120`) windows. Slopes are in units per year.

**`trend_utils.py`** — parsing, output, and plotting functions:
- `read_request_var()` — parses `vars.in` into 9 lists (read/print/plot × atm/ice/lnd) and validates that print/plot variables are a subset of read variables.
- `print2screen()` — tabular running output; `-a` flag selects which average is shown (0=monthly, 1=annual, 2=decadal).
- `atm_energy_calc()` — derives `etop = FSNT - FLNT` and `ebot = FSNS - FLNS - LHFLX - SHFLX`. Requires those six variables in the read list.
- `timeSeriesPlots()` — renders matplotlib line plots per requested variable; ice/land plotting is incomplete.
- `print2text()` — writes `data/<case_id>_<firstDate>-<lastDate>_cam.txt`; partially implemented (writes one hardcoded variable column).

**`vars.in`** — plain-text namelist with three blocks (read / print / plot), each with one line per component model (atm, ice, lnd). The special token `energy` in print/plot blocks triggers `atm_energy_calc` rather than a direct variable lookup.

## Array indexing conventions

Variable arrays carry a leading offset of coordinate dimensions: atmosphere arrays have offset 4 (`time, lon, lat, lev`); ice and land arrays have offset 1 (`time`). `atm_vars_offset = 4` and `ice_vars_offset = 1` are module-level constants in `trend_utils.py`. When indexing `vavg_vecA`, add `atm_vars_offset` to the 0-based index into `atmvars_in`. The derived `energy` variables are appended at the very end of the atmosphere array (`nvtotA-2` = etop, `nvtotA-1` = ebot).

The `read_monthly_files` return array has shape `(n_months, len(varnames))` with no coordinate offset — index 0 is `varnames[0]`. `trend.py` writes these into `vavg_vec*` starting at `nv1dA`/`nv1dI`/`nv1dL` to maintain the offset convention expected by `trend_utils`.

## File naming

CESM archive NetCDF files are expected at:
```
<dir>/archive/<case_id>/atm/hist/<case_id>.cam.h0.<YYYY>-<MM>.nc
```
Years are zero-padded to 4 digits (e.g., `0010`). The file scan exits cleanly when the next expected file is absent.

`read_monthly_files` uses `(start_year - 1) * 12` as a slice offset into the sorted glob result to skip pre-`START_YEAR` files. This assumes all years from 1 to `START_YEAR - 1` have exactly 12 complete monthly files.

## Known limitations / incomplete areas

- `print2text` is only partially implemented (writes a single hardcoded variable).
- `timeSeriesPlots` only handles atmosphere variables; ice/land branches are noted as incomplete.
- Only 2D (surface/column-integrated) variables are supported; 3D fields are not yet implemented.
- Only monthly-mean cadence (`nhtfrq=0`) is supported.
- Auto y-axis bounds for temperature plots (`auto_t_bound`) use the start/end of the 10-year average to decide increasing vs. decreasing — check `trend_utils.py:351-359` if plots look clipped.
