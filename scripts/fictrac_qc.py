from argparse import ArgumentError
import numpy as np
import sys
import os
import matplotlib.pyplot as plt
import matplotlib as mpl
# THIS A HACK FOR DEVELOPMENT
sys.path.insert(0, os.path.realpath("../brainsss"))
sys.path.insert(0, os.path.realpath("../brainsss/scripts"))
from argparse_utils import (
    get_base_parser,
    add_fictrac_qc_arguments,
)
from logging_utils import setup_logging
import logging
from fictrac import smooth_and_interp_fictrac, load_fictrac


def parse_args(input, allow_unknown=True):
    parser = get_base_parser('fictrac_qc')

    parser = add_fictrac_qc_arguments(parser)

    # need to add this manually to procesing steps in order to make required
    parser.add_argument(
        '-d',
        '--dir', 
        type=str,
        help='func directory',
        required=True)

    if allow_unknown:
        args, unknown = parser.parse_known_args()
        if unknown is not None:
            print(f'skipping unknown arguments:{unknown}')
    else:
        args = parser.parse_args()

    return args


def make_2d_hist(fictrac, fictrac_folder, full_id, 
                 outdir, save=True, fixed_crop=True):
    plt.figure(figsize=(10, 10))
    norm = mpl.colors.LogNorm()
    plt.hist2d(fictrac["Y"], fictrac["Z"], bins=100, cmap="Blues", norm=norm)
    plt.ylabel("Rotation, deg/sec")
    plt.xlabel("Forward, mm/sec")
    plt.title(f"Behavior 2D hist {full_id}")
    plt.colorbar()
    name = "fictrac_2d_hist.png"
    if fixed_crop:
        plt.ylim(-400, 400)
        plt.xlim(-10, 15)
        name = "fictrac_2d_hist_fixed.png"
    if save:
        fname = os.path.join(outdir, name)
        plt.savefig(fname, dpi=100, bbox_inches="tight")


def make_velocity_trace(fictrac, fictrac_folder, 
                        full_id, xnew, outdir, save=True,
                        filename="fictrac_velocity_trace.png"):
    plt.figure(figsize=(10, 10))
    plt.plot(xnew / 1000, fictrac["Y"], color="xkcd:dusk")
    plt.ylabel("forward velocity mm/sec")
    plt.xlabel("time, sec")
    plt.title(full_id)
    if save:
        fname = os.path.join(outdir, filename)
        plt.savefig(fname, dpi=100, bbox_inches="tight")


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    setup_logging(args, logtype="fictrac_qc")
    print(logging.getLogger().handlers)
    print(args)

    fictrac_dir = os.path.join(args.dir, "fictrac")
    outdir = os.path.join(args.dir, 'QC')
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    logging.info(f'running fictrac_qc.py on {fictrac_dir}')
    if not os.path.exists(fictrac_dir):
        logging.info(f"fictrac directory {fictrac_dir} not found, skipping fictrac_qc")
        sys.exit(0)

    try:
        fictrac_raw = load_fictrac(fictrac_dir)
    except FileNotFoundError:
        logging.error(f"fictrac directory {fictrac_dir} not found, skipping fictrac_qc")
        sys.exit(0)

    # fly = os.path.split(os.path.split(directory)[0])[1]
    # expt = os.path.split(directory)[1]
    # TODO: This is making some assumptions about the naming convention...
    full_id = ", ".join(args.dir.split("/")[-3:-1])

    expt_len = (fictrac_raw.shape[0] / args.fps) * 1000
    behaviors = ["dRotLabY", "dRotLabZ"]
    fictrac = {}
    for behavior in behaviors:
        if behavior == "dRotLabY":
            short = "Y"
        elif behavior == "dRotLabZ":
            short = "Z"
        fictrac[short] = smooth_and_interp_fictrac(
            fictrac_raw, args.fps, args.resolution, expt_len, behavior
        )
    xnew = np.arange(0, expt_len, args.resolution)

    make_2d_hist(fictrac, fictrac_dir, full_id, outdir, save=True,
                 fixed_crop=True)
    make_2d_hist(fictrac, fictrac_dir, full_id, outdir, save=True, 
                 fixed_crop=False)
    make_velocity_trace(fictrac, fictrac_dir, full_id, xnew, 
                        outdir, save=True)
