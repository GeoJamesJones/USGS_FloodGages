# Import necessary modules

import arcgis
import csv
import os
import requests
import sys
import time
import traceback
import json

from arcgis import geometry
from arcgis.gis import GIS
from copy import deepcopy

# Makes a connection to the potals used by the ArcGIS API for Python
gis = GIS("https://esrifederal.maps.arcgis.com", 'james_jones_federal', 'QWerty654321@!')

# Output Error Log Directory
logPath = r'C:\Users\dif_user\Documents\StreamGage_ErrorLogs'

# References a layer that is used to either update the Current Layer or the Historic Layer
layer = gis.content.get('f7b4ab698fad43e7a28cbfd445d17dfd')
current_lyr = layer.layers[0]

historic_lyr = layer.layers[1]

# Web end-point that will be monitored
url ='https://waterwatch.usgs.gov/webservices/realtime?region=pr&format=json'

# Helper Functions
def exitScript():
    outFile = 'SteamGageMonitor_' + str(time.time()) + '.txt'
    fileFixed = outFile.replace(':', '-')
    outFilePath = os.path.join(logPath, fileFixed)
    with open(outFilePath, 'w') as F:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg  = "PYTHON ERRORS:\n Traceback info:\n" + tbinfo + "Error info:\n" + str(sys.exc_info()[1])
        msg = "\nArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        print(pymsg)
        print(msg)
        F.write(pymsg)
        F.write(msg)
	F.close()


# Main Script
try:

    print("Making request...")
    while True:
        response = requests.get(url)
        data = response.json()
        out_start = time.time()
        for i in data['sites']:
            start = time.time()
            current_fset = current_lyr.query(where='site_no=' +str(i['site_no']), return_geometry=False)
            all_features = current_fset.features
            original_features = all_features[0]
            feature_to_be_updated = deepcopy(original_features)
            features_for_update = []

            feature_to_be_updated.attributes['huc_cd'] = i['huc_cd']
            feature_to_be_updated.attributes['flow'] = i['flow']
            feature_to_be_updated.attributes['flow_dt'] = i['flow_dt']
            feature_to_be_updated.attributes['stage'] = i['stage']
            feature_to_be_updated.attributes['stage_dt'] = i['stage_dt']
            feature_to_be_updated.attributes['class'] = i['class']
            feature_to_be_updated.attributes['percentile'] = i['percentile']
            feature_to_be_updated.attributes['percent_median'] = i['percent_median']
            feature_to_be_updated.attributes['percent_mean'] = i['percent_mean']

            features_for_update.append(feature_to_be_updated)
            current_lyr.edit_features(updates=features_for_update)

            historic_fset = historic_lyr.query(where='OBJECTID= 1', return_geometry=True)
            historic_all_features = historic_fset.features
            historic_original_features = historic_all_features[0]
            template_feature = deepcopy(historic_original_features)

            historic_features_for_update = []
            new_feature = deepcopy(template_feature)

            input_geometry = {'y':i['dec_lat_va'],
                              'x':i['dec_long_va']}
            output_geometry = geometry.project(geometries = [input_geometry],
                                               in_sr=historic_fset.spatial_reference['latestWkid'],
                                               out_sr=historic_fset.spatial_reference['latestWkid'],
                                               gis=gis)

            new_feature.geometry = output_geometry[0]

            new_feature.attributes['huc_cd'] = i['huc_cd']
            new_feature.attributes['flow'] = i['flow']
            new_feature.attributes['flow_dt'] = i['flow_dt']
            new_feature.attributes['stage'] = i['stage']
            new_feature.attributes['stage_dt'] = i['stage_dt']
            new_feature.attributes['class'] = i['class']
            new_feature.attributes['percentile'] = i['percentile']
            new_feature.attributes['percent_median'] = i['percent_median']
            new_feature.attributes['percent_mean'] = i['percent_mean']
            new_feature.attributes['site_no'] = i['site_no']
            new_feature.attributes['station_nm'] = i['station_nm']
            new_feature.attributes['dec_lat_va'] = i['dec_lat_va']
            new_feature.attributes['dec_long_va'] = i['dec_long_va']
            new_feature.attributes['tz_cd'] = i['tz_cd']
            new_feature.attributes['flow_unit'] = i['flow_unit']
            new_feature.attributes['stage_unit'] = i['stage_unit']
            new_feature.attributes['url'] = i['url']

            historic_features_for_update.append(new_feature)
            historic_lyr.edit_features(adds = historic_features_for_update)

            done = time.time()
            out_done = time.time()

        elapsed = done - start
        out_elapsed = out_done - out_start
        print('Total time for updates: ' + str(out_elapsed) + ', sleeping for 1 hour...')

        time.sleep(900)
except:
    print("Error at " + str(time.time()))
    exitScript()
finally:
    print("Script Exited at " + str(time.time()))