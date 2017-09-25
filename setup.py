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
          'requests',
          'future',
          'python-dateutil',
          'jinja2',
          'pyproj',
          'affine',
          'rasterio',
          'netCDF4',
          'matplotlib',
          'cartopy',
          'scipy',
          'numpy',
          'schedule',
          'pint'],
      scripts=['satmo/scripts/timerange_download.py',
               'satmo/scripts/nc2tif.py',
               'satmo/scripts/timerange_daily_composite.py',
               'satmo/scripts/satmo_nrt.py',
               'satmo/scripts/timerange_time_composite.py',
               'satmo/scripts/timerange_L3m_process.py',
               'satmo/scripts/timerange_bin_map.py',
               'satmo/scripts/timerange_L2m_process.py',
               'satmo/scripts/timerange_L2_process.py',
               'satmo/scripts/timerange_L2_append.py',
               'satmo/scripts/make_preview.py'],
      package_data={'satmo': ['templates/*']},
      test_suite="tests",
      extras_require=extra_reqs)
