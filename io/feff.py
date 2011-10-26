import ase

def read_feff(filename):
    f = open(filename)

    pot_section = False
    atoms_section = False
    potential_to_z = {}

    atoms = ase.Atoms()
    atoms.set_pbc((False, False, False))
    for line in f:
        if '*' in line:
            line = line[:line.index('*')]
        line = line.strip().lower()
        if len(line) == 0:
            continue
        if line == 'end':
            break
        if line == "potentials":
            pot_section = True
            continue
        elif line == "atoms":
            atoms_section = True
            pot_section = False
            continue
        elif len(line) == 0:
            continue

        if pot_section:
            fields = line.split()
            pot = int(fields[0])
            z = int(fields[1])
            potential_to_z[pot] = z

        if atoms_section:
            fields = line.split()
            x = float(fields[0])
            y = float(fields[1])
            z = float(fields[2])
            pot = int(fields[3])
            atomic_number = potential_to_z[pot]
            tag = pot
            atoms.append(ase.Atom(symbol=atomic_number ,position=(x,y,z),
                                  tag=tag))
    return atoms


def write_feff(filename, atoms, absorber, feff_options={}):
    f = open(filename, "w")
    f.write("TITLE Generated by tsase\n")
    for key, value in feff_options.iteritems():
        f.write("%s %s\n" % (key, value))
    f.write("\nPOTENTIALS\n")
    absorber_z = atoms[absorber].get_atomic_number()
    f.write("%i %i\n" % (0, absorber_z))

    unique_z = list(set(atoms.get_atomic_numbers()))
    pot_map = {}
    i = 1
    for z in unique_z:
        nz = len( [ a for a in atoms if a.number == z ] )
        if z == absorber_z and nz-1==0:
            continue
        f.write("%i %i\n" % (i, z))
        pot_map[z] = i
        i+=1

    f.write("\nATOMS\n")
    for i,atom in enumerate(atoms):
        if i == absorber:
            pot = 0
        else:
            pot = pot_map[atom.get_atomic_number()]
        f.write("%f %f %f %i\n" % (atom.x, atom.y, atom.z, pot))
