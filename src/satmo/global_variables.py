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


# See seadas defaults in /seadas/run/data/{sensor}/l2bin_defaults_{suite}.par
STANDARD_L3_SUITES = {'RRS': {'terra': ['Rrs_412','Rrs_443','Rrs_469','Rrs_488',
                                            'Rrs_531','Rrs_547','Rrs_555','Rrs_645',
                                            'Rrs_667','Rrs_678'],
                                   'viirs': ['Rrs_410','Rrs_443','Rrs_486','Rrs_551',
                                            'Rrs_671'],
                                   'aqua': ['Rrs_412','Rrs_443','Rrs_469','Rrs_488',
                                           'Rrs_531','Rrs_547','Rrs_555','Rrs_645',
                                           'Rrs_667','Rrs_678'],
                                   'seawifs': ['Rrs_412','Rrs_443','Rrs_490','Rrs_510',
                                               'Rrs_555','Rrs_670'],
                                   'meris': ['Rrs_413','Rrs_443','Rrs_490','Rrs_510',
                                            'Rrs_560','Rrs_620','Rrs_665','Rrs_681',
                                            'Rrs_709']},
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
                            'PAR': {'terra': ['par'],
                                     'aqua': ['par'],
                                     'viirs': ['par'],
                                     'seawifs': ['par'],
                                     'meris': ['par']},
                            'NSST': {'terra': ['sst'],
                                    'aqua': ['sst'],
                                    'viirs': ['sst'],
                                    'seawifs': ['sst'],
                                    'meris': ['sst']},
                            'CHL': {'terra': ['chlor_a', 'chl_ocx'],
                                    'aqua': ['chlor_a', 'chl_ocx'],
                                    'viirs': ['chlor_a', 'chl_ocx'],
                                    'seawifs': ['chlor_a', 'chl_ocx'],
                                    'meris': ['chlor_a']},
                            'KD490': {'terra': ['Kd_490'],
                                      'aqua': ['Kd_490'],
                                      'viirs': ['Kd_490'],
                                      'seawifs': ['Kd_490'],
                                      'meris': ['Kd_490']},
                            'FLH': {'aqua': ['nflh', 'ipar'],
                                    'terra': ['nflh', 'ipar']}}

# Rrc (Rayleight corrected reflectance), used by Hu are called rhos in seadas
# 


INDICES = {'chlor_a' : {'algorithm':{'OC3':{'modis': {'reflectances': 'RRS',
                                                     'bands': ['blue', 'green']},
                                                     'RRS': {'blue': [],
                                                          'green': []}}},
                        'stretch': {'vmax': 10},
                        'log': True}}

COMPOSITES = {'DAY': 'Daily',
              '8DAY': '8 day composite',
              '16DAY': '16 day composite',
              'MON': 'Monthly composite'}
