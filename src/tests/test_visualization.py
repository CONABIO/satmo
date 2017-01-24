import satmo
import unittest

class TestUtils(unittest.TestCase):

    def test_make_map_title(self):
        file_1 = 'T2014027.L3m_DAY_CHL_chlor_a_250m.tif'
        title_1 = 'Daily chlor_a terra 2014-01-27 250m'
        file_2 = 'X2014027.L3m_DAY_SST_sst_1km.tif'
        title_2 = 'Daily sst combined 2014-01-27 1km'
        file_3 = '/path/to/file/X2014027.L3m_8DAY_SST_sst_1km.tif'
        title_3 = '8 day composite sst combined 2014-01-27 1km'
        file_4 = 'XCLIM027.L3m_8DAY_SST4_sst4_1km.tif'
        title_4 = '8 day composite sst4 climatology January 27 1km'
        file_5 = 'Z2003027.L3m_8DAY_SST_sst_1km.tif' # Invalid 
        self.assertEqual(satmo.make_map_title(file_1), title_1)
        self.assertEqual(satmo.make_map_title(file_2), title_2)
        self.assertEqual(satmo.make_map_title(file_3), title_3)
        self.assertEqual(satmo.make_map_title(file_4), title_4)
        self.assertEqual(satmo.make_map_title(file_5), file_5)

if __name__ == '__main__':
    unittest.main()

