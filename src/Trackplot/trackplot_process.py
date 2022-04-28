#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# The future package will provide support for running your code on Python 2.6, 2.7, and 3.3+ mostly unchanged.
# http://python-future.org/quickstart.html
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
from operator import truediv

##### TiDDE packages #####
from trackplot_gooey import trackplotArguments

##### General packages #####
import os, sys
import datetime
import logging
from argparse import Namespace
import external.shapefile as shapefile 
import external.pyall as pyall
from datetime import timedelta
import numpy as np 
import math
import external.geodetic as geodetic
import geopandas as gpd
from shapely.geometry import Point,LineString,MultiLineString,GeometryCollection
from shapely import wkt
import pandas as pd
pd.options.mode.chained_assignment = None
import subprocess
from colored import stylize, attr, fg
import fiona
fiona.supported_drivers 



##########################################################
#               trackplot Pre-Start Functions                 #
##########################################################
def trackplot_prestart(args: Namespace, mode:str) -> trackplotArguments:
    arguments = trackplotArguments.from_gooey_args(args, mode)
    #print(arguments)
    # Logging
    if not os.path.exists(os.path.join(arguments.trackplot_output_folder, '_DEBUG_LOG')):
        os.makedirs(os.path.join(arguments.trackplot_output_folder, '_DEBUG_LOG'))

    if not os.path.exists(os.path.join(arguments.trackplot_output_folder, 'SHP')):
        os.makedirs(os.path.join(arguments.trackplot_output_folder, 'SHP'))


    nowlog = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(arguments.trackplot_output_folder, '_DEBUG_LOG', '_Processing_Log_' + str(nowlog) + '.txt')
    logging.basicConfig(filename=log_path, level=logging.INFO, format='%(asctime)s.%(msecs)03d | %(levelname)s | %(module)s - %(funcName)s | -- %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logging.info(f"trackplot Version: v0.1.0 | Mode: {mode}")
    logging.info("####################### START #######################") 

    list_proc = os.path.join(arguments.trackplot_output_folder, '_DEBUG_LOG', 'Processing_List.txt')
    if not os.path.isfile(list_proc):
        with open(list_proc, "w"): pass

    skip_list = os.path.join(arguments.trackplot_output_folder, '_DEBUG_LOG', 'Skip_List.txt')
    if not os.path.isfile(skip_list):
        with open(skip_list, "w"): pass


		
    
    return arguments, list_proc, skip_list

##########################################################
#           Offline Data Processing Functions            #
##########################################################
def process(arguments: trackplotArguments, list_proc, skip_list) -> None:
	exclude=[]
	path_spl= listFile(arguments.spl_folder,arguments.nav_pattern, set(exclude))
	#print(path_spl)
	
	CRP_Lines=[]
	CRP_points=[]
	CRP_decimate=[]
	CRP_line = pd.DataFrame(columns=['Date','Time', 'Easting', 'Northing', 'Height', 'LineName'])
	tolerance=0.3
	interval=int(arguments.interval)
	print(interval)
	#print(u'\xb0')

	

	dfver = pd.read_csv(list_proc, header=None, names=['PathCheck'],encoding='ISO-8859-1')
	dfver.drop_duplicates(keep='last', inplace=True)
	dfver.to_csv(list_proc, header=False, index=False)
	s1 = set(dfver['PathCheck'].tolist())
	
	tmp_spl = set(path_spl)

	spl_path = sorted(list(tmp_spl.difference(s1)))


	#Checking if Processing is not empty
	if spl_path:

		outputFolder=arguments.trackplot_output_folder

		for index, spl in enumerate(spl_path):
			#Converting FBF or FBZ to CSV
			CRP_df,skip_file=CRP2csv(spl, outputFolder)
			if skip_file:
				#Updating Processing list with processed files 
				with open(skip_list, "a") as f:
					f.write(f"{skip_file}\n")

			if not CRP_df.empty:
				#Converting Datetime to string shapefile can not handle python datetime format 
				CRP_df['Date']=CRP_df['DateTime'].dt.strftime('%Y-%m-%d')
				CRP_df['Time']=CRP_df['DateTime'].dt.strftime('%H:%M:%S')
				CRP_df.drop('DateTime',axis=1,inplace=True)

				#Including Vessel Name on attribute table
				CRP_df['Vessel']=arguments.vessel_name



				#Converting csv file to gemotry and creating a geopandas
				points=CRP_df.apply(lambda row: Point(row.Easting, row.Northing),axis=1)


				#azimuth(easting_start, northing_start, easting_end, northing_end)
				CRP_shp_points=gpd.GeoDataFrame(CRP_df,geometry=points)

				#Calculating point to point distance 
				CRP_shp_points['distance']=CRP_shp_points.distance(CRP_shp_points.shift()).cumsum()

				#Creating a decimate point file every tolerance meters
				decimate_CRP=CRP_shp_points[CRP_shp_points['distance']%interval < tolerance]
				decimate_CRP['distance']=decimate_CRP['distance'].astype(int)
				decimate_CRP.drop_duplicates(subset='distance',keep='first',inplace=True)

				#Appending last point on deciamte file
				last_row=CRP_shp_points.tail(1)
				decimate_CRP=decimate_CRP.append(last_row)

				#Drop distance and geometry column 
				CRP_shp_points.drop('distance',axis=1,inplace=True)
				CRP_df.drop('geometry',axis=1,inplace=True)

				#Converting point file to line file
				line = LineString( [[a.x, a.y] for a in CRP_shp_points.geometry.values])

				#First line information for line attribute table
				CRP_line=CRP_df.iloc[:1]


				#Converting Line string to geopandas geometry format
				CRP_line['line']=str(line)
				CRP_line['geometry']=CRP_line.line.apply(wkt.loads)
				CRP_line.drop('line',axis=1,inplace=True)


				#Creating line geopandas and calculate line length 
				CRP_line = gpd.GeoDataFrame(CRP_line, geometry='geometry')
				CRP_line['Length']= CRP_line.length
				CRP_line.drop('distance',axis=1,inplace=True)

				#Appending all created line by line dataframe to lists to concatenate
				CRP_Lines.append(CRP_line)
				CRP_points.append(CRP_shp_points)
				CRP_decimate.append(decimate_CRP)

				#Updating Processing list with processed files 
				with open(list_proc, "a") as f:
					f.write(f"{spl}\n")

				#Progress bar
				progressBar(index,spl_path)		


			

		CRP_point_concat=pd.concat(CRP_points)
		CRP_decimate_concat=pd.concat(CRP_decimate)
		CRP_line_concat=pd.concat(CRP_Lines)

		CRP_line_concat['Block']=""
		CRP_line_concat=CRP_line_concat[['Date','Time','Easting','Northing','Height','LineName','Vessel','Block','Length','geometry']]
		CRP_line_concat.rename(columns={"LineName": "Line"},inplace=True)
		CRP_line_concat=CRP_line_concat.round(3)


		outputFolder=os.path.join(arguments.trackplot_output_folder, 'SHP')

		shp_path=os.path.join(outputFolder, arguments.project_id+'_'+'lines.shp')
		if not os.path.isfile(shp_path):
			CRP_line_concat.to_file(shp_path)
		else:
			CRP_line_temp = gpd.read_file(shp_path)
			CRP_line_concat=CRP_line_temp.append(CRP_line_concat)
			CRP_line_concat.to_file(shp_path)
			

		# shp_path=os.path.join(outputFolder, arguments.project_id+'_'+'points.shp')
		# if not os.path.isfile(shp_path):
		# 	CRP_point_concat.to_file(shp_path)
		# else:
		# 	CRP_point_temp = gpd.read_file(shp_path)
		# 	CRP_point_concat=CRP_point_temp.append(CRP_point_concat)
		# 	CRP_point_concat.to_file(shp_path)

		shp_path=os.path.join(outputFolder, arguments.project_id+'_'+'decimate.shp')
		if not os.path.isfile(shp_path):
			CRP_decimate_concat.to_file(shp_path)
		else:
			CRP_decimate_temp = gpd.read_file(shp_path)
			CRP_decimate_concat=CRP_decimate_temp.append(CRP_decimate_concat)
			CRP_decimate_concat.to_file(shp_path)


		
		#CRP_point_concat.to_file(os.path.join(outputFolder, arguments.project_id+'_'+'points.shp'))
		#CRP_decimate_concat.to_file(os.path.join(outputFolder, arguments.project_id+'_'+'decimate.shp'))
	
	else:
		print("Position files were already processed or there is no position file to process")
		logging.info("Position files were already processed or there is no position file to process")
		logging.info("####################### END #######################") 



	
			
def CRP2csv(path, outputFolder):
	sk_spl = []
	##### Convert FBZ to CSV #####
	filename = os.path.splitext(os.path.basename(path))[0]    


	SPLFilePath = os.path.join(outputFolder, filename + '.txt')
	cmd = 'for %i in ("' + path + '") do %NGPATH%Fugro.DescribedData2Ascii.exe -n3 %i Time Easting Northing Height LineName > "' + SPLFilePath + '"'
	#cmd = 'for %i in ("' + SPLFileName + '") do fbf2asc -n 3 -i %i Time LineName > "' + SPLFilePath + '"'  ## OLD TOOL
	spl_path = path
	try:
		subprocess.run(cmd, shell=True, capture_output=True, close_fds=True) #https://github.com/pyinstaller/pyinstaller/wiki/Recipe-subprocess
		#subprocess.run(cmd, shell=True) ### For debugging
	except subprocess.CalledProcessError as error:
		print(stylize(f'Error to processing the SPL Position file {path}\nError: {error}...\n', fg('red')), flush=True)
		logging.info(f'Error to processing the SPL Position file {path}\nError: {error}...\n')
		sk_spl = spl_path
		df_CRP = pd.DataFrame()
		os.remove(SPLFilePath)


	# Check if empty
	if os.path.getsize(SPLFilePath) == 0:
		logging.info(f'SPL Position file is empty {path}.\n')
		print(f'Please verify the file...', flush=True)

		### LOG
		logging.info(f"SPL Position file is empty {path}. Please verify the file...")
		sk_spl = spl_path
		df_CRP = pd.DataFrame()
		os.remove(SPLFilePath)
	else:
		#if os.path.isfile(SPLFilePath):
		desCheck = pd.read_csv(SPLFilePath, header=None, skipinitialspace=True)    
		# Check if more than 5 colunms. This append when using the wrong Fugro.DescribedData2Ascii.exe
		if len(desCheck.columns) > 5:
			print(stylize(f'The Fugro.DescribedData2Ascii.exe version is wrong. Please copy the correct version the %NGPATH%', fg('red')), flush=True)
			logging.info(f'The Fugro.DescribedData2Ascii.exe version is wrong. Please copy the correct version the %NGPATH%')
			print(f'When Trackplot restart the {path} will be processed.', flush=True)
			print(f'Quitting Trackplot...', flush=True)
			### LOG
			now = datetime.datetime.now()
			with open(log_path, "a") as f:
				f.write(f"{now} -- The Fugro.DescribedData2Ascii.exe version is wrong. Please copy the correct version the %NGPATH%. Quitting TiDDE...")
			sys.exit()
		
		df_CRP = pd.read_csv(SPLFilePath, header=None, skipinitialspace=True, 
									names=["DateTime", "Easting", "Northing", "Height", "LineName"], parse_dates=["DateTime"])

		

		logging.info(f'Reading Fix Position file: {SPLFilePath}') 

		# Cleaning  
		os.remove(SPLFilePath)

		print('########SPL#########')
		print(sk_spl)

	


	return df_CRP, sk_spl
	

###############################################################################
def listFile(folder, ext, exclude):
    ls = [] 
    for root, dirs, files in os.walk(folder, topdown=True):
        dirs[:] = [d for d in dirs if d not in exclude]
        for filename in files:
            if filename.endswith(ext):
                filepath = os.path.join(root, filename)
                ls.append(filepath)  
    return ls

def azimuth(point1_x: float, point1_y: float, point2_x: float, point2_y: float):

	"""

	Calculate azimuth between 2 shapely points

	"""

	degBearing = round(math.degrees(math.atan2(

		(point2_x - point1_x), (point2_y - point1_y))), 0)

	if (degBearing < 0):

		degBearing += 360.0

	return degBearing

# Progress bar GUI and CMD
# adapt from https://www.pakstech.com/blog/python-gooey/
def print_progress(index, total):
    print(f"progress: {index+1}/{total}", flush=True)   

def progressBar(index, ls):
    print_progress(index, len(ls)) # to have a nice progress bar in the GUI            
    if index % math.ceil(len(ls)/10) == 0 and index != (len(ls) - 1): # decimate print
        print(f"Files Process: {index+1}/{len(ls)}", flush=True)
    if index == (len(ls) - 1):
        print(f"Files Process: {index+1}/{len(ls)}", flush=True)
        
def progressBarTime(time_in_s):
    i = 0
    for i in range(time_in_s):
        time.sleep(1)
        print(f"progress: {i + 1}/{time_in_s}", flush=True)