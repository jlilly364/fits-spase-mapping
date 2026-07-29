from datetime import datetime, timedelta
#import html
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

                  "FITS":"Format"
                  }
