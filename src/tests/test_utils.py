import satmo
import unittest
from datetime import datetime, date, time

class TestUtils(unittest.TestCase):

    def test_OC_filename_parser(self):
        f1 = 'getfile/A2005004002500.L1A_LAC.bz2'
        d1 = {'anomaly': False,
             'begin_year': None,
             'climatology': False,
             'composite': None,
             'date': date(2005, 1, 4),
             'dom': 4,
             'doy': 4,
             'end_year': None,
             'filename': 'A2005004002500.L1A_LAC.bz2',
             'level': 'L1A',
             'month': 1,
             'resolution': None,
             'sensor': 'aqua',
             'sensor_code': 'A',
             'suite': None,
             'time': time(0, 25, 00),
             'variable': None,
             'year': 2005}

        f2 = 'A2008085203500.L2_LAC_OC.nc'
        d2 = {'anomaly': False,
             'begin_year': None,
             'climatology': False,
             'composite': None,
             'date': date(2008, 3, 25),
             'dom': 25,
             'doy': 85,
             'end_year': None,
             'filename': 'A2008085203500.L2_LAC_OC.nc',
             'level': 'L2',
             'month': 3,
             'resolution': None,
             'sensor': 'aqua',
             'sensor_code': 'A',
             'suite': 'OC',
             'time': time(20, 35, 00),
             'variable': None,
             'year': 2008}

        f3 = 'A2004005.L3b_DAY_CHL.nc'
        d3 = {'anomaly': False,
             'begin_year': None,
             'climatology': False,
             'composite': None,
             'date': date(2004, 1, 5),
             'dom': 5,
             'doy': 5,
             'end_year': None,
             'filename': 'A2004005.L3b_DAY_CHL.nc',
             'level': 'L3b',
             'month': 1,
             'resolution': None,
             'sensor': 'aqua',
             'sensor_code': 'A',
             'suite': 'CHL',
             'time': None,
             'variable': None,
             'year': 2004}

        f4 = 'A2007009.L3m_DAY_SST4_sst4_1km.nc'
        d4 = {'anomaly': False,
             'begin_year': None,
             'climatology': False,
             'composite': 'DAY',
             'date': date(2007, 1, 9),
             'dom': 9,
             'doy': 9,
             'end_year': None,
             'filename': 'A2007009.L3m_DAY_SST4_sst4_1km.nc',
             'level': 'L3m',
             'month': 1,
             'resolution': '1km',
             'sensor': 'aqua',
             'sensor_code': 'A',
             'suite': 'SST4',
             'time': None,
             'variable': 'sst4',
             'year': 2007}

        f5 = 'X2014027.L3m_DAY_SST_sst_1km.tif'
        d5 = {'anomaly': False,
             'begin_year': None,
             'climatology': False,
             'composite': 'DAY',
             'date': date(2014, 1, 27),
             'dom': 27,
             'doy': 27,
             'end_year': None,
             'filename': 'X2014027.L3m_DAY_SST_sst_1km.tif',
             'level': 'L3m',
             'month': 1,
             'resolution': '1km',
             'sensor': 'combined',
             'sensor_code': 'X',
             'suite': 'SST',
             'time': None,
             'variable': 'sst',
             'year': 2014}

        f6 = 'X2014027.L3m_8DAY_SST_sst_1km.tif'
        d6 = {'anomaly': False,
             'begin_year': None,
             'climatology': False,
             'composite': '8DAY',
             'date': date(2014, 1, 27),
             'dom': 27,
             'doy': 27,
             'end_year': None,
             'filename': 'X2014027.L3m_8DAY_SST_sst_1km.tif',
             'level': 'L3m',
             'month': 1,
             'resolution': '1km',
             'sensor': 'combined',
             'sensor_code': 'X',
             'suite': 'SST',
             'time': None,
             'variable': 'sst',
             'year': 2014}

        f7 = 'CLIM.027.L3m_8DAY_CHL_chlor_a_1km_2000_2015.tif'
        d7 = {'anomaly': False,
             'begin_year': 2000,
             'climatology': True,
             'composite': '8DAY',
             'date': None,
             'dom': None,
             'doy': 27,
             'end_year': 2015,
             'filename': 'CLIM.027.L3m_8DAY_CHL_chlor_a_1km_2000_2015.tif',
             'level': 'L3m',
             'month': None,
             'resolution': '1km',
             'sensor': None,
             'sensor_code': None,
             'suite': 'CHL',
             'time': None,
             'variable': 'chlor_a',
             'year': None}

        f8 = 'ANOM.2014027.L3m_8DAY_SST_sst_1km.tif'
        d8 = {'anomaly': True,
             'begin_year': None,
             'climatology': False,
             'composite': '8DAY',
             'date': date(2014, 1, 27),
             'dom': 27,
             'doy': 27,
             'end_year': None,
             'filename': 'ANOM.2014027.L3m_8DAY_SST_sst_1km.tif',
             'level': 'L3m',
             'month': 1,
             'resolution': '1km',
             'sensor': None,
             'sensor_code': None,
             'suite': 'SST',
             'time': None,
             'variable': 'sst',
             'year': 2014}

        self.assertEqual(satmo.OC_filename_parser(f1), d1)
        self.assertEqual(satmo.OC_filename_parser(f2), d2)
        self.assertEqual(satmo.OC_filename_parser(f3), d3)
        self.assertEqual(satmo.OC_filename_parser(f4), d4)
        self.assertEqual(satmo.OC_filename_parser(f5), d5)
        self.assertEqual(satmo.OC_filename_parser(f6), d6)
        self.assertEqual(satmo.OC_filename_parser(f7), d7)
        self.assertEqual(satmo.OC_filename_parser(f8), d8)

    def test_OC_filename_builder(self):

        d1_0 = {'level': 'L2', 'filename': 'A2008085203500.L1A_LAC.bz2', 'suite': 'OC'}
        d1_1 = {'level': 'L2', 'sensor_code': 'A', 'date': datetime(2008, 03, 25), 'time': time(20, 35, 00), 'suite': 'OC'}
        d1_2 = {'level': 'L2', 'sensor_code': 'A', 'date': '2008-03-25', 'time': time(20, 35, 00), 'suite': 'OC'}
        f1 = 'A2008085203500.L2_LAC_OC.nc'
        d2_0 = {'level': 'L2', 'filename': 'A2008085203500.L1A_LAC.bz2', 'suite': 'OC', 'full_path': True}
        f2 = 'aqua/L2/2008/085/A2008085203500.L2_LAC_OC.nc'
        d3_0 = {'level': 'L2', 'filename': 'A2008085203500.L1A_LAC.bz2', 'suite': 'OC', 'full_path': True, 'data_root': '/media/system/satmo/'}
        f3 = '/media/system/satmo/aqua/L2/2008/085/A2008085203500.L2_LAC_OC.nc'
        d4_0 = {'level': 'L3b', 'filename': 'A2004005203500.L2_LAC_OC.nc', 'suite': 'CHL'}
        d4_1 = {'level': 'L3b', 'sensor_code': 'A', 'date': datetime(2004, 01, 5), 'suite': 'CHL'}
        f4 = 'A2004005.L3b_DAY_CHL.nc'
        d5_0 = {'level': 'L3b', 'sensor_code': 'A', 'date': datetime(2004, 01, 5), 'suite': 'CHL', 'full_path': True}
        f5 = 'aqua/L3b/2004/005/A2004005.L3b_DAY_CHL.nc'
        d6_0 = {'level': 'L3m', 'climatology': True, 'doy': 27, 'composite': '8DAY', 'suite': 'SST', 'variable': 'sst', 'resolution': '1km',
                'begin_year': 2000, 'end_year': 2015}
        d6_1 = {'level': 'L3m', 'climatology': True, 'date': datetime(1970, 01, 27), 'composite': '8DAY', 'suite': 'SST', 'variable': 'sst', 'resolution': '1km',
                'begin_year': 2000, 'end_year': 2015}
        f6 = 'CLIM.027.L3m_8DAY_SST_sst_1km_2000_2015.tif'
        d7_0 = {'level': 'L3m', 'climatology': True, 'date': datetime(1970, 01, 27), 'composite': '8DAY', 'suite': 'SST', 'variable': 'sst', 'resolution': '1km',
                'begin_year': 2000, 'end_year': 2015, 'full_path': True}
        f7 = 'combined/L3m/8DAY_clim/027/CLIM.027.L3m_8DAY_SST_sst_1km_2000_2015.tif'
        d8_0 = {'level': 'L3m', 'anomaly': True, 'filename': 'X2014027.L3m_8DAY_SST_sst_1km.tif'}
        d8_1 = {'level': 'L3m', 'anomaly': True, 'date': datetime(2014, 1, 27), 'composite': '8DAY', 'suite': 'SST', 'variable': 'sst', 'resolution': '1km'}
        f8 = 'ANOM.2014027.L3m_8DAY_SST_sst_1km.tif'
        d9_0 = {'level': 'L3m', 'anomaly': True, 'filename': 'X2014027.L3m_8DAY_SST_sst_1km.tif', 'full_path': True}
        f9 = 'combined/L3m/8DAY_anom/2014/027/ANOM.2014027.L3m_8DAY_SST_sst_1km.tif'
        d10_0 = {'level': 'L3m', 'filename': 'A2004005.L3b_DAY_CHL.nc', 'composite': 'DAY', 'variable': 'chlor_a', 'resolution': '1km', 'nc': True}
        d10_1 = {'level': 'L3m', 'date': datetime(2004, 01, 5), 'sensor_code': 'A', 'suite': 'CHL', 'composite': 'DAY', 'variable': 'chlor_a', 'resolution': '1km', 'nc': True}
        f10 = 'A2004005.L3m_DAY_CHL_chlor_a_1km.nc'
        d11_0 = {'level': 'L3m', 'filename': 'A2004005.L3b_DAY_CHL.nc', 'composite': 'DAY', 'variable': 'chlor_a', 'resolution': '1km'}
        f11 = 'A2004005.L3m_DAY_CHL_chlor_a_1km.tif'
        d12_0 = {'level': 'L3m', 'filename': 'A2004005.L3b_DAY_CHL.nc', 'composite': 'DAY', 'variable': 'chlor_a', 'resolution': '1km', 'full_path': True}
        f12 = 'aqua/L3m/DAY/2004/005/A2004005.L3m_DAY_CHL_chlor_a_1km.tif'


        self.assertEqual(satmo.OC_filename_builder(**d1_0), f1)
        self.assertEqual(satmo.OC_filename_builder(**d1_1), f1)
        self.assertEqual(satmo.OC_filename_builder(**d1_2), f1)
        self.assertEqual(satmo.OC_filename_builder(**d2_0), f2)
        self.assertEqual(satmo.OC_filename_builder(**d3_0), f3)
        self.assertEqual(satmo.OC_filename_builder(**d4_0), f4)
        self.assertEqual(satmo.OC_filename_builder(**d4_1), f4)
        self.assertEqual(satmo.OC_filename_builder(**d5_0), f5)
        self.assertEqual(satmo.OC_filename_builder(**d6_0), f6)
        self.assertEqual(satmo.OC_filename_builder(**d6_1), f6)
        self.assertEqual(satmo.OC_filename_builder(**d7_0), f7)
        self.assertEqual(satmo.OC_filename_builder(**d8_0), f8)
        self.assertEqual(satmo.OC_filename_builder(**d8_1), f8)
        self.assertEqual(satmo.OC_filename_builder(**d9_0), f9)
        self.assertEqual(satmo.OC_filename_builder(**d10_0), f10)
        self.assertEqual(satmo.OC_filename_builder(**d10_1), f10)
        self.assertEqual(satmo.OC_filename_builder(**d11_0), f11)
        self.assertEqual(satmo.OC_filename_builder(**d12_0), f12)


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

    def test_file_path_from_sensor_date(self):
        date_dt = datetime(2007, 02, 23) # doy: 54
        date_str = '2007-02-23'
        sensor = 'aqua'
        data_root = '/media/user/data/test'
        self.assertEqual(satmo.file_path_from_sensor_date('aqua', date_dt, data_root), '/media/user/data/test/aqua/L1A/2007/054')
        self.assertEqual(satmo.file_path_from_sensor_date('aqua', date_str, data_root, 'L2'), '/media/user/data/test/aqua/L2/2007/054')
        self.assertEqual(satmo.file_path_from_sensor_date('aqua', date_str, data_root, 'L3m', doy = False), '/media/user/data/test/aqua/L3m/2007')
        with self.assertRaises(ValueError):
            satmo.file_path_from_sensor_date('aqua', date_dt, data_root, 'L3')

if __name__ == '__main__':
    unittest.main()