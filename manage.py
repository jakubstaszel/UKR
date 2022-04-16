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

import settings as st

# code changed for dev environment in dataCheck2A
def dataCheck2A():
    """
    Calls Sentinel API to find new 2A products.
    Reguires lastRefresh.txt file in HOMEdir.
    Return dataframe with products found.
    """
    os.chdir(st.HOMEdir)

    api = SentinelAPI(st.OAHlogin,st.OAHpassword,'https://scihub.copernicus.eu/dhus')
    footprint = geojson_to_wkt(read_geojson(st.HOMEdir + '\\geojsonExtents\\' + st.oblast + '.geojson'))
    products = api.query(footprint,
# searching from last refresh date (saved in file) till now
                         #date=(dt.datetime.strptime(open('lastRefresh.txt','r').read(), '%Y-%m-%d %H:%M:%S.%f'), dt.datetime.now()),
                         date=(st.startDate, st.endDate),
                         platformname='Sentinel-2',
                         processinglevel = 'Level-2A',
                         cloudcoverpercentage=st.cloudCover)

    products_df = api.to_dataframe(products)

    if products_df.empty:
        print('No new products found')
# update the datetime of last refresh
        fileRefresh = open('lastRefresh.txt','w')
        fileRefresh.write(str(dt.datetime.now()))
        fileRefresh.close()
    else:
        print('Products found: ')
        for product in products_df.iterrows():
            print('Found: ', product[1]['filename'])

    return products_df

def dataDownload2A(products_df):
    """
    Downloads and unzips products found.
    Reguires data returned from dataCheck() function and lastRefresh.txt file in HOMEdir.
    Returns nothing.
    """

    os.chdir(st.DATAdir)
    api = SentinelAPI(st.OAHlogin,st.OAHpassword,'https://scihub.copernicus.eu/dhus')

    for product in products_df.iterrows():
    #product = products_df
        print('Now downloading: ', product[1]['filename']) # filename of the product
        api.download(product[1]['uuid']) # download the product using uuid
        odata = api.get_product_odata(product[1]['uuid'], full=True)
        with zipfile.ZipFile(odata['title']+'.zip',"r") as zip_ref:
            zip_ref.extractall()
            print("Zipped file extracted to", product[1]['filename'], "folder")

    os.chdir(st.HOMEdir)
def bands2A(product):
    """
    Gets directories to different bands of the 2A product.
    Returns dictionary with directories to the bands.
    """
# getting into exact imagery folder
    os.chdir(st.DATAdir + '/' + product)

# finding directories for needed bands (only used implemented)
    bands = {'b02_10m':None, 
             'b03_10m':None, 
             'b04_10m':None, 
             'b08_10m':None,
             'b11_20m':None,
             'b12_20m':None,
             'b01_60m':None, 
             'b03_60m':None}

    print('Getting bands directories for', product)
    for root,dirs,files in os.walk(os.getcwd()):
        for file in files:
# finding different bands and resolution
            if file.endswith("_B04_10m.jp2"):
                bands['b04_10m'] = os.path.join(root, file)
            if file.endswith("_B03_10m.jp2"):
                bands['b03_10m'] = os.path.join(root, file)
            if file.endswith("_B02_10m.jp2"):
                bands['b02_10m'] = os.path.join(root, file)
            if file.endswith("_B08_10m.jp2"):
                bands['b08_10m'] = os.path.join(root, file)
            if file.endswith("_B11_20m.jp2"):
                bands['b11_20m'] = os.path.join(root, file)
            if file.endswith("_B12_20m.jp2"):
                bands['b12_20m'] = os.path.join(root, file)
            if file.endswith("_B01_60m.jp2"):
                bands['b01_60m'] = os.path.join(root, file)
            if file.endswith("_B03_60m.jp2"):
                bands['b03_60m'] = os.path.join(root, file)
    os.chdir(st.HOMEdir)
    return bands
def showBand(bandDir, color_map='gray'):
    """
    Creates a chart with raster values.
    Requires directory for a saved raster file and optionally a color map.
    """
    fig = plt.figure(figsize=(8, 8))
    band = rasterio.open(bandDir).read(1).astype('f4')
    image_layer = plt.imshow(band)
    image_layer.set_cmap(color_map)
    plt.colorbar()
    plt.show()
def epsg3857(product, directory, delete = False):
    """
    Requires name of the .tif file and the directory.
    Saves reprojected to EPSG 3857 (Web Mercator) .tif file in REPROJdir.
    Can delete provided product in the specified directory after reprojection.
    """
    product = product.split('.tif')[0]
    # print('Reprojecting: ' + product)
    dst_crs = 'EPSG:3857'
    with rasterio.open(directory + '\\' + product + '.tif') as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        with rasterio.open(st.REPROJdir + '\\' + product + '_reprojected.tif' , 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest)
    if delete == True:
        if os.path.exists(directory + '\\' + product + '.tif'):
            os.remove(directory + '\\' + product + '.tif')
            # print('    Deleted: ' + product + '.tif')
def mergeWQindexes(toBeMerged, delete = False):
    """
    Requires a list of rasterio.open() objects.
    """
    for index in toBeMerged:
        src = toBeMerged[index][0]
        rasters = []
        print('Merging : ' + index)
        rasters.extend(toBeMerged[index])
        if exists(st.SHAREdir + '\\' + index + '_merged.tif'):
            previousMerge = rasterio.open(SHAREdir + '\\' + index + '_merged.tif')
            rasters.append(previousMerge)
        mosaic, out_trans = merge(rasters)
        
        kwargs = src.meta.copy()
        kwargs.update(
            driver='GTiff',
            height= mosaic.shape[1],
            width=mosaic.shape[2],
            transform=out_trans,
            dtype=rasterio.float32,
            count=1,
            compress='lzw')
        with rasterio.open(st.SHAREdir+'\\'+index+'_merged.tif', 'w', **kwargs) as dest:
            dest.write(mosaic)
    
    src.close()
    if 'previousMerge' in locals():
        previousMerge.close()
        
    for key in toBeMerged:
        for product in toBeMerged[key]:
            product.close()
    
def updateStructure(product, band, lastRefresh):
    """
    """
    os.chdir(st.HOMEdir)
    with open('structure.json', 'r') as json_file:
        structure = json.load(json_file)
    structure['lastRefresh'] = str(lastRefresh)
    newRast = rasterio.open(band)
    bboxFound = False
    i = 1
    for raster in structure['rasters']:
        if bboxFound == False:
            if raster['crs'] == str(newRast.crs) and raster['bbox'] == str(newRast.bounds):
                structure['rasters'][i-1]['product'] = product
                bboxFound = True
            i = i + 1
        else:
            break
    if bboxFound == False:
        structure['rasters'].append({'id':i, 'product': product, 'crs': str(newRast.crs), 'bbox': str(newRast.bounds)})
    
    with open('structure.json', 'w') as json_out:
        json.dump(structure, json_out)

    with open(st.HOMEdir + '\\structureArchive\\structure_' + str(dt.datetime.today().strftime('%Y%m%d')) + '.json', 'w') as json_out:
        json.dump(structure, json_out)
def masking(product, directory, maskingShp):
    """
    Mask product with a shapefile
    """
    print('Masking: ' + product)
    with fiona.open(maskingShp, "r") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]
    
    with rasterio.open(directory + '\\' + product) as src:
        out_image, out_transform = rasterio.mask.mask(src, shapes, crop=True, nodata=np.nan, all_touched=True)
        out_meta = src.meta
    
    out_meta.update({"driver": "GTiff",
                 "height": out_image.shape[1],
                 "width": out_image.shape[2],
                 "transform": out_transform})

    with rasterio.open(directory + '\\' + product.split('.tif')[0] + '_masked.tif', "w", **out_meta) as dest:
        dest.write(out_image)