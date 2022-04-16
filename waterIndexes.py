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

import settings

def cdom(product, B03, B04):
    """
    Calculates CDOM index.
    Requires the title of the product, b03 and b04 bands.
    Saves the CDOM index in results directiory.
    """
    print('    Calculating CDOM for', product)
# opening one of bands in separated to retrieve metadata to later save the raster
    srcB03 = rasterio.open(B03)
    B03 = srcB03.read().astype('f4')
    B04 = rasterio.open(B04).read().astype('f4')

    B03[B03 <= 0] = np.nan
    B04[B04 <= 0] = np.nan

    cdom = 537 * np.exp(-2.93*B03/B04)

    cdom[cdom <= 0] = np.nan

    dst_crs = 'EPSG:3857'
    transform, wid, hei = calculate_default_transform(srcB03.crs, dst_crs, srcB03.width, srcB03.height, *srcB03.bounds)
    kwargs = srcB03.meta.copy()
    kwargs.update(
        driver='GTiff',
        dtype=rasterio.float32,
        count=1,
        compress='lzw')

    os.chdir(RESULTSdir)
    with rasterio.open('CDOM_' + product + '.tif', 'w', **kwargs) as dst:
        dst.write(cdom.astype(rasterio.float32))

    os.chdir(HOMEdir)
def turbidity(product, B03, B01):
    """
    Calculates turbidity.
    Requires the title of the product, b03 and b04 bands.
    Saves the turbidity raster in results directiory.
    """
    print('    Calculating turbidity for', product)
# opening one of bands in separated to retrieve metadata to later save the raster
    srcB03 = rasterio.open(B03)
    B03 = srcB03.read().astype('f4')
    B01 = rasterio.open(B01).read().astype('f4')

    B03[B03 <= 0] = np.nan
    B01[B01 <= 0] = np.nan

    turb = 8.93 * (B03/B01) - 6.39

    #turb[turb <= 0] = np.nan

    kwargs = srcB03.meta.copy()
    kwargs.update(
        driver='GTiff',
        dtype=rasterio.float32,
        count=1,
        compress='lzw')

    os.chdir(RESULTSdir)
    with rasterio.open('turbidity_' + product + '.tif', 'w', **kwargs) as dst:
        dst.write(turb.astype(rasterio.float32))
    os.chdir(HOMEdir)
def doc(product, B03, B04):
    """
    Dissolved Organic Carbon

    """
    print('    Calculating DOC for', product)
# opening one of bands in separated to retrieve metadata to later save the raster
    srcB03 = rasterio.open(B03)
    B03 = srcB03.read().astype('f4')
    B04 = rasterio.open(B04).read().astype('f4')

    B03[B03 <= 0] = np.nan
    B04[B04 <= 0] = np.nan

    doc = 432 * np.exp(-2.24*B03/B04)

    doc[doc <= 0] = np.nan

    kwargs = srcB03.meta.copy()
    kwargs.update(
        driver='GTiff',
        dtype=rasterio.float32,
        count=1,
        compress='lzw')

    os.chdir(RESULTSdir)
    with rasterio.open('DOC_' + product + '.tif', 'w', **kwargs) as dst:
        dst.write(doc.astype(rasterio.float32))
    os.chdir(HOMEdir)
def chl_a(product, B03, B01):
    """
    Concentration of Chlorophyll a
    """
    print('    Calculating Chl a for', product)
# opening one of bands in separated to retrieve metadata to later save the raster
    srcB03 = rasterio.open(B03)
    B03 = srcB03.read().astype('f4')
    B01 = rasterio.open(B01).read().astype('f4')

    B03[B03 <= 0] = np.nan
    B01[B01 <= 0] = np.nan

    chla = 4.26 * np.float_power(B03/B01, 3.94)

    chla[chla <= 0] = np.nan

    kwargs = srcB03.meta.copy()
    kwargs.update(
        driver='GTiff',
        dtype=rasterio.float32,
        count=1,
        compress='lzw')

    os.chdir(RESULTSdir)
    with rasterio.open('chla_' + product + '.tif', 'w', **kwargs) as dst:
        dst.write(chla.astype(rasterio.float32))
    os.chdir(HOMEdir)
def cya(product, B03, B04, B02):
    """
    Density of Cyanobacteria
    """
    print('    Calculating Cya for', product)
# opening one of bands in separated to retrieve metadata to later save the raster
    srcB03 = rasterio.open(B03)
    B03 = srcB03.read().astype('f4')
    B04 = rasterio.open(B04).read().astype('f4')
    B02 = rasterio.open(B02).read().astype('f4')

    B03[B03 <= 0] = np.nan
    B04[B04 <= 0] = np.nan
    B02[B02 <= 0] = np.nan

    cyaTemp = 115530.31 * np.float_power(B03*B04/B02, 2.38)
    cya = np.divide(cyaTemp,10**12)
    
    cya[cya <= 0] = np.nan

    kwargs = srcB03.meta.copy()
    kwargs.update(
        driver='GTiff',
        dtype=rasterio.float32,
        count=1,
        compress='lzw')

    os.chdir(RESULTSdir)
    with rasterio.open('cya_' + product + '.tif', 'w', **kwargs) as dst:
        dst.write(cya.astype(rasterio.float32))
    os.chdir(HOMEdir)    