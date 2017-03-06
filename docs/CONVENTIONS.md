## SATMO file naming conventions

### Quick reference

|     Product type     |                Example filename               |         parser         | builder |           Directory           |
|----------------------|-----------------------------------------------|------------------------|---------|-------------------------------|
| L1A                  | `A2005004002500.L1A_LAC.bz2`                  | `OC_filename_parser()` |         | `aqua/L1A/2005/004`           |
| L2                   | `A2008085203500.L2_LAC_OC.nc`                 | `OC_filename_parser()` |         | `aqua/L2/2008/085`            |
| L3b                  | `A2004005.L3b_DAY_CHL.nc`                     | `OC_filename_parser()` |         | `aqua/L3b/2004/005`           |
| L3m ncdf             | `A2007009.L3m_DAY_SST4_sst4_1km.nc`           | `OC_filename_parser()` |         | `aqua/L3m/Daily/2007/009`     |
| L3m sensor composite | `X2014027.L3m_DAY_SST_sst_1km.tif`            | `OC_filename_parser()` |         | `combined/L3m/Daily/2014/027` |
| L3m time composite   | `X2014027.L3m_8DAY_SST_sst_1km.tif`           | `OC_filename_parser()` |         | `combined/L3m/8Day/2014/027`  |
| L3m climatology      | `CLIM.027.L3m_8DAY_SST_sst_1km_2000_2015.tif` | `OC_filename_parser()` |         | `combined/L3m/8Day_clim/027`  |
| L3m anomalies        | `ANOM.2014027.L3m_8DAY_SST_sst_1km.tif`       | `OC_filename_parser()` |         | `combined/L3m/8Day_anom/027`  |
| preview              | `X2014027.L3m_DAY_SST_sst_1km.png`            | `OC_filename_parser()` |         |                               |
|                      |                                               |                        |         |                               |
| ??L3m Cumulative     | `X2014027.L3m_8DAY_SST_sst_1km.tif`?          |                        |         |                               |


