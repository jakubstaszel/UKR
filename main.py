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

from manage import bands2A, updateStructure, dataCheck2A, dataDownload2A, epsg3857, mergeWQindexes, masking
from droughtIndexes import vci, ndvi, evi, wdrvi

import settings as st

def main():
    st.init()
    
    # detecting if we are calculating hist data 
    # then working on every product folder in DATAdir
    if list(st.indexes.keys())[0].endswith("hist"):
        for file in os.listdir(st.DATAdir):
            if not file.endswith(".zip"):
                bands = bands2A(file)
                
                ndvi(file, bands['b04_10m'], bands['b08_10m'])
                evi(file, bands['b02_10m'], bands['b04_10m'], bands['b08_10m'])
                wdrvi(file, bands['b04_10m'], bands['b08_10m'])

                #updateStructure(file, bands['b03_10m'], lastRefresh)
                
    # working on products from Open Access Hub
    else:
        # Open Access Hub API call
        products = dataCheck2A()
        
        # downloading data
        lastRefresh = dt.datetime.now()
        if not products.empty:
            #for product in products.iterrows():
            dataDownload2A(products)
        fileRefresh = open('lastRefresh.txt','w')
        fileRefresh.write(str(lastRefresh))
        fileRefresh.close()
        
        # retrieving bands and calculating indexes
        if not products.empty:
            for product in products.iterrows():
                bands = bands2A(product[1]['filename'])
                #showBand(bands['b02_10m'],'viridis')        
        # drought indexes
                vci(product[1]['title'], bands['b04_10m'], bands['b08_10m'], st.SHAREdir + '\\' + st.oblast + 'NDVIhist_merged_masked.tif')
                ndvi(product[1]['title'], bands['b04_10m'], bands['b08_10m'])
                evi(product[1]['title'], bands['b02_10m'], bands['b04_10m'], bands['b08_10m'])
                wdrvi(product[1]['title'], bands['b04_10m'], bands['b08_10m'])

                updateStructure(product[1]['title'], bands['b03_10m'], lastRefresh)

    print('Reprojecting indexes in RESULTSdir to EPSG:3857 and saving to REPROJdir')
    print('    Also removing files in RESULTSdir')
    for file in os.listdir(st.RESULTSdir):
        if file.endswith('.tif'):
            epsg3857(file, st.RESULTSdir, True)


    # from this part, indexes variable is needed to specify which indexes should be continued

    # indexes = {'VCI':[], 'NDWI':[], 'NMDI':[]}
    # indexes = {'NDMI':[], 'NDVI':[]}

    for file in os.listdir(st.REPROJdir):
        if file.endswith('.tif'):
            param = file.split('_')[0]
            src = rasterio.open(st.REPROJdir + '\\' + file)
            st.indexes[param].append(src)
    mergeWQindexes(st.indexes, True)

    # this is required to close all open files before deleting files in REPROJdir
    src.close()
    for key in st.indexes:
        for product in st.indexes[key]:
            product.close()

    print('Removing files from REPROJdir')
    for filename in os.listdir(st.REPROJdir):
        if os.path.exists(st.REPROJdir + '\\' + filename):
            os.remove(st.REPROJdir + '\\' + filename)
            print('    Deleted: ' + filename)

    for file in os.listdir(st.SHAREdir):
        if file.endswith('_merged.tif'):
            maskingShp = st.HOMEdir + "\\oblastExtent\\" + st.oblast + ".shp"
            masking(file, st.SHAREdir, maskingShp)

if __name__ == "__main__":
    main()