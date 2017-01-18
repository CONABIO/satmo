# Global variable that contains sensor information
SENSOR_CODES = {'A': 'aqua',
                'T': 'terra',
                'S': 'seawifs',
                'V': 'viirs',
                'O': 'octs',
                'C': 'czcs',
                'M': 'meris',
                'H': 'hico',
                'X': 'combined'} # 'combined' is not a sensor, but the name given to combined multisensors
                                 # products

DATA_LEVELS = ['L0', 'L1A', 'L1B', 'L2', 'L3b', 'L3m']

PRODUCT_SUITES = {'RRS': {'terra': ['Rrs_412','Rrs_443','Rrs_469','Rrs_488',
                                    'Rrs_531','Rrs_547','Rrs_555','Rrs_645',
                                    'Rrs_667','Rrs_678','Rrs_748','Rrs_859',
                                    'Rrs_869','Rrs_1240','Rrs_1640','Rrs_2130'],
                          'viirs': ['Rrs_410','Rrs_443','Rrs_486','Rrs_551',
                                    'Rrs_671','Rrs_745','Rrs_862','Rrs_1238',
                                    'Rrs_1601','Rrs_2257'],
                          'aqua': ['Rrs_412','Rrs_443','Rrs_469','Rrs_488',
                                   'Rrs_531','Rrs_547','Rrs_555','Rrs_645',
                                   'Rrs_667','Rrs_678','Rrs_748','Rrs_859',
                                   'Rrs_869','Rrs_1240','Rrs_1640','Rrs_2130'],
                           'seawifs': ['Rrs_412','Rrs_443','Rrs_490','Rrs_510',
                                       'Rrs_555','Rrs_670','Rrs_765','Rrs_865'],
                            'meris': ['Rrs_413','Rrs_443','Rrs_490','Rrs_510',
                                      'Rrs_560','Rrs_620','Rrs_665','Rrs_681',
                                      'Rrs_709','Rrs_779','Rrs_754','Rrs_762',
                                      'Rrs_865','Rrs_885','Rrs_900']},
                  'SST': {'terra': ['sst'],
                          'aqua': ['sst'],
                          'viirs': ['sst'],
                          'seawifs': ['sst'],
                          'meris': ['sst']},
                  'SST4': {'terra': ['sst4'],
                           'aqua': ['sst4'],
                           'viirs': ['sst4'],
                           'seawifs': ['sst4'],
                           'meris': ['sst4']},
                  'PAR': {'terra': ['par', 'ipar'],
                           'aqua': ['par', 'ipar'],
                           'viirs': ['par', 'ipar'],
                           'seawifs': ['par', 'ipar'],
                           'meris': ['par', 'ipar']},
                  'NSST': {'terra': ['nsst'],
                          'aqua': ['nsst'],
                          'viirs': ['nsst'],
                          'seawifs': ['nsst'],
                          'meris': ['nsst']}}

# Rrc (Rayleight corrected reflectance), used by Hu are called rhos in seadas


INDICES = {'OC3' : {'modis': {'reflectances': 'RRS',
                              'bands': ['blue', 'green']},
                              'RRS': {'blue': [],
                                      'green': []}},
                    'stretch': {'vmin': 0, 'vmax': 3}}

COMPOSITES = {'DAY': 'Daily',
              '8DAY': '8 day composite',
              '16DAY': '16 day composite',
              'MON': 'Monthly composite'}