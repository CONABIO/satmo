from setuptools import setup, find_packages

setup(name='satmo',
      version='0.0.1',
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
          'jinja2',
          'pyproj',
          'affine',
          'rasterio',
          'netCDF4',
          'matplotlib',
          'numpy'], # Recent version required for Basemap
      scripts=['satmo/scripts/timerange_download.py',
               'satmo/scripts/timerange_extract.py'],
      package_data={'satmo': ['templates/*']},
      test_suite="tests")
