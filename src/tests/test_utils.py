import satmo
import unittest
from datetime import datetime, date, time

class TestUtils(unittest.TestCase):

    def test_parse(self):
        file_name_terra = 'random/textT2002003002500.L1A_LAC.bz2'
        parsed_dict = {'sensor': 'terra',
                       'date': date(2002, 1, 3),
                       'time': time(0, 25),
                       'year': 2002,
                       'month': 1,
                       'doy': 3,
                       'dom': 3,
                       'level': 'L1A',
                       'filename': 'T2002003002500.L1A_LAC.bz2'}
        # file name without pattern
        landsat_file_name = 'LE71640572016196SG100'
        # correct pattern, sensor doesn't exist
        file_name_key_error = 'W2002003002500.L1A_LAC.bz2'
        self.assertEqual(satmo.parse_file_name(file_name_terra), parsed_dict)
        with self.assertRaises(ValueError):
            satmo.parse_file_name(landsat_file_name)
        with self.assertRaises(KeyError):
            satmo.parse_file_name(file_name_key_error)


if __name__ == '__main__':
    unittest.main()