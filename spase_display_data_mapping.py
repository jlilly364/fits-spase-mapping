from astropy.io import fits
from datetime import datetime, timedelta
#import html
import json
import lxml
from lxml import etree
import xml.etree.ElementTree as ET
import numpy as np
import os
import pandas as pd
from pathlib import Path
import re
import requests
import subprocess
import time

# Dict of fields that map to ResourceHeader Description
"""resourceHeaderDescription = {"CAMERA":"Description","CAR_ROT":"Description",
                             "CRS_DESC":"Description","CRS:TYPE":"Description",
                             "CTYPE1":"Description","CTYPE2":"Description",
                             "CUNIT1":"Description","CUNIT2":"Description",
                             "DESCRPTN":"Description","FILTER":"Description",
                             "GRATING":"Description","HISTORY":"Description",
                             "OBJECT":"Description","OBS_DESC":"Description",
                             "OBS_ID":"Description","OBS_MODE":"Description",
                             "TELCONFG":"Description","TEXPOSUR":"Description",
                             "TDESCn":"Description","UCD":"Description",
                             "EXPTIME":"Description","XPOSURE":"Description"}"""

# Not mapped in FITS: ResourceID, Contact>Role,
#                     AccessInformation>(RepositoryID,AccessURL)
# Dict of fields that map within DisplayData            
displayDataMap = {"OBSTITLE":"ResourceName","TITLE":"ResourceName",
                  "RELEASE":"ReleaseDate",

                  "CAMERA":"Description","CAR_ROT":"Description",
                  "CRS_DESC":"Description","CRS:TYPE":"Description",
                  "CTYPE1":"Description","CTYPE2":"Description",
                  "CUNIT1":"Description","CUNIT2":"Description",
                  "DESCRPTN":"Description","FILTER":"Description",
                  "GRATING":"Description","HISTORY":"Description",
                  "OBJECT":"Description","OBS_DESC":"Description",
                  "OBS_ID":"Description","OBS_MODE":"Description",
                  "TELCONFG":"Description","TEXPOSUR":"Description",
                  "TDESCn":"Description","UCD":"Description",
                  "EXPTIME":"Description","XPOSURE":"Description",

                  "AUTHOR":"PersonID","ORIGIN":"PersonID",
                  "RELEASEC":"PersonID",

                  "FITS":"Format",

                  "BTYPE":"MeasurmentType"
                  }

# Define the namespace URI
NAMESPACE_URI = "http://www.spase-group.org/data/schema"
# Register the namespace with a desired prefix
ET.register_namespace("", NAMESPACE_URI)

# Parse ElementTree and extract root
parser = etree.XMLParser()
tree = ET.parse('spase_display_data_req.xml', parser)
root = tree.getroot()

# Iterate through root to see subfields
for elt in root.iter(tag=etree.Element):
    print(elt.tag)

class fits_header_to_json():
    def __init__(self,fits_url):
        self.fits_url = fits_url

    def extract_header(self):

        # List to store all header dictionaries
        all_hdu_headers = []

        # Open the FITS file directly from the URL and process each HDU's header
        with fits.open(self.fits_url) as hdul:
            for i, hdu in enumerate(hdul):
                current_header_dict = {}
                for key, value in hdu.header.items():
                    current_header_dict[key] = value
                all_hdu_headers.append(current_header_dict)
        print(f"Headers successfully extracted for {self.fits_url}")

        """For PUNCH output data files: 
            -hdul[0] contains information about the compression scheme.
            -hdul[1] contains primary data array & astropy header string
            describing that data
            -hdul[2]) contains uncertainty array - corresponding on a
            pixel-by-pixel basis with the primary data array."""

        return all_hdu_headers[1]

    def write_json(self, headers_list):

        # Convert the list of dictionaries to a JSON string
        json_output = json.dumps(headers_list, indent=2)

        # Define a local base directory for saving JSON files
        local_output_base_dir = "local_json_output" # This will create a directory in /content/

        # Ensure the local base output directory exists
        os.makedirs(local_output_base_dir, exist_ok=True)

        #Construct the filename using the previous flattening method
        base_url_prefix = "https://umbra.nascom.nasa.gov/"
        no_prefix_path = self.fits_url.replace(base_url_prefix, "")
        flattened_path = no_prefix_path.replace("/", "_")
        #flattened_path = fits_url_to_convert.replace("/", "_")

        # Replace .fits extension with .json
        json_filename = flattened_path.replace(".fits", ".json")

        # Construct the full local output path
        output_filename = os.path.join(local_output_base_dir, json_filename)

        # Write the JSON to a file
        with open(output_filename, 'w') as f:
            f.write(json_output)

        print(f"JSON output saved to: {output_filename}\n")

        return None

# Run test on single example file
test_file = 'https://umbra.nascom.nasa.gov/punch/3/CAM/2026/02/20/PUNCH_L3_CAM_20260220001600_v0j.fits'
test = fits_header_to_json(test_file)
test.write_json(headers_list=test.extract_header())