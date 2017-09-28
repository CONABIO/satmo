from setuptools import setup, find_packages
import itertools

# Parse the version from the satmo module.
with open('satmo/__init__.py') as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            continue

# 
extra_reqs = {'docs': ['sphinx', 'sphinx-rtd-theme']}
extra_reqs['all'] = list(set(itertools.chain(*extra_reqs.values())))

setup(name='satmo',
      version=version,
      description=u"Fonctionalities to query, download, process and manipulate data for the SATMO project",
      classifiers=[],
      keywords='Ocean color, MODIS, VIIRS, SeaWifs, NASA',
      author=u"Loic Dutrieux",
      author_email='loic.dutrieux@conabio.gob.mx',
      url='https://github.com/CONABIO/satmo.git',
      license='GPLv3',
      packages=find_packages(),
      install_requires=[
          'requests==2.18.4',
          'python-dateutil==2.6.1',
          'pyproj==1.9.5.1',
          'affine==2.1.0',
          'rasterio==0.36.0',
          'netCDF4==1.3.0',
          'matplotlib==2.0.2',
          'cartopy==0.15.1',
          'scipy==0.19.1',
          'numpy==1.13.1',
          'schedule==0.4.3',
          'pint==0.8.1'],
      scripts=['satmo/scripts/timerange_download.py',
               'satmo/scripts/timerange_L2_process.py',
               'satmo/scripts/timerange_L2_append.py',
               'satmo/scripts/timerange_L2m_process.py',
               'satmo/scripts/timerange_bin_map.py',
               'satmo/scripts/timerange_time_compositing.py',
               'satmo/scripts/timerange_daily_composite.py',
               'satmo/scripts/satmo_nrt.py',
               'satmo/scripts/make_preview.py'],
      test_suite="tests",
      extras_require=extra_reqs)
