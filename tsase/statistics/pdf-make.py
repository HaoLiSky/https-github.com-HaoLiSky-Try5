#!/usr/bin/env python
import ase
#from ase import copy
#from ase.io import read
from tsase.io import read
import numpy as np
import sys
import math
from scipy import interpolate

def main():
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('--ignore-elements', type=str, metavar='ELEMENTS',
            help='comma delimited list of elements to ignore in the ' + \
            'pdf')
    parser.add_argument('--skip', type=int, default=0,
            help='number of frames to skip at the beginning')
    parser.add_argument('--every', type=int, default=1,
            help='number of frames to between each step')
    parser.add_argument('--num-bin', type=int, 
            help='num bins used in pdf function (default: %(default)s)', default=150)
    parser.add_argument('--mesh-size', type=float, metavar='DISTANCE', 
            help='mesh size used in pdf function interpolation (default: %(default)s)', default=0.01)
    parser.add_argument('trajectories', metavar='TRAJ', nargs='+',
            help='trajectory file (POSCAR, con, xyz)')

    args = parser.parse_args()

    if args.ignore_elements:
        args.ignore_elements = args.ignore_elements.split(',')

    snapshots_command(args)
        
    #Integrate spline for coordination

def integ(x,tck,constant=0.0):
    x = np.atleast_1d(x)   
    out = np.zeros(x.shape, dtype=x.dtype)
    for n in xrange(len(out)):
        out[n] = interpolate.splint(x[n-1],x[n],tck)
        print out[n]
        out += constant
        return out


def snapshots_command(args):
    trajectory = []
    for filename in args.trajectories:
        print 'reading', filename
        if filename[-3:] == 'con':
            trajectory += read(filename)[args.skip::args.every]
        elif filename.startswith('POSCAR') or filename.startswith('CONTCAR'):
            trajectory = [read(filename)]
        else:
            trajectory += read(filename, args.skip, args.every)

    hist=np.zeros(shape=(args.num_bin))
    dist=np.zeros(shape=(args.num_bin))

    ## Loop over snapshots
    for i, atoms in enumerate(trajectory):
        atoms = atoms.copy()
        if args.ignore_elements:
            ignore_indicies = [atom.index for atom in atoms 
                               if atom.symbol in args.ignore_elements]
            del atoms[ignore_indicies]
    
##Loop over pairs of atoms in snapshots
    cell =  atoms.get_cell()
    bl = cell[2,2]
    bl_norm = np.linalg.norm(cell)
    bin_size= bl_norm/2.0/(args.num_bin)
    for l in xrange(len(atoms)-1):
            for j in xrange(l+1, len(atoms)):  
                d = atoms.get_distance(l,j, True)
                if d < bl/2.0:
                    k = int(round(d/bin_size))
                    hist[k] = hist[k] + 2.0
 ##Normalize                   
    natoms= float(len(atoms))
    rho= natoms/atoms.get_volume()
    bs_vol=(4.0/3.0)*np.pi*bin_size*bin_size* bin_size
    for l in xrange(1, args.num_bin):
        dist[l] = bin_size*(0.5+l)   
        norm_factor= ((l+1)*(l+1)*(l+1)-l*l*l)*rho*bs_vol
        hist[l] = hist[l]/norm_factor/natoms/len(trajectory)

    ##Interpolate-proc
    dx = float(args.mesh_size)
    tck = interpolate.splrep(dist, hist, k=2)
    xnew = np.arange(1.0, bl_norm/2.0, dx)
    ynew = interpolate.splev(xnew, tck, der=0)
    yint = integ(xnew,tck)

    ## WRITE TO FILE ##
    outdat=np.column_stack((dist, hist))
    np.savetxt("pdf.dat", outdat, delimiter="   ")

    outdat_interp=np.column_stack((xnew, ynew, yint))
    np.savetxt("interprdf.dat", outdat_interp, delimiter="   ")


if __name__ == '__main__':
        main()

