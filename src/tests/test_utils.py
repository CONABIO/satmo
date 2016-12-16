import satmo
import unittest
from datetime import datetime, date, time

class TestUtils(unittest.TestCase):

    def test_parse(self):
        file_name_terra = 'random/textT2002003002500.L1A_LAC.bz2'
        file_name_geo_sub = '/test_data/terra/L2/2012/009/T2012009172500.GEO.sub'
        parsed_dict_terra = {'sensor': 'terra',
                       'date': date(2002, 1, 3),
                       'time': time(0, 25),
                       'year': 2002,
                       'month': 1,
                       'doy': 3,
                       'dom': 3,
                       'level': 'L1A',
                       'filename': 'T2002003002500.L1A_LAC.bz2'}
        parsed_dict_geo_sub = {'sensor': 'terra',
                               'date': date(2012, 1, 9),
                               'time': time(17, 25),
                               'year': 2012,
                               'month': 1,
                               'doy': 9,
                               'dom': 9,
                               'level': 'GEO',
                               'filename': 'T2012009172500.GEO.sub'}
        # file name without pattern
        landsat_file_name = 'LE71640572016196SG100'
        # correct pattern, sensor doesn't exist
        file_name_key_error = 'W2002003002500.L1A_LAC.bz2'
        self.assertEqual(satmo.parse_file_name(file_name_terra), parsed_dict_terra)
        self.assertEqual(satmo.parse_file_name(file_name_geo_sub), parsed_dict_geo_sub)
        with self.assertRaises(ValueError):
            satmo.parse_file_name(landsat_file_name)
        with self.assertRaises(KeyError):
            satmo.parse_file_name(file_name_key_error)

    def test_make_path(self):
        file_name = 'T2013001043500.L1A_LAC'
        self.assertEqual(satmo.make_file_path(file_name), 'terra/L1A/2013/001/T2013001043500.L1A_LAC')
        self.assertEqual(satmo.make_file_path(file_name, add_file = False), 'terra/L1A/2013/001')
        self.assertEqual(satmo.make_file_path(file_name, add_file = False, doy = False), 'terra/L1A/2013')
        self.assertEqual(satmo.make_file_path(file_name, add_file = True, doy = False), 'terra/L1A/2013/T2013001043500.L1A_LAC')
        self.assertEqual(satmo.make_file_path(file_name, add_file = True, doy = False, level = 'L3m'), 'terra/L3m/2013')
        with self.assertRaises(ValueError):
            satmo.make_file_path(file_name, add_file = False, doy = True, level = 'L3M')

    def test_make_file_name(self):
        file_name = 'T2005007002500.L2_LAC_OC.nc'
        self.assertEqual(satmo.make_file_name(file_name, 'L3b', 'SST'), 'T2005007.L3b_DAY_SST.nc')
        self.assertEqual(satmo.make_file_name(file_name, 'L3b', 'SST4', '.tif'), 'T2005007.L3b_DAY_SST4.tif')
        with self.assertRaises(ValueError):
            satmo.make_file_name(file_name, 'L3c', 'SST')

if __name__ == '__main__':
    unittest.main()