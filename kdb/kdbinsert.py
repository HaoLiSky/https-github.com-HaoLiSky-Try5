#!/usr/bin/env python

import os
import sys
import numpy 
import glob

from optparse import OptionParser

from kdb import *

def coordination_numbers(p, cutoff):
    nl = []
    for a in range(len(p)):
        nl.append([])
        for b in range(len(p)):
            if b != a:
                dist = numpy.linalg.norm(p.r[a] - p.r[b])        
                if dist < (elements[p.names[a]]["radius"] + elements[p.names[b]]["radius"]) * (1.0 + NEIGHBOR_FUDGE):
                    nl[a].append(b)
    return [len(l) for l in nl]

def getMappings(a, b, mappings = None):
    """ A recursive depth-first search for a complete set of mappings from atoms
        in configuration a to atoms in configuration b. Do not use the mappings
        argument, this is only used internally for recursion. 
        
        Returns None if no mapping was found, or a dictionary mapping atom 
        indices a to atom indices b.
        
        Note: If a and b are mirror images, this function will still return a 
        mapping from a to b, even though it may not be possible to align them 
        through translation and rotation. """
    # If this is the top-level user call, create and loop through top-level
    # mappings.
    if mappings == None:
        # Find the least common coordination number in b.
        bCoordinations = coordination_numbers(b, 3.3)
        bCoordinationsCounts = {}
        for coordination in bCoordinations:
            if coordination in bCoordinationsCounts:
                bCoordinationsCounts[coordination] += 1
            else:
                bCoordinationsCounts[coordination] = 1
        bLeastCommonCoordination = bCoordinationsCounts.keys()[0]
        for coordination in bCoordinationsCounts.keys():
            if bCoordinationsCounts[coordination] < bCoordinationsCounts[bLeastCommonCoordination]:
                bLeastCommonCoordination = coordination
        # Find one atom in a with the least common coordination number in b. 
        # If it does not exist, return None.
        aCoordinations = coordination_numbers(a, 3.3)
        try:
            aAtom = aCoordinations.index(bLeastCommonCoordination)
        except ValueError:
            return None
        # Create a mapping from the atom chosen from a to each of the atoms with
        # the least common coordination number in b, and recurse.
        for i in range(len(bCoordinations)):
            if bCoordinations[i] == bLeastCommonCoordination:
                # Make sure the element types are the same.
                if a.names[aAtom] != b.names[i]:
                    continue
                mappings = getMappings(a, b, {aAtom:i})
                # If the result is not none, then we found a successful mapping.
                if mappings is not None:
                    return mappings
        # There were no mappings.        
        return None
    
    # This is a recursed invocation of this function.
    else:
        # Find an atom from a that has not yet been mapped.
        unmappedA = 0
        while unmappedA < len(a):
            if unmappedA not in mappings.keys():
                break
            unmappedA += 1
        # Calculate the distances from unmappedA to all mapped a atoms.
        distances = {}
        for i in mappings.keys():
            distances[i] = a.atomAtomDistance(unmappedA, i)
        
        # Loop over each unmapped b atom. Compare the distances between it and 
        # the mapped b atoms to the corresponding distances between unmappedA 
        # and the mapped atoms. If everything is similar, create a new mapping
        # and recurse.
        for bAtom in range(len(b)):
            if bAtom not in mappings.values():
                for aAtom in distances:
                    # Break if type check fails.
                    if b.names[bAtom] != a.names[unmappedA]:
                        break
                    # Break if distance check fails  
                    bDist = b.atomAtomDistance(bAtom, mappings[aAtom])
                    if abs(distances[aAtom] - bDist) > DISTANCE_CUTOFF:
                        break
                else:
                    # All distances were good, so create a new mapping.
                    newMappings = mappings.copy()
                    newMappings[unmappedA] = bAtom
                    # If this is now a complete mapping from a to b, return it.
                    if len(newMappings) == len(a):
                        return newMappings
                    # Otherwise, recurse.
                    newMappings = getMappings(a, b, newMappings)
                    # Pass any successful mapping up the recursion chain. 
                    if newMappings is not None:
                        return newMappings     
        # There were no mappings.   
        return None 


def stripUnselectedAtoms(con, selected):
    """ Removes any atoms from con that are not in selected and returns a new
    structure and a mapping from atoms in the old structure to atoms in the new 
    structure. """
    mapping = {}
    new = Atoms(len(selected))
    new.box = con.box.copy()
    for i in range(len(selected)):
        new.r[i] = con.r[selected[i]]
        new.free[i] = con.free[selected[i]]
        new.names[i] = con.names[selected[i]]
        new.mass[i] = con.mass[selected[i]]
        mapping[selected[i]] = i
    return new, mapping
    
if __name__ == "__main__":

    # Parse command line options.
    parser = OptionParser(usage = "%prog [options] reactant.con saddle.con product.con mode")
    parser.add_option("-d", "--kdbdir", dest = "kdbdir", 
                      help = "the path to the kinetic database",
                      default = "./kdb")
    parser.add_option("-n", "--nf", dest = "nf", action="store", type="float", 
                      help = "neighbor fudge parameter",
                      default = NEIGHBOR_FUDGE)
    parser.add_option("-c", "--dc", dest = "dc", action="store", type="float", 
                      help = "distance cutoff parameter",
                      default = DISTANCE_CUTOFF)
    parser.add_option("--barrier1", dest = "b1", action="store", type="float", 
                      help = "barrier energy for reactant to saddle",
                      default = -1.0)
    parser.add_option("--barrier2", dest = "b2", action="store", type="float", 
                      help = "barrier energy for product to saddle",
                      default = -1.0)
    parser.add_option("--prefactor1", dest = "p1", action="store", type="float", 
                      help = "prefactor for reactant to saddle",
                      default = -1.0)
    parser.add_option("--prefactor2", dest = "p2", action="store", type="float", 
                      help = "prefactor for product to saddle",
                      default = -1.0)
    options, args = parser.parse_args()
    NEIGHBOR_FUDGE = options.nf
    DISTANCE_CUTOFF = options.dc
    

    # Make sure we get the reactant, saddle, product, and mode files.
    if len(args) < 4:
        parser.print_help()
        sys.exit()
        

    # Load the reactant, saddle, product, and mode files.
    reactant = loadcon(args[0])
    saddle = loadcon(args[1])
    product = loadcon(args[2])
    mode = load_mode(args[3])

    #TODO: check that the numbers and types of atoms are the same, and that the mode
    #      is the same length as the configs.

    # Make a list of mobile atoms.
    mobileAtoms = []
    reactant2saddle = per_atom_norm(saddle.r - reactant.r, saddle.box)
    product2saddle = per_atom_norm(saddle.r - product.r, saddle.box)
    reactant2product = per_atom_norm(product.r - reactant.r, saddle.box)
    for i in range(len(saddle)):
        if max(reactant2saddle[i], product2saddle[i], reactant2product[i]) > MOBILE_ATOM_CUTOFF:
            mobileAtoms.append(i)
    
    # If no atoms made the mobile atom cutoff, choose the one that moves the most 
    # between reactant and product.
    if len(mobileAtoms) == 0:
        mobileAtoms.append(list(reactant2product).index(max(reactant2product)))
        
    # Make a list of atoms that neighbor the mobile atoms.
    neighborAtoms = []
    for atom in mobileAtoms:
        r1 = elements[saddle.names[atom]]["radius"]
        for i in range(len(saddle)):
            if i in mobileAtoms or i in neighborAtoms:
                continue
            r2 = elements[saddle.names[i]]["radius"]
            maxDist = (r1 + r2) * (1.0 + NEIGHBOR_FUDGE)
            if reactant.atomAtomPbcDistance(atom, i) < maxDist:
                neighborAtoms.append(i)
            elif saddle.atomAtomPbcDistance(atom, i) < maxDist:
                neighborAtoms.append(i)
            elif product.atomAtomPbcDistance(atom, i) < maxDist:
                neighborAtoms.append(i)

    selectedAtoms = mobileAtoms + neighborAtoms
    
    # Quit if not enough selected atoms.
    if len(selectedAtoms) < 2:
        print "Too few atoms in process, or neighbor_fudge too small."
        sys.exit()
    
    # Remove unselected atoms.
    reactant, mapping = stripUnselectedAtoms(reactant, selectedAtoms)
    saddle, mapping = stripUnselectedAtoms(saddle, selectedAtoms)
    product, mapping = stripUnselectedAtoms(product, selectedAtoms)

    # Update the mode.
    newMode = numpy.zeros((len(selectedAtoms), 3))
    for m in mapping:
        newMode[mapping[m]] = mode[m]
    mode = newMode

    # Remove PBC's.
    temp = reactant.copy()
    undone = range(len(temp))
    working = [undone.pop()]        
    while len(undone) > 0:
        if len(working) == 0:
            print "Dissociated reactant, or neighbor_fudge too small."
            sys.exit()
        a = working.pop()
        for i in undone[:]:
            v = pbc(temp.r[i] - temp.r[a], temp.box)
            d = numpy.linalg.norm(v)
            if d < (elements[temp.names[a]]["radius"] + elements[temp.names[i]]["radius"]) * (1.0 + NEIGHBOR_FUDGE):
                temp.r[i] = temp.r[a] + v
                working.append(i)
                undone.remove(i)
    v1s = pbc(saddle.r - reactant.r, reactant.box)
    v12 = pbc(product.r - reactant.r, reactant.box)
    reactant = temp
    saddle.r = reactant.r + v1s
    product.r = reactant.r + v12
    
    # Find saddle center of coordinates.
    coc = numpy.zeros((1,3))
    for i in range(len(saddle)):
        coc += saddle.r[i]
    coc = coc / len(saddle)
    
    # Shift all structures so that the saddle center of coordinates is at 
    # [0, 0, 0].
    reactant.r -= coc    
    saddle.r -= coc    
    product.r -= coc    
    
    # Give all structures a huge box.
    # TODO: all references to boxes should be removed after PBCs are removed.
    reactant.box = numpy.identity(3) * 1024
    saddle.box = numpy.identity(3) * 1024
    product.box = numpy.identity(3) * 1024

    # Get the element path for this process
    elementPath = "".join(reactant.getNameList())
    elementPath = os.path.join(options.kdbdir, elementPath)
    if not os.path.exists(elementPath):
        os.makedirs(elementPath)

    # Get a list of process subdirectories in the element path.
    procdirs = glob.glob(os.path.join(elementPath, "*"))

    # Loop over the existing process and check for matches to the saddle.
    for procdir in procdirs:
        dbSaddle = loadxyz(os.path.join(procdir, "saddle.xyz"))
        if len(saddle) != len(dbSaddle):
            continue
        if getMappings(saddle, dbSaddle) is not None:
            print "duplicate of", procdir
            sys.exit()

    # Create the path for this process.
    i = 0
    while os.path.exists(os.path.join(elementPath, str(i))):
        i += 1
    processPath = os.path.join(elementPath, str(i))
    os.makedirs(processPath)

    # Save the configurations for this process.  
    savexyz(os.path.join(processPath, "min1.xyz"), reactant)
    savexyz(os.path.join(processPath, "saddle.xyz"), saddle)
    savexyz(os.path.join(processPath, "min2.xyz"), product)
    save_mode(os.path.join(processPath, "mode"), mode)

    def numberfile(filename, number):
        f = open(filename, 'w')
        f.write(str(number))
        f.close()
        
    # Save the barriers and prefactors.
    if options.b1 > 0.0: numberfile(os.path.join(processPath, "barrier1"), options.b1)
    if options.b2 > 0.0: numberfile(os.path.join(processPath, "barrier2"), options.b2)
    if options.p1 > 0.0: numberfile(os.path.join(processPath, "prefactor1"), options.p1)
    if options.p2 > 0.0: numberfile(os.path.join(processPath, "prefactor2"), options.p2)
    
    # Save the list of mobile atoms.
    f = open(os.path.join(processPath, "mobile"), 'w')
    for atom in mobileAtoms:
        f.write("%d\n" % mapping[atom])
    f.close()
    
    # Save a movie of the local process.
    mr = reactant.copy()
    steps = 8
    savexyz(os.path.join(processPath, "movie.xyz"), mr, 'w')
    for i in range(1, steps):
        mr.r = reactant.r + (saddle.r - reactant.r) * (i / float(steps))
        savexyz(os.path.join(processPath, "movie.xyz"), mr, 'a')
    savexyz(os.path.join(processPath, "movie.xyz"), saddle, 'a')
    for i in range(1, steps):
        mr.r = saddle.r + (product.r - saddle.r) * (i / float(steps))
        savexyz(os.path.join(processPath, "movie.xyz"), mr, 'a')
    savexyz(os.path.join(processPath, "movie.xyz"), product, 'a')
        
    # Indicate that the process was inserted successfully.
    print "good"

    
        
    
    
                    
                
                
        
        
    
    
    
        
        
        
        
        
            

        










