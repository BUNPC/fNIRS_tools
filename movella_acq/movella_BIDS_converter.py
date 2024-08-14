#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Read in movella file 
- inputs:   
    - run names
    - subj number
    - run number 
    
- save output in BIDS format
- populate the json file 

@author: lauracarlton
"""


import pandas as pd 
import matplotlib.pyplot as plt
import os
import csv
import json 

movella_path = '/projectnb/nphfnirs/ns/lcarlton/DATA/movella_RAW/'
bids_path = '/projectnb/nphfnirs/ns/lcarlton/DATA/MAFC_raw/'

date = '20240729'

tasks = [['RS', 1],
         ['audio', 1],
         ['MA', 1],
         ['MAaudio', 1]]

subjID = 'sub-10'

tracked_point_mapping = {'1': 'torso',
                '2': 'right_head',
                '3': 'left_head',
                '4': 'right_leg',
                '5': 'left_leg'
                }

unit_mapping = {'ACCEL' : 'm/s^2',
         'GYRO': 'deg/s',
         'ORNT': 'deg',
         'MISC': 'n/a',
         'LATENCY': 's'}

type_mapping = {'Euler': 'ORNT',
                  'FreeAcc': 'ACCEL',
                  'Gyr': 'GYRO',
                   'PacketCounter': 'MISC',
                   'SampleTimeFine': 'LATENCY'}

listAll = os.listdir(movella_path + date)
listDIRS = [entry for entry in listAll if os.path.isdir(os.path.join(movella_path, date, entry))]
listDIRS.sort()

resave_dir = os.path.join(bids_path, subjID, 'motion')
if not os.path.exists(resave_dir):
    os.makedirs(resave_dir)
    
for dd, DIR in enumerate(listDIRS):

    dir_path = os.path.join(movella_path, date, DIR)
    
    listFiles = os.listdir(dir_path)
    
    task = tasks[dd]
    task_id = task[0]
    run_num = task[1]
    
    IMU_dict = {}
      
    for file in listFiles:

        if file[0] == '.':
            continue
        
        file_path = os.path.join(dir_path, file)
        device_dict = {}
        with open(file_path, newline='') as f:
            reader = csv.reader(f)
            for ii,row in enumerate(reader):
                if ii == 0:
                    continue                
                try:
                    if row[0] == '':
                        header = ii+1
                        break
                except:
                    if len(row) == 0:
                        header = ii
                        break
                
                if len(row) > 1:
                    device_dict[row[0][:-1]]  = row[1]
                else:
                    manufacturer = row[0]

        # READ IN IMU CSV FILE 
        file_name_parts = file.split(date)
        deviceID = file_name_parts[0][:-1]
        run_name = subjID + '_task-' + task_id + '_tracksys-IMU' + deviceID + '_run-0' + str(run_num)
        
        df = pd.read_csv(file_path, header=header)
        # convert SampleTimeFine from ms to s
        df['SampleTimeFine'] = df['SampleTimeFine']/1e6
    
        # BREAK DOWN CHANNEL INFO FOR _channels.tsv
        channels = df.columns
        num_channels = len(channels)
        tracked_point = tracked_point_mapping[deviceID]
        channels_renamed = channels.copy()
        
        for key, value in type_mapping.items():
            channels_renamed =  [s.replace(key, value) for s in channels_renamed]
        
        channel_parts = [chan.split('_') for chan in channels_renamed]
        component = [chan[1].lower() if len(chan)>1 else 'n/a' for chan in channel_parts]
        types = [chan[0] for chan in channel_parts]
        
        units = types
        for key, value in unit_mapping.items():
            units = [s.replace(key, value) for s in units]
            
        channels_dict = {'name': channels,
                     'component': component,
                     'type': types,
                     'tracked_point': [tracked_point] * num_channels,
                     'units': units}
        
        channels_dict = pd.DataFrame(channels_dict)
        
        # POPULATE JSON SIDECAR FILE 
        json_dict = {'TaskName': task_id,
                     'SamplingFrequncy': int(device_dict['OutputRate'].split('H')[0]),
                     'Manufacturer': manufacturer,
                     'SoftwareVersions': device_dict['AppVersion'],
                     'MotionChannelCount': types.count('ACCEL') + types.count('ORNT') + types.count('GYRO'),
                     'ACCELChannelCount': types.count('ACCEL'),
                     'GYROChannelCount': types.count('GYRO'),
                     'ORNTChannelCount': types.count('ORNT'),
                     'LATENCYChannelCount': types.count('LATENCY'),
                     'MISCChannelCount': types.count('MISC'),
                     'TrackingSystemName': 'IMU' + deviceID,
                     'TrackedPointsCount': 1
            
            }
        
        
        # # SAVE CHANNELS TSV
        channels_path = os.path.join(resave_dir, run_name + '_channels.tsv')
        channels_dict.to_csv(channels_path,sep='\t', index=None)
        

        # # SAVE IMU CSV UNDER NEW _motion.tsv
        resave_name = run_name + '_motion.tsv'
        print(file  + ' ->  ' + resave_name)
        save_path = os.path.join(resave_dir, resave_name)
        df.to_csv(save_path, sep='\t', index=None)
        
        
        # # SAVE JSON SIDE CAR FILE
        json_path = os.path.join(resave_dir, run_name + '_motion.json')
        with open(json_path, 'w') as f:
                json.dump(json_dict, f, indent=4)




