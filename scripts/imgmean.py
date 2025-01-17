# create and save mean image to/from nii/h5
# pyright: reportMissingImports=false

import logging
import h5py
import numpy as np
import argparse
import sys
import nibabel as nib
import nilearn.image
from hdf5_utils import get_chunk_boundaries


def parse_args(input, allow_unknown=True):
    parser = argparse.ArgumentParser(
        description="make mean brain over time for a single h5 or nii file"
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        help="h5 file",
        required=True,
    )
    parser.add_argument('--stepsize', type=int, default=50,
                        help="stepsize for chunking")
    parser.add_argument('--outfile_type', type=str, choices=['h5', 'nii'], default=None)
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    return parser.parse_args()


def imgmean(file, verbose=False, outfile_type=None, stepsize=50):
    """
    create and save temporal mean image to/from nii/h5

    Parameters
    ----------
    file : str
        h5 or nii file
    stepsize : int
        stepsize for chunking
    verbose : bool
        verbose output
    outfile_type : str
        output file type (nii or h5)
        defaults to same as input file
    """
    if 'h5' in file:
        infile_type = 'h5'
    elif 'nii' in file:
        infile_type = 'nii'
    else:
        raise ValueError(f"Unknown file type: {file}")

    if outfile_type is not None:
        assert outfile_type in ['nii', 'h5'], "outfile_type must be either 'nii' or 'h5'"
    else:
        outfile_type = infile_type

    meanfile = file.replace(f".{infile_type}", f"_mean.{outfile_type}")

    assert meanfile != file, f"meanfile should be different from file: {meanfile}"
    if infile_type == 'h5':
        print('computing mean of h5 file')
        with h5py.File(file, 'r') as f:

            # convert immediately to nibabel image
            img = nib.Nifti1Image(f['data'], affine=f['qform'][:])
            meanimg = nib.Nifti1Image(np.zeros(img.shape[:3]), affine=f['qform'][:])
            chunk_boundaries = get_chunk_boundaries(stepsize, img.shape[-1])

            nchunks = len(chunk_boundaries)
            for chunk_num, (chunk_start, chunk_end) in enumerate(chunk_boundaries):
                meanimg.dataobj[:, :, :] += np.mean(img.dataobj[:, :, :, chunk_start:chunk_end], axis=-1) / nchunks

            if 'qform' in f:
                meanimg.header.set_qform(f['qform'][:])
                # need to set sform as well as qform
                meanimg.header.set_sform(f['qform'][:])
            else:
                print('no qform found in h5 file')

            if 'zooms' in f:
                meanimg.header.set_zooms(f['zooms'][:3])
            else:
                print('no zooms found in h5 file')

            if 'xyzt_units' in f:
                # hdf saves to byte strings
                try:
                    xyz_units = f['xyzt_units'][0].decode('utf-8')
                except AttributeError:
                    xyz_units = f['xyzt_units'][0]
                meanimg.header.set_xyzt_units(xyz=xyz_units)
            else:
                print('no xyzt_units found in h5 file')

    else:
        print('computing mean of nii file')
        img = nib.load(file, mmap='r')
        # print('original image header:', img.header)
        # try using dataobj to get the data without loading the whole image
        meanimg = nib.Nifti1Image(np.zeros(img.shape[:3]), img.affine)
        chunk_boundaries = get_chunk_boundaries(stepsize, img.shape[-1])

        nchunks = len(chunk_boundaries)
        for chunk_num, (chunk_start, chunk_end) in enumerate(chunk_boundaries):
            meanimg.dataobj[:, :, :] += np.mean(img.dataobj[:, :, :, chunk_start:chunk_end], axis=-1) / nchunks
        # meanimg = nilearn.image.mean_img(file)
        meanimg.header.set_qform(img.header.get_qform())
        meanimg.header.set_sform(img.header.get_sform())
        meanimg.header.set_xyzt_units(xyz=img.header.get_xyzt_units()[0])
        meanimg.header.set_zooms(img.header.get_zooms()[:3])

    logging.info(f'image mean: {np.mean(meanimg.get_fdata())}')

    if verbose:
        print(f'saving mean of {file} to file {meanfile}')

    if outfile_type == 'h5':
        print("saving to h5")
        with h5py.File(meanfile, 'w') as f:
            f.create_dataset('data', data=meanimg.get_fdata(), dtype="float32", chunks=True)
            f.create_dataset('qform', data=meanimg.header.get_qform())
            f.create_dataset('zooms', data=meanimg.header.get_zooms())
            f.create_dataset('xyzt_units', data=meanimg.header.get_xyzt_units())

    else:
        print('saving to nii')
        meanimg.to_filename(meanfile)
    return(meanfile)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    print(f'making mean brain for {args.file}')
    meanimg = imgmean(args.file, args.verbose, args.outfile_type)
