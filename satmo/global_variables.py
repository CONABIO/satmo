import re

class SuperDict(dict):
    # Defined here to avoid circular dependencies and because it's only
    # used here anyway
    """Class to enable use of regex patterns as dictionary keys

    Args:
        dict (dict): A dictionary

    Examples:
        >>> a = SuperDict({'rrs_.*': 12, 'chlor_a': 11})
        >>> print a['rrs_555']
        >>> print a['chlor_a']
        >>> print a['random_key']
    """
    def __getitem__(self, word):
        keys = [x for x in self.keys() if re.match(x, word) is not None]
        if len(keys) > 1:
            raise KeyError('Too many matching keys')
        elif len(keys) == 0:
            raise KeyError('No matching keys')
        return dict.__getitem__(self, keys[0])


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

DATA_LEVELS = ['L0', 'L1A', 'L1B', 'L2', 'L2m', 'L3b', 'L3m']


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
                      'FAI': {'terra': ['fai', 'afai'],
                              'aqua': ['fai', 'afai'],
                              'viirs': ['afai']},
                            'FLH': {'aqua': ['nflh', 'ipar'],
                                    'terra': ['nflh', 'ipar']}}

# Rrc (Rayleight corrected reflectance), used by Hu are called rhos in seadas

L2_L3_SUITES_CORRESPONDENCES = {'RRS': 'OC',
                                'FAI': 'FAI',
                                'SST': 'SST',
                                'NSST': 'SST',
                                'SST4': 'SST4',
                                'PAR': 'OC',
                                'CHL': 'OC',
                                'KD490': 'OC',
                                'FLH': 'OC'}




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

SUBSCRIPTIONS = {'L2':{'nrt': {'day': [1823, 1821, 1825],
                               'night': [1824, 1822, 1826]},
                       'refined': {'day': [1857, 1859, 1861],
                                   'night': [1862, 1858, 1860]}},
                 'L1A': {'day': [1954, 1955, 1956],
                         'night': []}}

VARS_FROM_L2_SUITE = {'aqua':{'day':{'OC': ['Rrs_412', 'Rrs_443', 'Rrs_469',
                                            'Rrs_488', 'Rrs_531', 'Rrs_547',
                                            'Rrs_555', 'Rrs_645', 'Rrs_667',
                                            'Rrs_678', 'Kd_490', 'chl_ocx',
                                            'aot_869', 'ipar', 'nflh', 'par',
                                            'pic', 'poc', 'chlor_a'],
                                     'SST': ['sst']},
                              'night':{'SST': ['sst'],
                                       'SST4': ['sst4']}},
                      'terra':{'day':{'OC': ['Rrs_412', 'Rrs_443', 'Rrs_469',
                                             'Rrs_488', 'Rrs_531', 'Rrs_547',
                                             'Rrs_555', 'Rrs_645', 'Rrs_667',
                                             'Rrs_678', 'Kd_490', 'chl_ocx',
                                             'aot_869', 'ipar', 'nflh', 'par',
                                             'pic', 'poc', 'chlor_a'],
                                      'SST': ['sst']},
                               'night':{'SST': ['sst'],
                                        'SST4': ['sst4']}},
                      'viirs':{'day':{'OC': ['Kd_490', 'Rrs_410', 'Rrs_443',
                                             'Rrs_486', 'Rrs_551', 'Rrs_671',
                                             'aot_862', 'chl_ocx', 'chlor_a',
                                             'par', 'pic', 'poc'],
                                      'SST': ['sst']},
                               'night':{'SST': ['sst'],
                                        'SST3': ['sst_triple']}}}

L3_SUITE_FROM_VAR = SuperDict({'day': {'Rrs_.*': 'RRS',
                                       'chlor_a': 'CHL',
                                       'chl_ocx': 'CHL',
                                       'sst': 'SST',
                                       'ipar': 'FLH',
                                       'par': 'PAR',
                                       'pic': 'PIC',
                                       'poc': 'POC',
                                       'nflh': 'FLH',
                                       'fai': 'FAI',
                                       'afai': 'FAI',
                                       'Kd_490': 'KD490'},
                               'night': {'sst': 'NSST',
                                         'sst_triple': 'SST3',
                                         'sst4': 'SST4'}})

BIT_MASK_FROM_L3_SUITE = {'CHL':0x669d73b,
                          'RRS':0x669d73b,
                          'FLH':0x679d73f,
                          'PIC':0x641532b,
                          'PAR':0x600000a,
                          'POC':0x669d73b,
                          'KD490':0x669d73b,
                          'FAI':0x20a, # CLDICE,LAND,HIGLINT
                          'SST':0x1002,
                          'NSST':0x2,
                          'SST3':0x2,
                          'SST4':0x2}

FLAGS = {'CHL':[],
         'RRS':[],
         'FLH':[],
         'PIC':[],
         'PAR':[],
         'POC':[],
         'KD490':[],
         'FAI':['CLDICE','LAND','HIGLINT'],
         'AFAI':['CLDICE','LAND','HIGLINT'],
         'SST':[],
         'NSST':[],
         'SST3':[],
         'SST4':[]}

QUAL_ARRAY_NAME_FROM_SUITE = {'SST': 'qual_sst',
                              'NSST': 'qual_sst',
                              'SST4': 'qual_sst4',
                              'SST3': None, # Not sure about this one (not present in l2bin viirs defaults)
                              'CHL': None,
                              'RRS': None,
                              'FLH': None,
                              'PIC': None,
                              'PAR': None,
                              'POC': None,
                              'FAI': None,
                              'KD490': None}

def afai_viirs(red, nir, swir):
    nir_line = red + (swir - red) * (745 - 671) / (862 - 671)
    return nir - nir_line

def afai_modis(red, nir, swir):
    nir_line = red + (swir - red) * (748 - 667) / (869 - 667)
    return nir - nir_line

def fai_modis(red, nir, swir):
    nir_line = red + (swir - red) * (859 - 645) / (1240 - 645)
    return nir - nir_line

# The keys of the lowest level of nested dict match the l2_append function arguments
# so that they can be passed as kwargs
BAND_MATH_FUNCTIONS = {'afai': {'aqua': {'formula': afai_modis,
                                         'bands': ['rhos_667', 'rhos_748', 'rhos_869'],
                                         'standard_name': 'afai',
                                         'short_name': 'afai',
                                         'valid_min': -1.,
                                         'valid_max': 1.,
                                         'long_name': 'Alternative floating algae index'},
                                'terra':{'formula': afai_modis,
                                         'bands': ['rhos_667', 'rhos_748', 'rhos_869'],
                                         'standard_name': 'afai',
                                         'short_name': 'afai',
                                         'valid_min': -1.,
                                         'valid_max': 1.,
                                         'long_name': 'Alternative floating algae index'},
                                'viirs':{'formula': afai_viirs,
                                         'bands': ['rhos_671', 'rhos_745', 'rhos_862'],
                                         'standard_name': 'afai',
                                         'short_name': 'afai',
                                         'valid_min': -1.,
                                         'valid_max': 1.,
                                         'long_name': 'Alternative floating algae index'}},
                       'fai': {'aqua': {'formula': fai_modis,
                                        'bands': ['rhos_645', 'rhos_859', 'rhos_1240'],
                                        'standard_name': 'fai',
                                        'short_name': 'fai',
                                        'valid_min': -1.,
                                        'valid_max': 1.,
                                        'long_name': 'Floating algae index'},
                               'terra': {'formula': fai_modis,
                                        'bands': ['rhos_645', 'rhos_859', 'rhos_1240'],
                                        'standard_name': 'fai',
                                        'short_name': 'fai',
                                        'valid_min': -1.,
                                        'valid_max': 1.,
                                        'long_name': 'Floating algae index'}}}


