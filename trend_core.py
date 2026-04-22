#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# trend_core.py
#
#  Author: Wolf, E.T.
#
#  Core computation functions: area weights, dataset I/O,
#  global means, and running statistics.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import numpy as np
import xarray as xr


def build_area_weights(lon, lat):
    """
    Compute normalized 2D area weights for a regular lat/lon grid.
    Returns array of shape (nlat, nlon) with weights summing to 1.0.
    Uses staggered grid: cell edges at lat midpoints, poles at ±90°.
    """
    lat_rad = np.deg2rad(lat)

    # Cell edge latitudes: midpoints between adjacent points, poles at boundaries
    lat_edges = np.empty(len(lat) + 1)
    lat_edges[0]    = -np.pi / 2.0
    lat_edges[-1]   =  np.pi / 2.0
    lat_edges[1:-1] = 0.5 * (lat_rad[:-1] + lat_rad[1:])

    # Uniform longitude spacing (CAM uses regular lon grids)
    dlon_rad = np.deg2rad(lon[1] - lon[0]) if len(lon) > 1 else 2.0 * np.pi

    # Cell area proportional to dlon * delta(sin(lat)); broadcast to (nlat, nlon)
    d_sin_lat = np.sin(lat_edges[1:]) - np.sin(lat_edges[:-1])
    weights   = d_sin_lat[:, np.newaxis] * np.full(len(lon), dlon_rad)

    return weights / weights.sum()


def load_dataset(root_path, case_id, prefix, varnames):
    """
    Open all monthly component files at once with dask-backed lazy loading.
    Files are matched by glob and concatenated along the time dimension.
    Returns a Dataset containing only the requested variables.
    No data is read from disk until compute() is called.
    """
    glob_pattern = f"{root_path}/{case_id}{prefix}*.nc"
    ds = xr.open_mfdataset(
        glob_pattern,
        combine='by_coords',
        data_vars='minimal',
        coords='minimal',
        compat='override',
        parallel=True,
    )
    return ds[list(varnames)]


def global_mean_dataset(ds, weights):
    """
    Compute area-weighted global mean for all variables across all timesteps.
    Replaces -999.0 sentinel values with NaN before averaging so they are
    excluded from the weighted sum. Triggers dask computation and returns
    an in-memory Dataset of 1D time series (one scalar per timestep per variable).
    """
    weights_da = xr.DataArray(weights, dims=['lat', 'lon'])
    ds = ds.where(ds != -999.0)
    return ds.weighted(weights_da).mean(dim=['lat', 'lon']).compute()


def compute_running_means(vavg_vec, int1, int2):
    """
    Compute two causal rolling-window means and their per-year slopes.

    Window int1 (annual, 12 months) and int2 (decadal, 120 months).
    Before the window is full the mean is taken over all available data
    and the slope is computed relative to the first value, matching the
    original per-timestep logic.

    Slope units: [variable units] / year.

    Returns (intavg1, intavg2, slope1, slope2), each a 1D array of
    length len(vavg_vec).
    """
    N   = len(vavg_vec)
    cs  = np.cumsum(np.insert(vavg_vec, 0, 0.0))
    idx = np.arange(N)

    def _running_mean(window):
        # i < window: mean over vavg_vec[0 : i+1]  (cs[i+1] - cs[0]) / (i+1)
        # i >= window: mean over vavg_vec[i-window : i]  (cs[i] - cs[i-window]) / window
        end   = np.where(idx < window, idx + 1, idx)
        start = np.where(idx < window, 0,        idx - window)
        denom = np.where(idx < window, idx + 1,  window)
        return (cs[end] - cs[start]) / denom

    intavg1 = _running_mean(int1)
    intavg2 = _running_mean(int2)

    def _slope(intavg, window):
        # i < window: (intavg[i] - intavg[0]) / (window/12)
        # i >= window: (intavg[i] - intavg[i-window]) / (window/12)
        ref = np.where(idx < window, 0, idx - window)
        return (intavg - intavg[ref]) / (window / 12.0)

    slope1 = _slope(intavg1, int1)
    slope2 = _slope(intavg2, int2)

    return intavg1, intavg2, slope1, slope2
