#!/usr/bin/env python
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# plot_trends.py
#
#  Author: Wolf, E.T.
#
#  Offline multi-case time-series plotter.
#  Reads 1-N data files written by trend.py --data and overlays
#  them on shared axes for presentation-quality figures.
#
#  Usage:
#    python plot_trends.py data/file1.txt [data/file2.txt ...] \
#        --vars TS ICEFRAC energy_top \
#        [--freq native|int1|int2] \
#        [--xlabel LABEL] [--outdir plots/]
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import argparse
import os
import re
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ---------------------------------------------------------------
# colour / line-style cycle so N cases are visually distinct
# ---------------------------------------------------------------
_COLORS = [
    '#1f77b4', '#d62728', '#2ca02c', '#ff7f0e',
    '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
    '#bcbd22', '#17becf',
]
_LINESTYLES = ['-', '--', '-.', ':']


def _style(idx):
    return _COLORS[idx % len(_COLORS)], _LINESTYLES[(idx // len(_COLORS)) % len(_LINESTYLES)]


# ---------------------------------------------------------------
# helpers
# ---------------------------------------------------------------
def parse_case_id(filepath):
    """Extract case_id from filename: <case_id>_<firstDate>-<lastDate>_<model>.txt"""
    base = os.path.basename(filepath)
    # strip _<YYYY-MM>-<YYYY-MM>_cam/cice/clm.txt suffix
    m = re.match(r'^(.+)_\d{4}-\d{2}-\d{4}-\d{2}_\w+\.txt$', base)
    if m:
        return m.group(1)
    # fallback: strip extension
    return os.path.splitext(base)[0]


def load_file(filepath):
    """Return (header list, month array, data dict {colname: array})."""
    with open(filepath) as f:
        header = f.readline().split()
    data = np.loadtxt(filepath, skiprows=1)
    if data.ndim == 1:
        data = data[np.newaxis, :]
    months = data[:, 0].astype(int)
    cols = {name: data[:, i] for i, name in enumerate(header)}
    return header, months, cols


def available_vars(header):
    """Return base variable names present in header (strip _native/_int1/_int2 suffix)."""
    seen = []
    for col in header[1:]:  # skip 'month'
        base = re.sub(r'_(native|int1|int2)$', '', col)
        if base not in seen:
            seen.append(base)
    return seen


# ---------------------------------------------------------------
# main
# ---------------------------------------------------------------
def list_data_files(datadir='data'):
    """Print available data files and their variables, then exit."""
    if not os.path.isdir(datadir):
        sys.exit("Error: data directory '{}' not found.".format(datadir))
    txt_files = sorted(f for f in os.listdir(datadir) if f.endswith('.txt') and f != 'README')
    if not txt_files:
        print("No data files found in {}/".format(datadir))
        return
    print("\nAvailable files in {}/".format(datadir))
    print("-" * 72)
    for fname in txt_files:
        fp = os.path.join(datadir, fname)
        try:
            header, months, _ = load_file(fp)
            vars_list = available_vars(header)
            print("  {}".format(fname))
            print("    months : {} – {}  ({} timesteps)".format(
                int(months[0]), int(months[-1]), len(months)))
            print("    vars   : {}".format('  '.join(vars_list)))
        except Exception as e:
            print("  {}  [could not read: {}]".format(fname, e))
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Plot time-series from one or more trend.py data files.')
    parser.add_argument('files', nargs='*',
                        help='Data file(s) in data/ written by trend.py --data')
    parser.add_argument('--vars', nargs='+',
                        help='Variable(s) to plot (e.g. TS ICEFRAC energy_top)')
    parser.add_argument('--freq', choices=['native', 'int1', 'int2'], default='native',
                        help='Time frequency to plot (default: native)')
    parser.add_argument('--xlabel', default='Month',
                        help='X-axis label (default: Month)')
    parser.add_argument('--outdir', default='plots/post',
                        help='Output directory for saved figures (default: plots/post/)')
    parser.add_argument('--list', action='store_true',
                        help='List available data files in data/ and exit')
    parser.add_argument('--datadir', default='data',
                        help='Directory to scan for --list (default: data/)')
    args = parser.parse_args()

    if args.list:
        list_data_files(args.datadir)
        sys.exit(0)

    if not args.files:
        parser.error('Provide at least one data file, or use --list to see available files.')
    if not args.vars:
        parser.error('--vars is required when plotting.')

    if not os.path.isdir(args.outdir):
        sys.exit("Error: output directory '{}' does not exist.".format(args.outdir))

    # load all files
    cases = []
    for fp in args.files:
        if not os.path.isfile(fp):
            sys.exit("Error: file not found: {}\n"
                     "Hint: run from the repo root and use paths like data/<file>.txt\n"
                     "      use --list to see available files".format(fp))
        header, months, cols = load_file(fp)
        case_id = parse_case_id(fp)
        cases.append({'case_id': case_id, 'months': months, 'cols': cols, 'header': header})
        print("Loaded  {}  ({} months,  {} variables)".format(
            case_id, len(months), len(available_vars(header))))

    # validate requested variables against loaded files
    for var in args.vars:
        col_name = '{}_{}'.format(var, args.freq)
        for c in cases:
            if col_name not in c['cols']:
                avail = available_vars(c['header'])
                sys.exit(
                    "Error: '{}' (column '{}') not found in {}.\n"
                    "Available variables: {}".format(
                        var, col_name, c['case_id'], ', '.join(avail)))

    freq_label = {'native': 'monthly mean', 'int1': 'short-window avg', 'int2': 'long-window avg'}

    # one figure per variable
    for var in args.vars:
        col_name = '{}_{}'.format(var, args.freq)
        fig, ax = plt.subplots(figsize=(10, 5))

        for idx, c in enumerate(cases):
            color, ls = _style(idx)
            ax.plot(c['months'], c['cols'][col_name],
                    color=color, linestyle=ls, linewidth=1.5,
                    label=c['case_id'])

        ax.set_xlabel(args.xlabel, fontsize=12)
        ax.set_ylabel(var, fontsize=12)
        ax.set_title('{} — {}'.format(var, freq_label[args.freq]), fontsize=13)
        ax.legend(fontsize=9, framealpha=0.7)
        ax.grid(True, linestyle=':', linewidth=0.5, alpha=0.7)
        fig.tight_layout()

        outfile = os.path.join(args.outdir, '{}_{}.png'.format(var, args.freq))
        fig.savefig(outfile, dpi=150)
        plt.close(fig)
        print("Saved  {}".format(outfile))


if __name__ == '__main__':
    main()
