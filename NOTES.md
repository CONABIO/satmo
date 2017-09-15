- Ask on forum whether files processed with `multilevel_processor.py` are definitive wrt ancillary data
- How to pass ancdir (`getanc.py`) to `multilevel-processor.py`
- TO avoid crashes when extracting (because of swath outside of extent), the extent of `query_from_extent` should be smaller than `extractJob.extract` extent.
- VIIRS:
    - l1aextract_viirs is not yet part of the `multilevel_processor.py`
    - GEO files (required for many things) can be downloaded from the oceancolor servers. TO be able to generate these files directly from L1A source files, a gigantic DEM is needed
- Lots of algorithms with formulas here http://oceancolor.gsfc.nasa.gov/cms/atbd
- VIIRS nc files have internal compression (I think)
- Handle sub files in download updating mode??
- Would it be possible to symlink all drives to have a vituarl satmo root with all the data?
- `matplotlib.basemap` installed for testing (131 MB package) using `pip install https://github.com/matplotlib/basemap/archive/v1.0.7rel.tar.gz`


Add `Alternative floating algae index:afai:dimensionless:linear:-1:1:F:default` to $OCDATAROOT/common/smigen_product_table.dat to allow l2mapgen to work with custom products