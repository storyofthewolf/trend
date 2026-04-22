# trend

This family of scripts allows one to produce time-series outputs of CAM or
ExoCAM simulations from model outputs produced on a monthly mean cadence.
The primary use of this package is to determine model convergence characteristics
and diagnose any residual trends. The model assumes your directory structure
is set up in accordance with NCAR standards, `$RUNDIR` and `$DOUT_S_ROOT` (i.e. the
archive directory).

**Requires:** `numpy`, `matplotlib`, `xarray`, `dask`, `netCDF4`

## Contains

| File | Description |
|------|-------------|
| `trend.py` | Main program |
| `trend_core.py` | Core computation: area weights, xarray/dask file loading, global mean averaging, and O(N) running statistics |
| `trend_utils.py` | Functions for reading `vars.in`, screen/text output, and plotting |
| `vars.in` | Lists of variables to read from atmosphere, ice, and land model respectively |

## Usage

```
usage: trend.py [-h] [-y Y] [-n N] [-p P] [-a A] [--cam] [--cice] [--clm]
                [--rundir] [--plots] [--data]
                case_id
```

### Positional arguments

| Argument | Description |
|----------|-------------|
| `case_id` | Set simulation time series case name |

### Optional arguments

| Flag | Description |
|------|-------------|
| `-h, --help` | show this help message and exit |
| `-y Y` | Start year over which to begin timeseries |
| `-n N` | Number of months to integrate over |
| `-p P` | Interval for screen output, in number of months |
| `-a A` | Average shown on screen: 0=monthly, 1=yearly, 2=decadal (default 2) |
| `--cam` | Read atmosphere model data |
| `--cice` | Read sea ice model data |
| `--clm` | Read land model data |
| `--rundir` | Read files from run directory instead of archive |
| `--plots` | Do lineplots at end of sequence |
| `--data` | Print to data file |

## Example

```bash
python trend.py $my_case_name --cam -p 100 -y 10 --plots
```

This command:
- Produces a time-series from the run titled `$my_case_name`
- Reads atmosphere model files only (`cam.h0`, variables defined in `vars.in`)
- Reads data from the archive directory
- Starts at date `0010-01`
- Prints to screen once every 100 model months
- Plots data to screen
