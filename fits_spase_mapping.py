from astropy.io import fits
from datetime import datetime, timedelta
#import html
import json
#import lxml
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

# Not mapped in FITS: ResourceID, AccessInformation>(RepositoryID,AccessURL)
# Dict of fields that map within NumericalData            
dataMap = {"OBSTITLE":"ResourceName","TITLE":"ResourceName",

           "RELEASE":"ReleaseDate",

           "CAMERA":"Description","CAR_ROT":"Description",
           "CRS_DESC":"Description","CRS:TYPE":"Description",
           "CTYPE1":"Description","CTYPE2":"Description",
           "CUNIT1":"Description","CUNIT2":"Description",
           "DESCRPTN":"Description","FILTER":"Description",
           "GRATING":"Description","HISTORY":"Description",
           "OBJECT":"Description","OBS_DESC":"Description",
           "OBS_ID":"Description","OBS-MODE":"Description",
           "TELCONFG":"Description","TEXPOSUR":"Description",
           "TDESCn":"Description","UCD":"Description",
           "EXPTIME":"Description","XPOSURE":"Description",

           "AUTHOR":"PersonID","ORIGIN":"PersonID","RELEASEC":"PersonID",

           "FITS":"Format",

           "BTYPE":"MeasurmentType",

           "BNDCTR":"SpectralRange",

           "EXTNAME":"Name","FILTER":"Name","OBS_MODE":"Name","XPOSURE":"Name",

           "BNAME":"Description",
           "CDELT1":"Description","CDELT2":"Description","CDELTn":"Description",
           "CUNIT1":"Description","CUNIT2":"Description","CUNITn":"Description",
           "NAXIS":"Description","NAXIS1":"Description","NAXIS2":"Description",
           "NAXISn"

           "BUNIT":"Units",

           "CADENCE":"Cadence","CADMIN":"CadenceMin","CADMAX":"CadenceMax",

           "COMMENT":"URL","DOC_URL":"URL","DOI":"URL","INFO_URL":"URL",
           "KEYWDDOC":"URL","REFERENCEC":"URL","SCI_SW":"URL"
}

# Define the namespace URI
NAMESPACE_URI = "http://www.spase-group.org/data/schema"
# Register the namespace with a desired prefix
ET.register_namespace("", NAMESPACE_URI)

# Parse ElementTree and extract root
parser = etree.XMLParser()
tree = ET.parse('spase_numerical_data_fits.xml', parser)
print(tree)
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

        """
        https://punchbowl.readthedocs.io/en/0.0.19/data/access.html
        For PUNCH output data files: 
            -hdul[0] contains information about the compression scheme.
            -hdul[1] contains primary data array & astropy header string
            describing that data
            -hdul[2]) contains uncertainty array - corresponding on a
            pixel-by-pixel basis with the primary data array.
        """

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

"""# Run test on single example file
test_file = 'https://umbra.nascom.nasa.gov/punch/3/CAM/2026/02/20/PUNCH_L3_CAM_20260220001600_v0j.fits'
test = fits_header_to_json(test_file)
test.write_json(headers_list=test.extract_header())"""

# Open the file and parse its contents
json_file = "local_json_output/punch_3_CAM_2026_02_20_PUNCH_L3_CAM_20260220001600_v0j.json"
with open(json_file, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Initialize counters
i,j = 0,0

# Initialize storage of ResourceHeader description components
resourceDescriptionParts = []
personIDs = []
roles = []
resourceDescriptionEnd = None

# Initialize storage of Parameter description components
paramDescriptionParts = []
names = []

# Initialize dictionary for all other mapped fields
mappedFields = {}

# Loop through FITS metadata keys and associated SPASE xml tags
for key, tag in dataMap.items():
    print(key,tag)
    if key in data:
        i+=1
        value = data[key]
        #value = str(data[key]).strip()
        print(f"{key} found! ({value})\n")

        # Look for all ResourceHeader Description components and add if found
        if tag == "Description":
            if key == "DESCRPTN":
                resourceDescriptionParts.insert(0,value)
            elif key == "CAMERA":
                resourceDescriptionParts.append(f"CAMERA: {value}")
            elif key == "CAR_ROT":
                if isinstance(value,list):
                    # Possibly has multiple values in list?
                    resourceDescriptionParts.append(f"Carrington rotations {min(value)} to {max(value)}")
                else:
                    resourceDescriptionParts.append(f"Carrington rotations {value}")
            elif key == "CRS_DESC":
                print("Concatenate unique values into a list")
            elif key == "CRS_TYPE":
                resourceDescriptionParts.append(f"SpectralRange: {value}")
            elif key == "CTYPE1":
                resourceDescriptionParts.append(f"Coordinate System: {value} ({data["CUNIT1"]}) x {data["CTYPE2"]} ({data["CUNIT2"]})")
            elif key == "FILTER":
                resourceDescriptionParts.append(f"Filter: {value}")
            elif key == "GRATING":
                resourceDescriptionParts.append(f"Grating: {value}")
            elif key == "OBJECT":
                resourceDescriptionParts.append(f"{value}")
            elif key == "OBS_DESC":
                resourceDescriptionParts.append(f"Observation: {value}")
            elif key == "OBS_ID":
                resourceDescriptionParts.append(f"Observation IDs: {value}")
            elif key == "OBS-MODE":
                resourceDescriptionParts.append(f"Observation modes: {value}")
            elif key == "TDESCn":
                print("Look for `CONTINUE` fields following these and append them.")
            elif key == "TELCONFG":
                resourceDescriptionParts.append(f"Configuration: {value}")
            elif key == "TEXPOSUR":
                resourceDescriptionParts.append(f"Single exposure time: {value}")
            elif key == "UCD":
                print("UCD = Unified Content DescriptorDescribes the physical" \
                " quantity in a standard way (e.g., identifier for the concept)" \
                "could be mapped into keyword if it had URL/identifier support")
            elif key == "EXPTIME":
                resourceDescriptionParts.append(f"Exposures: {np.median(value)}")
            elif key == "XPOSURE":
                resourceDescriptionParts.append(f"Exposures: {value}")       
            elif key == "HISTORY":
                resourceDescriptionEnd = value

            # Constructing components of Parameter description field
            elif key == "BNAME":
                paramDescriptionParts += value
            # "Pixel Resolution: "{CDELT1} {CUNIT1} "x"+{CDELT2}+{CUNIT2}+"x"+
            # ...+{CDELTn}+{CUNITn}"\n" for the number of axes given in {NAXIS}
            elif key == "CDELT1":
                paramDescriptionParts.append(f"Pixel Resolution: {value} {data["CUNIT1"]}")
                for j in range(1,data["NAXIS"]):
                    paramDescriptionParts.append(f"x {data[f"CDELT{j}"]} {data[f"CUNIT{j}"]}")
                paramDescriptionParts.append("\n")
            elif key == "NAXIS":
                paramDescriptionParts.append(f"Array size: {data["NAXIS1"]}")
                for j in range(1,value):
                    paramDescriptionParts.append(f"x {data[f"NAXIS{j}"]}")
                paramDescriptionParts.append("\n")
            else:
                print(f"{key} not recognized in FITS-SPASE mapping. Skipping")

        # Assign proper role depending on FITS fields
        elif tag == "PersonID":
            print(f"PersonID: {value}")
            if key == "AUTHOR":
                roles.append("Author")
            elif key == "ORIGIN":
                roles.append("HostContact")
            elif key == "RELEASEC":
                roles.append("DataProducer")
            personIDs.append(value)

        elif tag == "Name":
            if key == "EXTNAME" or key == "FILTER" or key == "OBS_MODE" or key == "XPOSURE":
                names.append(f" {value}")

        # Assign values of fields not mapped to Description
        else:
            mappedFields[tag] = value
    else:
        j+=1
        print(f"{key} NOT found\n")

# Assess how many fields are present or not
print(f"Total # of fields: {i+j}")
print(f"Total found: {i}")
print(f"Total not found: {j}")
#print(personIDs)

# Conjoin parts of description
resourceDescription = ". ".join(resourceDescriptionParts) + f". {resourceDescriptionEnd}."
parameterDescription = ". ".join(paramDescriptionParts)


# Define namespaces and find fields in ElementTree root
namespaces = {"spase": f"{NAMESPACE_URI}"}
resourceHeader = root.find('.//spase:ResourceHeader', namespaces=namespaces)
parameter = root.find('.//spase:Parameter', namespaces=namespaces)

# Find ResourceHeader description elements or create one if not found 
resourceDescriptionElem = resourceHeader.find('spase:Description', namespaces=namespaces)
if resourceDescriptionElem is None:
    resourceDescriptionElem = etree.SubElement(resourceHeader, f"{{{NAMESPACE_URI}}}Description")
resourceDescriptionElem.text = resourceDescription

# Find Parameter description elements or create one if not found 
paramDescriptionElem = parameter.find('spase:Description', namespaces=namespaces)
paramNameElem = parameter.find('spase:Name', namespaces=namespaces)
if paramDescriptionElem is None:
    paramDescriptionElem = etree.SubElement(parameter, f"{{{NAMESPACE_URI}}}Description")
    paramNameElem = etree.SubElement(paramDescriptionElem, f"{{{NAMESPACE_URI}}}Name")
paramDescriptionElem.text = ". ".join(paramDescriptionParts)
paramNameElem.text = ". ".join(names)

# Create Contact and PersonID elements for all fields that provide one
for i, personID in enumerate(personIDs):
    contactElem = resourceHeader.find('spase:Contact', namespaces=namespaces)
    pidElem = contactElem.find('spase:PersonID', namespaces=namespaces)
    roleElem = contactElem.find('spase:Role', namespaces=namespaces)

    if contactElem is None:
        contactElem = etree.SubElement(resourceHeader, f"{{{NAMESPACE_URI}}}Contact")
        pidElem = etree.SubElement(contactElem, f"{{{NAMESPACE_URI}}}PersonID")
        roleElem = etree.SubElement(contactElem, namespaces=namespaces)
    pidElem.text = personID
    roleElem.text = roles[i]

# Find other mapped fields, or create if needed, and insert value
for tag, value in mappedFields.items():
    print(f"Now inserting {tag}: {value}")
    elem = resourceHeader.find(f'spase:{tag}', namespaces=namespaces)
    if elem is None:
        elem = etree.SubElement(resourceHeader, f"{{{NAMESPACE_URI}}}{tag}")
    elem.text = value

# Save modified XML tree to file
output_xml = 'mapped_fits_spase_numerical_data_v2.xml'
tree.write(output_xml, encoding='utf-8', xml_declaration=True,
           default_namespace=NAMESPACE_URI,short_empty_elements=False)
print(f"Success! FITS > JSON > XML mapped and saved to {output_xml}")