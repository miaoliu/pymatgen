#!/usr/bin/python

import unittest
import os
from numpy import array

from pymatgen.io.vaspio_set import MITVaspInputSet, MITHSEVaspInputSet, \
    MPVaspInputSet, MITGGAVaspInputSet, \
    MPStaticVaspInputSet, MPNonSCFVaspInputSet, MITMDVaspInputSet
from pymatgen.io.vaspio.vasp_input import Poscar
from pymatgen import Specie, Lattice, Structure
from pymatgen.serializers.json_coders import PMGJSONDecoder

test_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                        'test_files')

dec = PMGJSONDecoder()


class MITMPVaspInputSetTest(unittest.TestCase):

    def setUp(self):
        filepath = os.path.join(test_dir, 'POSCAR')
        poscar = Poscar.from_file(filepath)
        self.struct = poscar.structure

        self.mitparamset = MITVaspInputSet()
        self.mithseparamset = MITHSEVaspInputSet()
        self.paramset = MPVaspInputSet()
        self.userparamset = MPVaspInputSet(
            {'MAGMOM': {"Fe": 10, "S": -5, "Mn3+": 100}}
        )
        self.mitggaparam = MITGGAVaspInputSet()
        self.mpstaticparamset = MPStaticVaspInputSet()
        self.mpnscfparamsetu = MPNonSCFVaspInputSet(
            {"NBANDS":50}, mode="Uniform")
        self.mpnscfparamsetl = MPNonSCFVaspInputSet(
            {"NBANDS":60}, mode="Line")

    def test_get_potcar_symbols(self):
        syms = self.paramset.get_potcar_symbols(self.struct)
        self.assertEquals(syms, ['Fe_pv', 'P', 'O'])

    def test_get_incar(self):
        incar = self.paramset.get_incar(self.struct)

        self.assertEqual(incar['LDAUU'], [5.3, 0, 0])
        self.assertAlmostEqual(incar['EDIFF'], 0.0012)

        incar = self.mitparamset.get_incar(self.struct)
        self.assertEqual(incar['LDAUU'], [4.0, 0, 0])
        self.assertAlmostEqual(incar['EDIFF'], 0.0012)

        incar_gga = self.mitggaparam.get_incar(self.struct)
        self.assertNotIn("LDAU", incar_gga)

        incar_static = self.mpstaticparamset.get_incar(self.struct)
        self.assertEqual(incar_static["NSW"], 0)

        incar_nscfl = self.mpnscfparamsetl.get_incar(self.struct)
        self.assertEqual(incar_nscfl["NBANDS"], 60)

        incar_nscfu = self.mpnscfparamsetu.get_incar(self.struct)
        self.assertEqual(incar_nscfu["ISYM"], 0)

        si = 14
        coords = list()
        coords.append(array([0, 0, 0]))
        coords.append(array([0.75, 0.5, 0.75]))

        #Silicon structure for testing.
        latt = Lattice(array([[3.8401979337, 0.00, 0.00],
                              [1.9200989668, 3.3257101909, 0.00],
                              [0.00, -2.2171384943, 3.1355090603]]))
        struct = Structure(latt, [si, si], coords)
        incar = self.paramset.get_incar(struct)
        self.assertNotIn("LDAU", incar)

        incar = self.mithseparamset.get_incar(self.struct)
        self.assertTrue(incar['LHFCALC'])

        coords = list()
        coords.append([0, 0, 0])
        coords.append([0.75, 0.5, 0.75])
        lattice = Lattice([[3.8401979337, 0.00, 0.00],
                           [1.9200989668, 3.3257101909, 0.00],
                           [0.00, -2.2171384943, 3.1355090603]])
        struct = Structure(lattice, ["Fe", "Mn"], coords)

        incar = self.paramset.get_incar(struct)
        self.assertNotIn('LDAU', incar)

        #check fluorides
        struct = Structure(lattice, ["Fe", "F"], coords)
        incar = self.paramset.get_incar(struct)
        self.assertEqual(incar['LDAUU'], [5.3, 0])
        self.assertEqual(incar['MAGMOM'], [5, 0.6])

        struct = Structure(lattice, ["Fe", "F"], coords)
        incar = self.mitparamset.get_incar(struct)
        self.assertEqual(incar['LDAUU'], [4.0, 0])

        #Make sure this works with species.
        struct = Structure(lattice, ["Fe2+", "O2-"], coords)
        incar = self.paramset.get_incar(struct)
        self.assertEqual(incar['LDAUU'], [5.3, 0])

        struct = Structure(lattice, ["Fe", "Mn"], coords,
                           site_properties={'magmom': (5.2, -4.5)})
        incar = self.paramset.get_incar(struct)
        self.assertEqual(incar['MAGMOM'], [5.2, -4.5])
        incar = self.mpstaticparamset.get_incar(struct)
        self.assertEqual(incar['MAGMOM'], [5.2, -4.5])

        struct = Structure(lattice, [Specie("Fe", 2, {'spin':4.1}), "Mn"],
                           coords)
        incar = self.paramset.get_incar(struct)
        self.assertEqual(incar['MAGMOM'], [4.1, 5])
        incar = self.mpnscfparamsetl.get_incar(struct)
        self.assertEqual(incar.get('MAGMOM', None), None)

        struct = Structure(lattice, ["Mn3+", "Mn4+"], coords)
        incar = self.mitparamset.get_incar(struct)
        self.assertEqual(incar['MAGMOM'], [4, 3])
        incar = self.mpnscfparamsetu.get_incar(struct)
        self.assertEqual(incar.get('MAGMOM', None), None)

        self.assertEqual(self.userparamset.get_incar(struct)['MAGMOM'],
                         [100, 0.6])

        #sulfide vs sulfate test

        coords = list()
        coords.append([0, 0, 0])
        coords.append([0.75, 0.5, 0.75])
        coords.append([0.25, 0.5, 0])

        struct = Structure(lattice, ["Fe", "Fe", "S"], coords)
        incar = self.mitparamset.get_incar(struct)
        self.assertEqual(incar['LDAUU'], [1.9, 0])

        #Make sure Matproject sulfides are ok.
        self.assertNotIn('LDAUU', self.paramset.get_incar(struct))
        self.assertNotIn('LDAUU', self.mpstaticparamset.get_incar(struct))

        struct = Structure(lattice, ["Fe", "S", "O"], coords)
        incar = self.mitparamset.get_incar(struct)
        self.assertEqual(incar['LDAUU'], [4.0, 0, 0])

        #Make sure Matproject sulfates are ok.
        self.assertEqual(self.paramset.get_incar(struct)['LDAUU'], [5.3, 0, 0])
        self.assertEqual(self.mpnscfparamsetl.get_incar(struct)['LDAUU'],
                         [5.3, 0, 0])

        self.assertEqual(self.userparamset.get_incar(struct)['MAGMOM'],
                         [10, -5, 0.6])


    def test_get_kpoints(self):
        kpoints = self.paramset.get_kpoints(self.struct)
        self.assertEquals(kpoints.kpts, [[2, 4, 5]])
        self.assertEquals(kpoints.style, 'Monkhorst')

        kpoints = self.mitparamset.get_kpoints(self.struct)
        self.assertEquals(kpoints.kpts, [[2, 4, 5]])
        self.assertEquals(kpoints.style, 'Monkhorst')

        kpoints = self.mpstaticparamset.get_kpoints(self.struct)
        self.assertEquals(kpoints.kpts, [[3, 5, 6]])
        self.assertEquals(kpoints.style, 'Monkhorst')

        kpoints = self.mpnscfparamsetl.get_kpoints(self.struct)
        self.assertEquals(kpoints.num_kpts, 140)
        self.assertEquals(kpoints.style, 'Reciprocal')

        kpoints = self.mpnscfparamsetu.get_kpoints(self.struct)
        self.assertEquals(kpoints.num_kpts, 168)

    def test_to_from_dict(self):
        self.mitparamset = MITVaspInputSet()
        self.mithseparamset = MITHSEVaspInputSet()
        self.paramset = MPVaspInputSet()
        self.userparamset = MPVaspInputSet(
            {'MAGMOM': {"Fe": 10, "S": -5, "Mn3+": 100}}
        )

        d = self.mitparamset.to_dict
        v = dec.process_decoded(d)
        self.assertEqual(type(v), MITVaspInputSet)

        d = self.mitggaparam.to_dict
        v = dec.process_decoded(d)
        self.assertEqual(type(v), MITGGAVaspInputSet)

        d = self.mithseparamset.to_dict
        v = dec.process_decoded(d)
        self.assertEqual(type(v), MITHSEVaspInputSet)

        d = self.paramset.to_dict
        v = dec.process_decoded(d)
        self.assertEqual(type(v), MPVaspInputSet)

        d = self.userparamset.to_dict
        v = dec.process_decoded(d)
        self.assertEqual(type(v), MPVaspInputSet)
        self.assertEqual(v.incar_settings["MAGMOM"],
                         {"Fe": 10, "S": -5, "Mn3+": 100})


class MITMDVaspInputSetTest(unittest.TestCase):

    def setUp(self):
        filepath = os.path.join(test_dir, 'POSCAR')
        poscar = Poscar.from_file(filepath)
        self.struct = poscar.structure
        self.mitmdparam = MITMDVaspInputSet(300, 1200, 10000)

    def test_get_potcar_symbols(self):
        syms = self.mitmdparam.get_potcar_symbols(self.struct)
        self.assertEquals(syms, ['Fe', 'P', 'O'])

    def test_get_incar(self):
        incar = self.mitmdparam.get_incar(self.struct)
        self.assertNotIn("LDAUU", incar)
        self.assertAlmostEqual(incar['EDIFF'], 2.4e-5)

    def test_get_kpoints(self):
        kpoints = self.mitmdparam.get_kpoints(self.struct)
        self.assertEquals(kpoints.kpts, [(1, 1, 1)])
        self.assertEquals(kpoints.style, 'Gamma')

    def test_to_from_dict(self):
        d = self.mitmdparam.to_dict
        v = dec.process_decoded(d)
        self.assertEqual(type(v), MITMDVaspInputSet)
        self.assertEqual(v.incar_settings["TEBEG"], 300)

if __name__ == '__main__':
    unittest.main()
