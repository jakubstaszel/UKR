import arcpy
from arcgis.gis import GIS
import os
import datetime as dt
import xml.dom.minidom as DOM

import settings as st

def uploadAGOL(indexName):
    arcGISproProj = st.HOMEdir + '\\share\\' + st.oblast + 'UkrSharing.aprx'

    arcpy.SignInToPortal("https://www.arcgis.com", st.ARClogin, st.ARCpassword)
    print('Start publishing : ' + indexName)
    os.chdir(st.SHAREdir)
# this layer (index) was uploaded before
    if os.path.isfile('.\\' + indexName + '.sd'):
        outdir = st.SHAREdir
        service_name = indexName + str(dt.datetime.today().strftime('%Y%m%d'))
        sddraft_filename = service_name + ".sddraft"
        sddraft_output_filename = os.path.join(outdir, sddraft_filename)
        sddraft_temp_output_filename = os.path.join(outdir, service_name + 'temp.sddraft')
        sd_filename = service_name + ".sd"
        sd_output_filename = os.path.join(outdir, sd_filename)

        # Reference map to publish
        aprx = arcpy.mp.ArcGISProject(arcGISproProj)
        m = aprx.listMaps(indexName)[0]

        # Create TileSharingDraft and set metadata and portal folder properties
        server_type = "HOSTING_SERVER"
        sddraft = m.getWebLayerSharingDraft(server_type, "TILE", service_name)
        sddraft.credits = ""
        sddraft.description = "Layer containg raster values for " + indexName + "."
        sddraft.summary = ""
        sddraft.tags = "Water Quality, Sentinel-2, Drought, " + indexName
        sddraft.useLimitations = ""
        sddraft.portalFolder = "UKR"
        sddraft.overwriteExistingService = True
        sddraft.exportToSDDraft(sddraft_temp_output_filename)
        
        # Modyf minScale and maxScale in sddraft file
        doc = DOM.parse(sddraft_temp_output_filename)
        prop = doc.getElementsByTagName('ConfigurationProperties')[0]
        configProps = doc.getElementsByTagName('ConfigurationProperties')[0]
        propArray = configProps.firstChild
        propSets = propArray.childNodes
        
        for propSet in propSets:
            keyValues = propSet.childNodes
            for keyValue in keyValues:
                if keyValue.tagName == 'Key':
                    if keyValue.firstChild.data == "minScale":
                        # set min scale
                        keyValue.nextSibling.firstChild.data = "10000000.000000"
            for keyValue in keyValues:
                if keyValue.tagName == 'Key':
                    if keyValue.firstChild.data == "maxScale":
                        # set max scale
                        keyValue.nextSibling.firstChild.data = "5000.000000"

        f = open(sddraft_output_filename, 'w')
        doc.writexml(f)
        f.close()
        
        # Stage
        print("    Start Staging")
        arcpy.StageService_server(sddraft_output_filename, sd_output_filename)

        # Upload
        print("    Start Uploading")
        arcpy.UploadServiceDefinition_server(sd_output_filename, server_type)
        
        # Creates and updates tiles in an existing web tile layer cache
        print("    Start Creating Tiles")
        input_service = r'https://tiles.arcgis.com/tiles/MzCtPDSne0rpIt7V/arcgis/rest/services/' + service_name + r'/MapServer'
        arcpy.ManageMapServerCacheTiles_server(input_service, [200000,50000,10000], "RECREATE_ALL_TILES")
        
        # Replace prod layer with temp
        print("    Start Replacing Layers")
        
        gis = GIS("https://www.arcgis.com", st.ARClogin, st.ARCpassword)
        for item in gis.content.search(query='title:' + indexName,item_type = 'Map Image Layer',max_items=-1):
            if item.title == indexName:
                main_service = item.id
        input_service = gis.content.search(query='title:' + service_name,item_type = 'Map Image Layer',max_items=1)[0].id
        
        archive_serviceName = indexName + r'archive' + str(dt.datetime.today().strftime('%Y%m%d'))

        arcpy.server.ReplaceWebLayer(main_service, archive_serviceName, input_service)
        
        os.remove(sddraft_output_filename)
        os.remove(sd_output_filename)
        os.remove(sddraft_temp_output_filename)
# this layer (index) is uploaded for the first time
    else:
        outdir = st.SHAREdir
        service_name = indexName
        sddraft_filename = service_name + ".sddraft"
        sddraft_output_filename = os.path.join(outdir, sddraft_filename)
        sddraft_temp_output_filename = os.path.join(outdir, service_name + 'temp.sddraft')
        sd_filename = service_name + ".sd"
        sd_output_filename = os.path.join(outdir, sd_filename)

        # Reference map to publish
        aprx = arcpy.mp.ArcGISProject(arcGISproProj)
        m = aprx.listMaps(indexName)[0]

        # Create TileSharingDraft and set metadata and portal folder properties
        server_type = "HOSTING_SERVER"
        sddraft = m.getWebLayerSharingDraft(server_type, "TILE", service_name)
        sddraft.credits = ""
        sddraft.description = "Layer containg raster values for " + indexName + "."
        sddraft.summary = ""
        sddraft.tags = "Water Quality, Sentinel-2, Drought, " + indexName
        sddraft.useLimitations = ""
        sddraft.portalFolder = "UKR"
        sddraft.overwriteExistingService = True
        sddraft.exportToSDDraft(sddraft_temp_output_filename)
        
        # Modyf minScale and maxScale in sddraft file
        doc = DOM.parse(sddraft_temp_output_filename)
        prop = doc.getElementsByTagName('ConfigurationProperties')[0]
        configProps = doc.getElementsByTagName('ConfigurationProperties')[0]
        propArray = configProps.firstChild
        propSets = propArray.childNodes
        
        for propSet in propSets:
            keyValues = propSet.childNodes
            for keyValue in keyValues:
                if keyValue.tagName == 'Key':
                    if keyValue.firstChild.data == "minScale":
                        # set min scale
                        keyValue.nextSibling.firstChild.data = "10000000.000000"
            for keyValue in keyValues:
                if keyValue.tagName == 'Key':
                    if keyValue.firstChild.data == "maxScale":
                        # set max scale
                        keyValue.nextSibling.firstChild.data = "5000.000000"

        f = open(sddraft_output_filename, 'w')
        doc.writexml(f)
        f.close()
        
        # Stage
        print("    Start Staging")
        arcpy.StageService_server(sddraft_output_filename, sd_output_filename)

        # Upload
        print("    Start Uploading")
        arcpy.UploadServiceDefinition_server(sd_output_filename, server_type)
        
        # Creates and updates tiles in an existing web tile layer cache
        print("    Start Creating Tiles")
        input_service = repr(r'https://tiles.arcgis.com/tiles/MzCtPDSne0rpIt7V/arcgis/rest/services/' + service_name + r'/MapServer')
        arcpy.ManageMapServerCacheTiles_server(input_service, [150000,50000,10000], "RECREATE_ALL_TILES")
        
    print('Finish publishing : ' + indexName)
    os.chdir(st.HOMEdir)