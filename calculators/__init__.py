try:
    from al import al
except:
    pass
try:
    from morse import morse
except:
    pass
try:
    from lj import lj
except:
    pass
try:
    from ljocl import ljocl
except:
    pass
try:
    import lammps_ext
except:
    pass

from bopfox import bopfox

def pt():
    return morse()
    

