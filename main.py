import sys

from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
import datetime as dt
import zipfile
import os
from os.path import exists

#from osgeo import gdal
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.merge import merge
import rasterio.mask
from rasterio.features import bounds
from rasterio.enums import Resampling
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import fiona

import json

# dates to search for new Sentinel images 
# e.g. '20211025' 'rrrrMMdd'
startDate = '20210401' # included 
endDate = '20210430' # not included

# you need to specify if the data will be actual or historical 
# so the indexes do not merge together
oblast = 'kk'
indexes = {oblast + 'EVIhist':[],oblast + 'NDVIhist':[],oblast + 'VCIhist':[],oblast + 'WDRVIhist':[]}
# indexes = {oblast + 'EVI':[],oblast + 'NDVI':[],oblast + 'VCI':[],oblast + 'WDRVI':[]}

HOMEdir = os.getcwd()
DATAdir = HOMEdir + r'\data'
RESULTSdir = HOMEdir + r'\results'
SHAREdir = HOMEdir + r'\share'
REPROJdir = HOMEdir + r'\reproject'

cloudCover = (0,20)

def main():
    # detecting if we are calculating hist data 
    # then working on every product folder in DATAdir
    if list(indexes.keys())[0].endswith("hist"):
        for file in os.listdir(DATAdir):
            if not file.endswith(".zip"):
                bands = bands2A(file)
                
                vci(file, bands['b04_10m'], bands['b08_10m'], SHAREdir + '\\' + oblast + 'NDVIhist_merged_masked.tif')
                ndvi(file, bands['b04_10m'], bands['b08_10m'])
                evi(file, bands['b02_10m'], bands['b04_10m'], bands['b08_10m'])
                wdrvi(file, bands['b04_10m'], bands['b08_10m'])

                updateStructure(product[1]['title'], bands['b03_10m'], lastRefresh)
                
    # working on products from Open Access Hub
    else:
        # Open Access Hub API call
        products = dataCheck2A()
        
        # downloading data
        lastRefresh = dt.datetime.now()
        if not products.empty:
            for product in products.iterrows():
                dataDownload2A(product)
        fileRefresh = open('lastRefresh.txt','w')
        fileRefresh.write(str(lastRefresh))
        fileRefresh.close()
        
        # retrieving bands and calculating indexes
        if not products.empty:
            for product in products.iterrows():
                bands = bands2A(product[1]['filename'])
                #showBand(bands['b02_10m'],'viridis')        
        # drought indexes
                vci(product[1]['title'], bands['b04_10m'], bands['b08_10m'], SHAREdir + '\\' + oblast + 'NDVIhist_merged_masked.tif')
                ndvi(product[1]['title'], bands['b04_10m'], bands['b08_10m'])
                evi(product[1]['title'], bands['b02_10m'], bands['b04_10m'], bands['b08_10m'])
                wdrvi(product[1]['title'], bands['b04_10m'], bands['b08_10m'])

                updateStructure(product[1]['title'], bands['b03_10m'], lastRefresh)

    print('Reprojecting indexes in RESULTSdir to EPSG:3857 and saving to REPROJdir')
    print('    Also removing files in RESULTSdir')
    for file in os.listdir(RESULTSdir):
        if file.endswith('.tif'):
            epsg3857(file, RESULTSdir, True)


    # from this part, indexes variable is needed to specify which indexes should be continued

    # indexes = {'VCI':[], 'NDWI':[], 'NMDI':[]}
    # indexes = {'NDMI':[], 'NDVI':[]}

    for file in os.listdir(REPROJdir):
        if file.endswith('.tif'):
            param = file.split('_')[0]
            src = rasterio.open(REPROJdir + '\\' + file)
            indexes[param].append(src)
    mergeWQindexes(indexes, True)

    # this is required to close all open files before deleting files in REPROJdir
    src.close()
    for key in indexes:
        for product in indexes[key]:
            product.close()

    print('Removing files from REPROJdir')
    for filename in os.listdir(REPROJdir):
        if os.path.exists(REPROJdir + '\\' + filename):
            os.remove(REPROJdir + '\\' + filename)
            print('    Deleted: ' + filename)

    for file in os.listdir(SHAREdir):
        if file.endswith('_merged.tif'):
            maskingShp = HOMEdir + "\\oblastExtent\\" + oblast + ".shp"
            masking(file, SHAREdir, maskingShp)

if __name__ == "__main__":
    main()