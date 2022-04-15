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

def vci(product, B04, B08, histNDVI):
    """
    Calculates VCI index.
    Requires the title of the product, b04 and b08 bands with resolution 10m.
    Saves the VCI index in results directiory.
    """
    print('    Calculating VCI for', product)
# opening one of bands in separated to retrieve metadata to later save the raster
    srcB04 = rasterio.open(B04)
    B04 = srcB04.read().astype('f4')
    B08 = rasterio.open(B08).read().astype('f4')

    B04[B04 <= 0] = np.nan
    B08[B08 <= 0] = np.nan
    
# ndvi matrix is required for calculating vci 
    try:
        ndvi = rasterio.open(histNDVI).read().astype('f4')
        ndviMax = np.nanmax(ndvi)
        ndviMin = np.nanmin(ndvi)
    except:
        print("VCI needs calculated historical NDVI")
    
    ndvi = np.divide((B08 - B04), (B08 + B04))
    vci = np.divide((ndvi - ndviMin), (ndviMax - ndviMin)) * 100

    vci[vci < 0] = np.nan
    vci[vci > 100] = np.nan

    dst_crs = 'EPSG:3857'
    transform, wid, hei = calculate_default_transform(srcB04.crs, dst_crs, srcB04.width, srcB04.height, *srcB04.bounds)
    kwargs = srcB04.meta.copy()
    kwargs.update(
        driver='GTiff',
        dtype=rasterio.float32,
        count=1,
        compress='lzw')

    os.chdir(RESULTSdir)
    with rasterio.open('VCI_' + product + '.tif', 'w', **kwargs) as dst:
        dst.write(vci.astype(rasterio.float32))

    os.chdir(HOMEdir)
    
### --------------------------------------------------------------------------------------------------------------------------------------------
def ndwi(product, B03, B08):
    """
    Calculates NDWI index.
    Requires the title of the product, b03 and b08 bands with resolution 10m.
    Saves the NDWI index in results directiory.
    """
    print('    Calculating NDWI for', product)
# opening one of bands in separated to retrieve metadata to later save the raster
    srcB03 = rasterio.open(B03)
    B03 = srcB03.read().astype('f4')
    B08 = rasterio.open(B08).read().astype('f4')

    B03[B03 <= 0] = np.nan
    B08[B08 <= 0] = np.nan
    
    ndwi = np.divide((B03 - B08),(B03 + B08))

    ndwi[ndwi < -1] = np.nan
    ndwi[ndwi > 1] = np.nan

    dst_crs = 'EPSG:3857'
    transform, wid, hei = calculate_default_transform(srcB03.crs, dst_crs, srcB03.width, srcB03.height, *srcB03.bounds)
    kwargs = srcB03.meta.copy()
    kwargs.update(
        driver='GTiff',
        dtype=rasterio.float32,
        count=1,
        compress='lzw')

    os.chdir(RESULTSdir)
    with rasterio.open('NDWI_' + product + '.tif', 'w', **kwargs) as dst:
        dst.write(ndwi.astype(rasterio.float32))

    os.chdir(HOMEdir)
### --------------------------------------------------------------------------------------------------------------------------------------------
def nmdi(product, B08, B11, B12):
    """
    Calculates NMDI index.
    Requires the title of the product, b08, b11 and b12 bands with resolution 20m.
    Saves the NMDI index in results directiory.
    """
    print('    Calculating NMDI for', product)
# opening one of bands in separated to retrieve metadata to later save the raster
    srcB11 = rasterio.open(B11) 
    B11 = srcB11.read().astype('f4')
    B12 = rasterio.open(B12).read().astype('f4')
    
# band 8 is not available in 20m, using 10m and resampling
    upscale_factor = 1/2
    with rasterio.open(B08) as B08init:
        # resample data to target shape
        B08 = B08init.read(
            out_shape=(
                B08init.count,
                int(B08init.height * upscale_factor),
                int(B08init.width * upscale_factor)
            ),
            resampling=Resampling.bilinear
        ).astype('f4')

    B08[B08 <= 0] = np.nan
    B11[B11 <= 0] = np.nan
    B12[B12 <= 0] = np.nan
    
    B11B12 = B11 - B12
    
    nmdi = np.divide(B08 - B11B12, B08 + B11B12)

#normalized, values from 0 to 1 are the only reasonable
    nmdi[nmdi < 0] = np.nan
    nmdi[nmdi > 1] = np.nan

    dst_crs = 'EPSG:3857'
    transform, wid, hei = calculate_default_transform(srcB11.crs, dst_crs, srcB11.width, srcB11.height, *srcB11.bounds)
    kwargs = srcB11.meta.copy()
    kwargs.update(
        driver='GTiff',
        dtype=rasterio.float32,
        count=1,
        compress='lzw')

    os.chdir(RESULTSdir)
    with rasterio.open('NMDI_' + product + '.tif', 'w', **kwargs) as dst:
        dst.write(nmdi.astype(rasterio.float32))

    os.chdir(HOMEdir)
### --------------------------------------------------------------------------------------------------------------------------------------------
def ndmi(product, B08, B11):
    """
    Calculates NDMI index.
    Requires the title of the product, b08 and b11 bands with resolution 20m.
    Saves the NDMI index in results directiory.
    """
    print('    Calculating NDMI for', product)
# opening one of bands in separated to retrieve metadata to later save the raster
    srcB11 = rasterio.open(B11) 
    B11 = srcB11.read().astype('f4')
    
# band 8 is not available in 20m, using 10m and resampling
    upscale_factor = 1/2
    with rasterio.open(B08) as B08init:
        # resample data to target shape
        B08 = B08init.read(
            out_shape=(
                B08init.count,
                int(B08init.height * upscale_factor),
                int(B08init.width * upscale_factor)
            ),
            resampling=Resampling.bilinear
        ).astype('f4')

    B08[B08 <= 0] = np.nan
    B11[B11 <= 0] = np.nan
    
    ndmi = np.divide((B08 - B11), (B08 + B11))

    ndmi[ndmi < 0] = np.nan
    ndmi[ndmi > 1] = np.nan

    dst_crs = 'EPSG:3857'
    transform, wid, hei = calculate_default_transform(srcB11.crs, dst_crs, srcB11.width, srcB11.height, *srcB11.bounds)
    kwargs = srcB11.meta.copy()
    kwargs.update(
        driver='GTiff',
        dtype=rasterio.float32,
        count=1,
        compress='lzw')

    os.chdir(RESULTSdir)
    with rasterio.open('NDMI_' + product + '.tif', 'w', **kwargs) as dst:
        dst.write(ndmi.astype(rasterio.float32))

    os.chdir(HOMEdir)
### --------------------------------------------------------------------------------------------------------------------------------------------
def ndvi(product, B04, B08):
    """
    Calculates NDVI index.
    Requires the title of the product, b04 and b08 bands with resolution 20m.
    Saves the NDMI index in results directiory.
    """
    print('    Calculating NDVI for', product)
# opening one of bands in separated to retrieve metadata to later save the raster
    srcB04 = rasterio.open(B04) 
    B04 = srcB04.read().astype('f4')
    B08 = rasterio.open(B08).read().astype('f4')

    B08[B08 <= 0] = np.nan
    B04[B04 <= 0] = np.nan
    
    ndvi = np.divide((B08 - B04), (B08 + B04))

    ndvi[ndvi < -1] = np.nan
    ndvi[ndvi > 1] = np.nan

    dst_crs = 'EPSG:3857'
    transform, wid, hei = calculate_default_transform(srcB04.crs, dst_crs, srcB04.width, srcB04.height, *srcB04.bounds)
    kwargs = srcB04.meta.copy()
    kwargs.update(
        driver='GTiff',
        dtype=rasterio.float32,
        count=1,
        compress='lzw')

    os.chdir(RESULTSdir)
    with rasterio.open('NDVI_' + product + '.tif', 'w', **kwargs) as dst:
        dst.write(ndvi.astype(rasterio.float32))

    os.chdir(HOMEdir)
### --------------------------------------------------------------------------------------------------------------------------------------------
def wdrvi(product, B04, B08):
    """
    Calculates WDRVI index.
    Requires the title of the product, b04 and b08 bands with resolution 20m.
    Saves the WDRVI index in results directiory.
    """
    print('    Calculating WDRVI for', product)
# opening one of bands in separated to retrieve metadata to later save the raster
    srcB04 = rasterio.open(B04) 
    B04 = srcB04.read().astype('f4')
    B08 = rasterio.open(B08).read().astype('f4')

    B08[B08 <= 0] = np.nan
    B04[B04 <= 0] = np.nan
    
    wdrvi = np.divide(((0.1*B08) - B04), ((0.1*B08) + B04))

    #wdrvi[ndvi < -1] = np.nan
    #wdrvi[ndvi > 1] = np.nan

    dst_crs = 'EPSG:3857'
    transform, wid, hei = calculate_default_transform(srcB04.crs, dst_crs, srcB04.width, srcB04.height, *srcB04.bounds)
    kwargs = srcB04.meta.copy()
    kwargs.update(
        driver='GTiff',
        dtype=rasterio.float32,
        count=1,
        compress='lzw')

    os.chdir(RESULTSdir)
    with rasterio.open('WDRVI_' + product + '.tif', 'w', **kwargs) as dst:
        dst.write(wdrvi.astype(rasterio.float32))

    os.chdir(HOMEdir)
### --------------------------------------------------------------------------------------------------------------------------------------------
def evi(product, B02, B04, B08):
    """
    Calculates EVI index.
    Requires the title of the product, b04 and b08 bands with resolution 10m.
    Saves the EVI index in results directiory.
    """
    print('    Calculating EVI for', product)
# opening one of bands in separated to retrieve metadata to later save the raster
    srcB04 = rasterio.open(B04)
    B04 = srcB04.read().astype('f4')
    B08 = rasterio.open(B08).read().astype('f4')
    B02 = rasterio.open(B02).read().astype('f4')

    B04[B04 <= 0] = np.nan
    B08[B08 <= 0] = np.nan
    B02[B02 <= 0] = np.nan
    
    evi = np.divide((B08 - B04), (B08 + 6*B04 - 7.5*B02 +1)) * 2.5

    # evi[evi < 0] = np.nan
    # evi[evi > 100] = np.nan

    dst_crs = 'EPSG:3857'
    transform, wid, hei = calculate_default_transform(srcB04.crs, dst_crs, srcB04.width, srcB04.height, *srcB04.bounds)
    kwargs = srcB04.meta.copy()
    kwargs.update(
        driver='GTiff',
        dtype=rasterio.float32,
        count=1,
        compress='lzw')

    os.chdir(RESULTSdir)
    with rasterio.open('EVI_' + product + '.tif', 'w', **kwargs) as dst:
        dst.write(evi.astype(rasterio.float32))

    os.chdir(HOMEdir)