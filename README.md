# fits-spase-mapping
Repository for mapping FITS metadata to SPASE metadata schema

### <b><u>fits_spase_mapping.py</u></b>:
This is the primary script for extracting FITS metadata and transferring it to the appropriate location the SPASE schema.
It contains dictionaries with the mapped keywords as well as individual functions for mapping to the appropriate SPASE container within a NumericalData record.

### <b><u>fits_spase_json.py</u></b>:
This script includes functionality for parsing webpages that have links to several FITS files and extracting the unique metadata from their headers.
