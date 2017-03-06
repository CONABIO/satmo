import satmo
import unittest

class TestUtils(unittest.TestCase):

    file_1 = 'T2014027.L3m_DAY_CHL_chlor_a_250m.tif'
    file_2 = 'X2014027.L3m_DAY_SST_sst_1km.tif'
    file_3 = '/path/to/file/X2014027.L3m_8DAY_SST_sst_1km.tif'
    file_4 = 'CLIM.027.L3m_8DAY_SST_sst4_1km_2000_2015.tif'
    file_5 = 'Z2003027.L3m_8DAY_SST_sst_1km.tif' # Invalid

    def test_make_map_title(self):
        title_1 = 'Daily chlor_a terra 2014-01-27 250m'
        title_2 = 'Daily sst combined 2014-01-27 1km'
        title_3 = '8 day composite sst combined 2014-01-27 1km'
        title_4 = '8 day composite sst4 climatology January 27 1km'
        self.assertEqual(satmo.make_map_title(self.file_1), title_1)
        self.assertEqual(satmo.make_map_title(self.file_2), title_2)
        self.assertEqual(satmo.make_map_title(self.file_3), title_3)
        self.assertEqual(satmo.make_map_title(self.file_4), title_4)
        self.assertEqual(satmo.make_map_title(self.file_5), self.file_5)

    # def test_var_name_extraction(self):
    #     # Helper function not exported to satmo __init__
    #     self.assertEqual(satmo.visualization.get_var_name(self.file_1), 'chlor_a')
    #     self.assertEqual(satmo.visualization.get_var_name(self.file_2), 'sst')
    #     self.assertEqual(satmo.visualization.get_var_name(self.file_3), 'sst')
    #     self.assertEqual(satmo.visualization.get_var_name(self.file_4), 'sst4')
    #     self.assertEqual(satmo.visualization.get_var_name(self.file_5), 'sst')


if __name__ == '__main__':
    unittest.main()

