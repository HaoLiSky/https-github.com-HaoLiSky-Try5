#!usr/bin/env python
from ase.lattice.cubic import Diamond
import numpy as np
from ase.lattice.tetragonal import SimpleTetragonal
from ase.lattice.tetragonal import CenteredTetragonal
from ase.lattice.tetragonal import SimpleTetragonalFactory
from ase.lattice.tetragonal import CenteredTetragonalFactory
from ase.cluster.cubic import FaceCenteredCubicFactory
from ase.cluster.wulff import wulff_construction
from ase.io import write

#atoms = Diamond(symbol='Sn', latticeconstant =  6.5366, size = (2,2,2))
class dnxtalFactory(FaceCenteredCubicFactory):
    atomic_basis=np.array([[0,0,0], [0.5, 0,0.5],[0,0.5,0.5],[0.5,0.5,0.0],[0.25,0.25,0.25],[0.25,0.75,0.75], [0.75,0.25,0.75],[0.75,0.75,0.25]])
   
dnxtal=dnxtalFactory()
#atoms = dnxtal(symbols='Sn', surfaces=[[0,1,1], [1,0,1],[1,1,0]], layers=[4,4,4], latticeconstant = 6.53, vacuum = 5)

class aSnFactory(SimpleTetragonalFactory):
    bravais_basis=[[0,0,0], [0,0.5,0.25], [0.5,0, 0.75], [0.5, 0.5, 0.5]]
aSn = aSnFactory()

class SnO2rutFactory(SimpleTetragonalFactory):
    bravais_basis=[[0,0,0], [0.5, 0.5, 0.5], [0.3071,0.3071,0.0], [0.8071, 0.1931, 0.5], [0.1931, 0.8071, 0.5], [0.6929, 0.6929, 0.0]]
    element_basis=(0,0, 1, 1, 1, 1)
SnO2rut = SnO2rutFactory()


def Octahedron(symbol, length, cutoff, latticeconstant, alloy=False):
    # Check length and cutoff 
    if length < 2: 
        raise ValueError("The lenght must be greater than one.") 
    if cutoff < 0 or length < 2 * cutoff + 1: 
        raise ValueError("The cutoff must fullfill: > 0 and <= (length - 1) / 2.") 

# Create cluster 
    surfaces = [(1,1,1), (1,0,0)] 
    if length % 2 == 0: 
        center = np.array([0.5, 0.5, 0.5]) 
        layers = [length/2, length - 1 - cutoff] 
    else: 
        center = np.array([0.0, 0.0, 0.0]) 
        layers = [(length - 1)/2, length - 1 - cutoff] 

    if not alloy: 
        return dnxtal(symbol, surfaces, layers, latticeconstant, center) 
    else: 
        return L1_2(symbol, surfaces, layers, latticeconstant, center) 


#atoms = SnO2rut(symbol = ('Sn', 'O'), latticeconstant = {'a': 4.738,'c' : 3.1865}, size = (1,1,1))

#atoms=wulff_construction(symbol='Sn', surfaces=[[1,0,0], [1,1,0]], energies=[0.036,  0.023],   size= 147, structure=dnxtal, latticeconstant=6.53)
atoms= Octahedron(symbol='Sn', length=11, cutoff=0, latticeconstant= 6.53)
atoms.center(5.0)

write('POSCAR', atoms, format = 'vasp')


