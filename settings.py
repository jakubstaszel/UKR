import os

def init():
    global OAHlogin, OAHpassword, ARClogin, ARCpassword, startDate, endDate, oblast, indexes, HOMEdir, DATAdir, RESULTSdir, SHAREdir, REPROJdir, cloudCover
    
    # credentials - Open Access Hub
    OAHlogin = 'zuluzi'
    OAHpassword = 'kom987ik'
    # credentials ArcGIS Pro
    ARClogin = "zuluzi"
    ARCpassword = "Jem987dzem!"

    # dates to search for new Sentinel images 
    # e.g. '20211025' 'rrrrMMdd'
    startDate = '20220401' # included 
    endDate = '20220405' # not included

    # you need to specify if the data will be actual or historical 
    # so the indexes do not merge together
    oblast = 'kk'
    indexes = {oblast + 'EVIhist':[],oblast + 'NDVIhist':[],oblast + 'WDRVIhist':[]}
    # indexes = {oblast + 'EVI':[],oblast + 'NDVI':[],oblast + 'VCI':[],oblast + 'WDRVI':[]}

    HOMEdir = os.getcwd()
    DATAdir = HOMEdir + r'\data'
    RESULTSdir = HOMEdir + r'\results'
    SHAREdir = HOMEdir + r'\share'
    REPROJdir = HOMEdir + r'\reproject'

    cloudCover = (0,30)
