import ase

def read_feff(filename):
    f = open(filename)

    pot_section = False
    atoms_section = False
    potential_to_z = {}

    atoms = ase.Atoms()
    atoms.set_pbc((False, False, False))
    for line in f:
        line = line.strip().lower()
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


def write_feff(filename, atoms, absorber):
    f = open(filename, "w")
    f.write("TITLE Generated by tsase\n")
    f.write("\nPOTENTIALS\n")
    f.write("%i %i\n" % (0, atoms[absorber].get_atomic_number()))

    unique_z = list(set(atoms.get_atomic_numbers()))
    for i,z in enumerate(unique_z):
        f.write("%i %i\n" % (i+1, z))

    f.write("\nATOMS\n")
    for i,atom in enumerate(atoms):
        if i == absorber:
            pot = 0
        else:
            pot = unique_z.index(atom.get_atomic_number())+1
        f.write("%f %f %f %i\n" % (atom.x, atom.y, atom.z, pot))
