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
# Dict of FITS metadata labels that map with ResourceHeader fields        
resourceHeaderMap = {"OBSTITLE":"ResourceName","TITLE":"ResourceName",

                    "RELEASE":"ReleaseDate",

                    "PROJECT":"Project",

                    "CAMERA":"Description","CAR_ROT":"Description",
                    "CRS_DESC":"Description","CRS:TYPE":"Description",
                    "CDELT1":"Description","CDELT2":"Description",
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

                    "COMMENT":"URL","DOC_URL":"URL","DOI":"URL","INFO_URL":"URL",
                    "KEYWDDOC":"URL","REFERENCEC":"URL","SCI_SW":"URL"}

# Dict of FITS metadata labels that map with other NumericalData fields        
accessInfoMap = {"LICENSE":"RightsName"}
providerNameMap = {"HOSTNAME":"ProviderName","ORIGIN":"ProviderName"}
providerProcessingMap = {"LEVEL":"ProviderProcessingLevel","LVL_NUM":"ProviderProcessingLevel"}
instrumentIdMap = {"DETECTOR":"InstrumentID","INSTRUME":"InstrumentID","TELESCOP":"InstrumentID"}
measurementTypeMap = {"BTYPE":"MeasurmentType"}
temporalDescriptionMap = {"CADENCE":"Cadence","CADMIN":"CadenceMin","CADMAX":"CadenceMax",
                      "DATE-BEG":"StartDate","DATE-END":"StopDate"} \
                      # "DATE-OBS":"StartDate","DATE-OBS":"StopDate"
spectralRangeMap = {"CRS_TYPE":"SpectralRange","UCD":"SpectralRange"}
obsRegionMap = {"TARGET":"ObservedRegion"}
spatialCoverageMap = {"WCS_NAME":"CoordinateSystemName","WCS_NAME":"CoordinateSystemRepresentation"}
keywordMap = {"DATATAGS":"Keyword","KEYVOCAB":"Keyword","KEYWORDS":"Keyword","TARGET":"Keyword"}

paramMap = {"FILTER":"Name","OBS-MODE":"Name","SCI_SW":"Name","XPOSURE":"Name",
            
            "BNAME":"Description","CDELT1":"Description","CDELT2":"Description",
            "CUNIT1":"Description","CUNIT2":"Description",
            "NAXIS":"Description","NAXIS1":"Description","NAXIS2":"Description",

            "BUNIT":"Units",

            "BNDCTR":"SpectralRange",

            "DATAMIN":"ValidMin", "DATAMAX":"ValidMax",

            "WAVEBAND":"SpectralRange","WAVELNTH":"SpectralRange","WAVEUNIT":"SpectralRange",
            "WAVEMIN":"Low","WAVEMAX":"High"}#,"WAVEUNIT":"Units"}

spaseFields = ["ResourceHeader","AccessInformation","ProviderName",
               "ProviderProcessing","InstrumentID","MeasurementType",
               "TemporalDescriptionMap","SpectralRange","ObservedRegion",
               "SpatialCoverage","Keyword","Parameter"]
spaseMaps = [resourceHeaderMap,accessInfoMap,providerNameMap,
             providerProcessingMap,instrumentIdMap,measurementTypeMap,
             temporalDescriptionMap,spectralRangeMap,obsRegionMap,
             spatialCoverageMap,keywordMap,paramMap]

# Iterate through root to see subfields
# for elt in root.iter(tag=etree.Element):
#     print(elt.tag)

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

class fitsSpaseMapping:

    def __init__(self,json_file):

        # Open the file and parse its contents
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        self.data = data

        # Define the namespace URI
        self.NAMESPACE_URI = "http://www.spase-group.org/data/schema"
        # Register the namespace with a desired prefix
        ET.register_namespace("", self.NAMESPACE_URI)

        # Establish namespace format
        self.namespaces = {"spase": f"{self.NAMESPACE_URI}"}

        # Parse empty SPASE NumericalData record and extract root
        parser = etree.XMLParser()
        self.tree = ET.parse('fits_spase_numerical_data.xml', parser)
        #print(tree)
        self.root = self.tree.getroot()

        # Initialize string for Pixel Resolution component of description
        self.pixResolution = ""

    def fitsResourceMap(self,resMap):
        # Initialize storage of ResourceHeader components
        resourceDescriptionParts = []
        personIDs = []
        roles = []
        resourceDescriptionEnd = None
        fitsURLs = ["COMMENT","DOC_URL","DOI","INFO_URL","KEYWDDOC","REFERENCEC","SCI_SW"]
        infoURLs = []

        # Initialize counters
        i,j = 0,0

        # Initialize dictionary for all other mapped fields
        mappedFields = {}

        for key, tag in resMap.items():
            if key in self.data:
                j+=1
                # Extract value of FITS metadata field
                value = self.data[key]
                print(f"{key} found! ")
    
                # Look for all ResourceHeader Description components and add if found
                if tag == "Description":
                    if key == "DESCRPTN":
                        resourceDescriptionParts.insert(0,f"{value}\n")
                    elif key == "CAMERA":
                        resourceDescriptionParts.append(f"CAMERA: {value}\n")
                    elif key == "CAR_ROT":
                        if isinstance(value,list):
                            # Possibly has multiple values in list?
                            resourceDescriptionParts.append(f"Carrington rotations {min(value)} to {max(value)}\n")
                        else:
                            resourceDescriptionParts.append(f"Carrington rotations {value}\n")
                    elif key == "CRS_DESC":
                        print("Concatenate unique values into a list")
                    elif key == "CRS_TYPE":
                        resourceDescriptionParts.append(f"SpectralRange: {value}\n")
                    elif key == "CTYPE1":
                        resourceDescriptionParts.append(f"Coordinate System: {value} ({self.data["CUNIT1"]}) x {self.data["CTYPE2"]} ({self.data["CUNIT2"]})\n")
                    elif key == "FILTER":
                        resourceDescriptionParts.append(f"Filter: {value}\n")
                    elif key == "GRATING":
                        resourceDescriptionParts.append(f"Grating: {value}\n")
                    elif key == "OBJECT":
                        resourceDescriptionParts.append(f"{value}\n")
                    elif key == "OBS_DESC":
                        resourceDescriptionParts.append(f"Observation: {value}\n")
                    elif key == "OBS_ID":
                        resourceDescriptionParts.append(f"Observation IDs: {value}\n")
                    elif key == "OBS-MODE":
                        resourceDescriptionParts.append(f"Observation modes: {value}\n")
                    elif key == "TDESCn":
                        print("Look for `CONTINUE` fields following these and append them.")
                    elif key == "TELCONFG":
                        resourceDescriptionParts.append(f"Configuration: {value}\n")
                    elif key == "TEXPOSUR":
                        resourceDescriptionParts.append(f"Single exposure time: {value}\n")
                    elif key == "UCD":
                        print("UCD = Unified Content DescriptorDescribes the physical" \
                        " quantity in a standard way (e.g., identifier for the concept)" \
                        "could be mapped into keyword if it had URL/identifier support")
                    elif key == "EXPTIME":
                        resourceDescriptionParts.append(f"Exposures: {np.median(value)}\n")
                    elif key == "XPOSURE":
                        resourceDescriptionParts.append(f"Exposures: {value}\n")       
                    elif key == "HISTORY":
                        resourceDescriptionEnd = value

                    # "Pixel Resolution: "{CDELT1} {CUNIT1} "x"+{CDELT2}+{CUNIT2}+"x"+
                    # ...+{CDELTn}+{CUNITn}"\n" for the number of axes given in {NAXIS}
                    elif key == "CDELT1":
                        pixResolution = f"Pixel Resolution: {value} {self.data["CUNIT1"]}"
                        for k in range(1,self.data["NAXIS"]):
                            pixResolution += f" x {self.data[f"CDELT{k}"]} {self.data[f"CUNIT{k}"]}"
                        resourceDescriptionParts.append(f"{pixResolution}\n")
    
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

                    """# Assign values of fields not mapped to previous fields
                    else:
                        mappedFields[tag] = value
                        print(f"Key:{key} | Tag:{tag} | Value = {value}\n")"""

                # InformationURLs
                elif key in fitsURLs:
                    if key != "COMMENT":
                        infoURLs.append([key,value])
                    else:
                        if "//" in key or len(value)==19:
                            infoURLs.append([key,value])

        # Assess how many fields are present or not
        # print(f"Total # of fields: {j+k}")
        # print(f"Total found: {j}")
        # print(f"Total not found: {k}")

        # Conjoin parts of description
        resourceDescription = ". ".join(resourceDescriptionParts) + f". {resourceDescriptionEnd}."

        # Find ResourceHeader fields in ElementTree root
        resourceHeader = self.root.find('.//spase:ResourceHeader', namespaces=self.namespaces)

        # Find ResourceHeader description elements or create one if not found 
        resourceDescriptionElem = resourceHeader.find('spase:Description', namespaces=self.namespaces)
        if resourceDescriptionElem is None:
            resourceDescriptionElem = etree.SubElement(resourceHeader, f"{{{self.NAMESPACE_URI}}}Description")
        resourceDescriptionElem.text = resourceDescription

        # Create Contact and PersonID elements for all fields that provide one
        for i, personID in enumerate(personIDs):
            contactElem = resourceHeader.find('spase:Contact', namespaces=self.namespaces)
            pidElem = contactElem.find('spase:PersonID', namespaces=self.namespaces)
            roleElem = contactElem.find('spase:Role', namespaces=self.namespaces)

            if contactElem is None:
                contactElem = etree.SubElement(resourceHeader, f"{{{self.NAMESPACE_URI}}}Contact")
                pidElem = etree.SubElement(contactElem, f"{{{self.NAMESPACE_URI}}}PersonID")
                roleElem = etree.SubElement(contactElem, namespaces=self.namespaces)
            pidElem.text = personID
            roleElem.text = roles[i]

        # Map project name
        fundingElem = resourceHeader.find('spase:Funding', namespaces=self.namespaces)
        projectElem = fundingElem.find('spase:Project', namespaces=self.namespaces)
        projectElem.text = self.data["PROJECT"]

        # Map Information URLs
        # Possible FITS keywords: 
        # "COMMENT","DOC_URL","DOI","INFO_URL","KEYWDDOC","REFERENCEC","SCI_SW"
        infoURLElem = resourceHeader.find('spase:InformationURL', namespaces=self.namespaces)
        nameElem = infoURLElem.find('spase:Name', namespaces=self.namespaces)
        urlElem = infoURLElem.find('spase:URL', namespaces=self.namespaces)
        descriptionElem = infoURLElem.find('spase:Description', namespaces=self.namespaces)

        # Include first InformationURL from FITS file into pre-existing element
        nameElem.text = infoURLs[i][0]
        urlElem.text = infoURLs[i][1]
        descriptionElem.text = infoURLs[i][0]

        # Create new InformationURL elements for additional links found
        for i in range(1,len(infoURLs)):
            infoURLElem = etree.SubElement(resourceHeader, f"{{{self.NAMESPACE_URI}}}InformationURL")
            nameElem = etree.SubElement(infoURLElem, f"{{{self.NAMESPACE_URI}}}Name")
            urlElem = etree.SubElement(infoURLElem, f"{{{self.NAMESPACE_URI}}}URL")
            descriptionElem = etree.SubElement(infoURLElem, f"{{{self.NAMESPACE_URI}}}Description")

            # Use collected keys and values to fill InformationURL fields
            nameElem.text = infoURLs[i][0]
            urlElem.text = infoURLs[i][1]
            descriptionElem.text = infoURLs[i][0]        

        # Find other mapped fields, or create if needed, and insert value
        for tag, value in mappedFields.items():
            print(f"Now inserting {tag}: {value}")
            resourceElem = resourceHeader.find(f'spase:{tag}', namespaces=self.namespaces)
            if resourceElem is None:
                resourceElem = etree.SubElement(resourceHeader, f"{{{self.NAMESPACE_URI}}}{tag}")
            resourceElem.text = value

        ET.indent(self.root, space="    ")

        output_xml = 'mapped_fits_spase_numerical_data_v2.xml'
        self.tree.write(output_xml, encoding='utf-8', xml_declaration=True,
        default_namespace=self.NAMESPACE_URI,short_empty_elements=False)
        print(f"Success! FITS > JSON > XML mapped and saved to {output_xml}")

    def fitsParamMap(self,parMap):
        # Initialize storage of Parameter description components
        paramDescriptionParts = []
        names = []

        for key, tag in parMap.items():
            if key in self.data:
                # Extract value of FITS metadata field
                value = self.data[key]
                print(f"{key} found! ")
        
        # Constructing components of Parameter description field
        # elif key == "BNAME":
        #     paramDescriptionParts.append(value)

        # Include "Pixel Resolution" info in Parameter description
        paramDescriptionParts.append(f"{self.pixResolution}\n")

        # Include size of array in Parameter description
        if key == "NAXIS":
            paramDescriptionParts.append(f"Array size: {self.data["NAXIS1"]}")
            for k in range(1,value):
                paramDescriptionParts.append(f"x {self.data[f"NAXIS{j}"]}")
            paramDescriptionParts.append("\n")

        if "EXTNAME" in self.data:
            names.append(self.data["EXTNAME"])
        # else:
        #     for key, tag in resourceHeaderMap.items():
        #         print(key,tag)
        #         names.append(self.data[key])

        # Conjoin parts of description
        parameterDescription = ". ".join(paramDescriptionParts)
        print(parameterDescription)

        # Find Parameter element
        parameter = self.root.find('.//spase:Parameter', namespaces=self.namespace)

        # Find Parameter elements, create them if not found, and map value to field
        paramNameElem = parameter.find('spase:Name', namespaces=self.namespace)
        paramDescriptionElem = parameter.find('spase:Description', namespaces=self.namespace)
        paramUnitElem = parameter.find('spase:Units', namespaces=self.namespace)

        # Should already be in SPASE record because it's required
        if paramNameElem is None:
            paramNameElem = etree.SubElement(parameter, f"{{{self.NAMESPACE_URI}}}Name")
        paramNameElem.text = ". ".join(names)

        if paramDescriptionElem is None:
            paramDescriptionElem = etree.SubElement(parameter, f"{{{self.NAMESPACE_URI}}}Description")
        paramDescriptionElem.text = ". ".join(paramDescriptionParts)

        if (paramUnitElem is None) and ("BUNIT" in self.data):
            paramUnitElem = etree.SubElement(parameter, f"{{{self.NAMESPACE_URI}}}Units")
        paramUnitElem.text = self.data["BUNIT"]

json_file = "local_json_output/punch_3_CAM_2026_02_20_PUNCH_L3_CAM_20260220001600_v0j.json"
test = fitsSpaseMapping(json_file)
test.fitsResourceMap(resourceHeaderMap)

"""# Save modified XML tree to file
output_xml = 'mapped_fits_spase_numerical_data_v2.xml'
tree.write(output_xml, encoding='utf-8', xml_declaration=True,
           default_namespace=NAMESPACE_URI,short_empty_elements=False)
print(f"Success! FITS > JSON > XML mapped and saved to {output_xml}")"""