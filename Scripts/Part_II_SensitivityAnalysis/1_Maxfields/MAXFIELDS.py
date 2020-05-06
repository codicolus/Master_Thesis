#!/store/msrad/utils/anaconda3/bin/python
############# General Information ##############
# Author: Christoph von Matt
# Created: 13.06.2019
# Purpose:  This script is mainly for the calculation of spatial maximum fields
#			Other functionalities include temporal statistics of individual timesteps.
#
#			TO DO: more detailed and adjusted header description
#
print("Correct desctiption!")
#exit()
################################################
############# Structural Information ###########
# The script-logic is as follows:
#
#	Part zero: Auxiliary functions
#	Part one: File handling and preparation for statistical assessments + maximum fields
#	Part two: Looping through timesteps and writing out files (at each timestep, to avoid complete loss)
#	Part three: Write out statistics and files which require the loop to be completed (e.g. statistics over entire time period)
################################################
# Libraries
import os
import sys
import inspect
import fnmatch
import zipfile
from zipfile import ZipFile
import numpy as np
import datetime
import rasterio
import rasterio.mask
import pyrad.io
import rasterstats
from shapely import geometry
from pyproj import Proj, transform
from affine import Affine
from matplotlib import path
# additional functions required
from scipy.stats import iqr, ttest_ind, kruskal, mannwhitneyu, normaltest
import csv
import shutil
from multiprocessing import Pool
import matplotlib.pyplot as plt

# Append necessary paths for reading diverse metranet-files
sys.path.append("path_to_metranet_lib")
import metranet
########### AUXILIARY FUNCTIONS ################
# create all daystrings for given period
def get_yrdays(years, doy):
	"""Create Year-DOY strings """
	
	yrdays = list()
	
	for year in years:
		
		if isLeapYear(year):
			doy = doy[0:-1]
		
		yr = str(year)
		yr = yr[2:4]
		
		yrday_partly = [(yr + "{0:03}".format(day)) for day in doy]
		yrdays = yrdays + yrday_partly
	
	return(yrdays)


# returning correctstring of days
def get_productPATH(basepath, time, product, zipped=False):
	"""Returns the path to the zip-files of
	The auxiliary products BZC MZC RZC TRTC CZC"""
	
	yearday = time.strftime("%y%j")
	year = str(time.year)
	
	if zipped:
		return os.path.join(basepath, year, yearday, product+".zip")
	else:
		return os.path.join(basepath, year, yearday, product)


# returns all files (folders excluded) from auxiliary products
def get_auxiliary_files(folder_path, time, full=False, product=None):
	"""Returns files matching time conditions
	-->folders are exluded this way"""
	all_files = os.listdir(folder_path)
	
	if not full:
		if product == "TRTC":
			return [path for path in all_files if fnmatch.fnmatch(path, get_searchpattern(time.strftime("%y%j%H%M"))+".trt")][0]
		
		return [path for path in all_files if fnmatch.fnmatch(path, get_searchpattern(time.strftime("%y%j%H%M")))][0]
	else:
		if product == "TRTC":
			return [path for path in all_files if fnmatch.fnmatch(path, get_searchpattern(time.strftime("%y%j"))+".trt")]
		
		return [path for path in all_files if fnmatch.fnmatch(path, get_searchpattern(time.strftime("%y%j")))]
		


# Creates a search pattern
def get_searchpattern(string):
	return "*" + string + "*"


# Converts timestep strings (yeardoytime) to datetimes
def convert_to_datetimes(timesteps):
	"""converts given timestrings to datetimes"""
	
	
	if len(timesteps) == 1:
		timesteps = timesteps[0]
		hour = timesteps[-4:-2]
		minute = timesteps[-2:]
		date = datetime.datetime.strptime(timesteps[0:5], "%y%j")
		date.replace(hour=int(hour), minute=int(minute))
		return date
	else:
		hours = [timestep[-4:-2] for timestep in timesteps]
		minutes = [timestep[-2:] for timestep in timesteps]
		dates = [datetime.datetime.strptime(timestep[0:5], "%y%j") for timestep in timesteps]
		dates = [dates[i].replace(hour=int(hours[i]), minute=int(minutes[i])) for i in range(len(dates))]
		return dates


# Extract All Zip-Files 
def extractAll(list_of_filepathes, datadir):
	"""Extracts all files from list of ZipFile-pathes
	into "datadir-directory"""
	
	for i in range(len(list_of_filepathes)):
		zipped=ZipFile(list_of_filepathes[i])
		zipped.extractall(datadir)
		zipped.close()
		
	print("Extraction done!")

	
# Extract Individual Files
def extractFileList(zipfile, filelist, datadir, pattern=None):
	"""Function extracts a list of files from Zipfile
	into datadir-directory"""
	
	zipped = ZipFile(zipfile)
	files = zipped.namelist()
	
	if len(filelist) == 0:
		if pattern is None:
			print("Extraction failed!")
			return(None)
		else:
			filelist = [file for file in files if fnmatch.fnmatch(file, pattern)]
	
	if len(filelist) == 0:
		print("Extraction failed!")
		return None
	
	for i in range(len(filelist)):
		zipped.extract(filelist[i], datadir)
	
	zipped.close()
	print("Extraction done!")


# function returns product-file for given timestep
def get_productFileString(product, time, ending=None):
	"""Returns product filestring
	Currently only supported for
	TRTC BZC MZC RZC CZC ZDC HZT"""
	dattim = time
	if product == "HZT":
		hzt_hour = get_hzttime(dattim)
		time = time.replace(hour=hzt_hour, minute=0)
	
	time = time.strftime("%y%j%H%M")
	
	if ending is None:
		
		if product == "TRTC":
			return "CZC" + time + "0T.trt"
		
		if product == "BZC":
			return "BZC" + time + "VL.845"
		
		if product == "MZC":
			return "MZC" + time + "VL.850"
		
		if product == "HZT":
			if dattim.hour%3 == 0:
				return "HZT" + time + "0L.800"
			if dattim.hour%3 == 1:
				return "HZT" + time + "0L.801"
			if dattim.hour%3 == 2:
				return "HZT" + time + "0L.802"
			
		else:
			return product + time + "VL.801"
	else:
		return product + time + ending
	


def convertToGeoTIFF(filelist, prdt_names, outdir, timesteps, onlyvalid=None, ending=None):
	"""This function converts MCH_product_filelist
	to GeoTIFFs.
	Stored in Temporary folder which must exist"""
	
	if ending is None:
		ending = "_GeoTIFF"
	if not isinstance(filelist, list):
		print("Filelist must be of type list!")
		return False
	if not isinstance(prdt_names,list):
		print("Product names must be of type list!")
		return False
	if not isinstance(timesteps, list):
		print("Timesteps must be a of type list!")
		return False
	if (len(filelist) == 0) or (len(outdir) == 0) or (len(timesteps) == 0) or (len(prdt_names) == 0):
		print("One of filelist, outdir, timesteps or prdt_names was of length 0!")
		return False
	if not os.path.exists(outdir):
		print("Outpath does not exist!")
		return False
	
	if onlyvalid is not None:
		timesteps = [timesteps[i] for i in onlyvalid]
		filelist = [filelist[i] for i in onlyvalid]
	if len(prdt_names) != len(filelist):
		if len(prdt_names) == 1:
			prdt_names = prdt_names * len(filelist)
		else:
			print("Length of Product Names and Filelist are not matching!")
			print("Can either be one for all - or must match!")
			return False
	if len(timesteps) != len(filelist):
		if len(timesteps) == 1:
			timesteps = timesteps * len(filelist)
		else:
			print("Length of Timesteps and Filelist are not matching!")
			print("Can either be one for all - or must match!")
			return False
	
	# specification of projection
	meta = {'driver': 'GTiff', 
		'dtype': 'uint8', 
		'nodata': np.nan, 
		'width': 710, 
		'height': 640, 
		'count': 1,
		'crs': rasterio.crs.CRS.from_wkt('PROJCS["SWISS_GRID",GEOGCS["SWISS_GRID",DATUM["CH_1903",SPHEROID["BESSEL 1841",6378137,299.15281]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Hotine_Oblique_Mercator"],PARAMETER["latitude_of_center",46.952406],PARAMETER["longitude_of_center",7.4395833],PARAMETER["azimuth",90],PARAMETER["rectified_grid_angle",90],PARAMETER["scale_factor",1],PARAMETER["false_easting",600000],PARAMETER["false_northing",200000],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]'),
		'transform': rasterio.Affine(1000.0, 0.0, 255000.0, 0.0, -1000.0, 480000.0)}
		
	# Write Temporary GeoTIFFs
	for index, data in enumerate(filelist):
		
		# current values
		timestring = timesteps[index].strftime("%y%j%H%M")
		prdt = prdt_names[index]
		
		# Specify dtype
		meta["dtype"] = str(data.dtype)
		
		# specify filename
		outname = os.path.join(outdir, prdt + timestring + ending +".tiff")
		
		# Write GeoTIFF
		with rasterio.open(outname, "w", **meta) as gtiff_temp:
			gtiff_temp.write(data,1)
		gtiff_temp.close()
		del gtiff_temp
	
	return True





# Function reads + converts metranet-file according to
# data + scale
def read_convert_METRANET(filepath, ZDC=None):
	"""This function reads in MeteoSwiss-Metranet-Files
	and converts values according to data-scale"""
	
	met_file = metranet.read_file(filepath)
	
	if met_file is None:
		return None
	
	data = met_file.data
	scale = met_file.scale
	
	if ZDC:
		scale = scale*200
	
	converted = np.apply_along_axis(convert2scale, 1, data, scale)
	
	if ZDC:
		converted[np.where(converted < 600.)] = np.nan
		converted[np.where(converted > 6000.)] = np.nan
		
	return converted


# function returns nearest HZT-time
def get_hzttime(time):
	"""Returns hour of nearest HZT time - takes datetime object"""
	hour = time.hour
	
	if hour < 3:
		return 0
	elif hour < 6:
		return 3
	elif hour < 9:
		return 6
	elif hour < 12:
		return 9
	elif hour < 15:
		return 12
	elif hour < 18:
		return 15
	elif hour < 21:
		return 18
	else:
		return 21


# Function converts given value according to given scale
# value is used as index for look-up value in scale
def convert2scale(value, scale):
	"""Returns value looked-up in scale"""
	return scale[value]


# Function transforms coordinates into SwissGrid
def transform_2_CH1903(lon, lat):
	"""This function transforms given coordinates (lons, lats)
	to the SwissGrid CH1903"""
	
	projection_ch1903 = rasterio.crs.CRS.from_wkt('PROJCS["SWISS_GRID",GEOGCS["SWISS_GRID",DATUM["CH_1903",SPHEROID["BESSEL 1841",6378137,299.15281]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Hotine_Oblique_Mercator"],PARAMETER["latitude_of_center",46.952406],PARAMETER["longitude_of_center",7.4395833],PARAMETER["azimuth",90],PARAMETER["rectified_grid_angle",90],PARAMETER["scale_factor",1],PARAMETER["false_easting",600000],PARAMETER["false_northing",200000],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]')
	
	inProj = Proj(init="epsg:4326")
	outProj = Proj(projection_ch1903)
	lons, lats = transform(inProj, outProj, lon, lat)
	
	return lons, lats


# TRT-functions
# Function that creates a single Shapely-Polygon out of lon, lat-values
# the lon-lat-coordinates may be reprojected to Swiss Coordinates if necessary
# TODO: think of clause where if only one TRT-cell is available only a Polygon is created instead of MultiPolygon?
def makeTRTPolygon(lon, lat, convertWGS84ToCH1903):
	"""This function makes a Shapely Polygon out of TRT-coordinates"""
	
	#projection_ch1903 = rasterio.crs.CRS.from_wkt('PROJCS["SWISS_GRID",GEOGCS["SWISS_GRID",DATUM["CH_1903",SPHEROID["BESSEL 1841",6378137,299.15281]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Hotine_Oblique_Mercator"],PARAMETER["latitude_of_center",46.952406],PARAMETER["longitude_of_center",7.4395833],PARAMETER["azimuth",90],PARAMETER["rectified_grid_angle",90],PARAMETER["scale_factor",1],PARAMETER["false_easting",600000],PARAMETER["false_northing",200000],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]')
	
	#lons = lon
	#lats = lat
	if convertWGS84ToCH1903:
		#inProj = Proj(init="epsg:4326")
		#outProj = Proj(init="epsg:21781")
		#outProj = Proj(projection_ch1903)
		#lons, lats = transform(inProj, outProj, lons, lats)
		lons, lats = transform_2_CH1903(lon, lat)
	
	coords = list(zip(lons, lats))
	
	return geometry.Polygon(coords)


# Function to create a Multipolygon out of all available TRT-cells within TRT-File
# Coordinates may be reprojected to Swiss Coordinates if necessary
def TRT_Multi_Polygon(TRT_cell_coordinates, convertWGS84ToCH1903):
	"""This function creates a MultiPolygon from all TRT-cells"""
	
	poly_list = [makeTRTPolygon(TRT_cell_coordinates[i]["lon"], TRT_cell_coordinates[i]["lat"], convertWGS84ToCH1903) for i in range(len(TRT_cell_coordinates))]
	
	return geometry.MultiPolygon(poly_list)


# Function which transforms TRTC_coordinates to a Matplotlib-Path object
def createPathObject(lon, lat, convertWGS84ToCH1903):
	"""Function creates path object out of coordinate lists lon + lat
	Returns a matplotlib.path Object
	--only transforms from WGS84 (TRT-original crs) to CH1903"""
	
	# Convert to CH1903 if true
	if convertWGS84ToCH1903:
		lons, lats = transform_2_CH1903(lon, lat)
	else:
		lons, lats = lon, lat
	
	coords = list(zip(lons, lats))
	
	return path.Path(coords)


# Function creates a meshgrid for given file with all coordinates
def create_coordinateMESHGRID(data_tiff):
	"""Function creates a meshgrid of given TIFF-file
	- returns x, y coordinate array (1D)"""
	
	# get bounds
	nx, ny = data_tiff.width, data_tiff.height
	
	# get transformation from file
	transformation_data = data_tiff.transform
	
	# generate meshgrid
	x, y = np.meshgrid(np.arange(nx) + 0.5, np.arange(ny) + 0.5) * transformation_data
	
	return x, y


# Function determines which points lay within Path Object
def points_within_PathObj(path_obj, x, y):
	"""Function returns True if point is within Path Object,
	False if not (for whole array)
	- Takes a path-obj + x and y meshgrids"""
	
	# Stackoverflow: What's the faastest way of checking if a point is inside a polygon in python
	indizes = path_obj.contains_points(np.hstack((x.flatten()[:, np.newaxis], y.flatten()[:, np.newaxis])))
	
	return np.where(indizes == True)[0]


# Function determines which points lay within a given TRTC-cell
def points_within_TRTCcell(TRTC_contours, data_tiff, convertWGS84ToCH1903=True):
	"""This function returns all points which lay within given TRTC-cell contours
	- Takes a dictionary of "lon" + "lat" and a TIFF-file for geographic location"""
	
	# create path-object from TRTC-contours
	TRTC_pathObj = createPathObject(TRTC_contours["lon"], TRTC_contours["lat"], convertWGS84ToCH1903)
	
	# retrieve coordinates meshgrid
	x, y = create_coordinateMESHGRID(data_tiff)
	
	# return points which lay within given TRTC-path-object
	return points_within_PathObj(TRTC_pathObj, x, y)



###############################################################################
# Function extracts given key from list of dictionaries
def extract_key(list_of_dicts, key):
	"""Extracts given key for every dictionary in list"""
	
	return [dict({key: data[key]}) for data in list_of_dicts]



# Function creates ONE dictionary out of a list of dictionaries by summing up on common keys
def unifyDictionaries2timestep(stats):
	"""This function unifies a list of dictionaries by summing up on common keys
	- used to prepare for writing out stats"""
	if len(stats) == 0:
		print("No dictionaries found or provided!")
		return None
	if not isinstance(stats, list):
		print("Please provide a dictionary!")
		return None
	if not isinstance(stats[0], dict):
		print("Items in list are not dicts!")
		return None
	
	# get keys
	stats_keys = list(stats[0].keys())
	
	# unify lists per key
	unified = [[stat[key] for stat in stats] for key in stats_keys]
	
	return dict(list(zip(stats_keys, unified)))


def create_SummaryStats(ZDC_data, withMask=False, withinTRT=False, mask="None", diffstats=False):
	"""Creates summary statistics for provided ZDC_data.
	Data can be either provided:
	1) without Mask (all values are taken into account)
	2) With Mask
	"""
	data = ZDC_data
	
	# Determine if with mask or not and within TRT-cells or Outside TRT-cells
	if withMask:
		if (mask != "None") and withinTRT:
			data = data[np.where(mask == False)]
		if (mask != "None") and (not withinTRT):
			data = data[np.where(mask == True)]
	
	if diffstats:
		data_gt0 = np.isnan(data)
		data_gt0 = data[np.where(data_gt0 == False)]
	else:
		data_gt0 = data[np.where(data > 0)]
	
	all_pix = len(data)
	if diffstats:
		all_pix = data.shape[0]*data.shape[1]
	
	
	num_columns = len(data_gt0)
	# Create Statistics
	if len(data_gt0) > 0:
		min_zdc = np.nanmin(data_gt0)
		max_zdc = np.nanmax(data_gt0)
		mean_zdc = np.nanmean(data_gt0)
		median_zdc = np.nanmedian(data_gt0)
		st_dev = np.std(data_gt0)
		int_qrt = iqr(data_gt0, nan_policy="omit")
	else:
		min_zdc, max_zdc, mean_zdc, median_zdc, st_dev, int_qrt = [np.nan]*6
	
	num_gt1000 = len(np.where(data >= 1000)[0])
	num_gt1400 = len(np.where(data >= 1400)[0])
	num_gt2000 = len(np.where(data >= 2000)[0])
	num_gt2400 = len(np.where(data >= 2400)[0])
	num_gt3000 = len(np.where(data >= 3000)[0])
	num_gt3400 = len(np.where(data >= 3400)[0])
	num_gt4000 = len(np.where(data >= 4000)[0])
	num_gt4400 = len(np.where(data >= 4400)[0])
	num_gt5000 = len(np.where(data >= 5000)[0])
	num_gt5400 = len(np.where(data >= 5400)[0])
	num_gt6000 = len(np.where(data >= 6000)[0])
	
	return np.array([all_pix, num_columns, min_zdc, max_zdc, mean_zdc, median_zdc, st_dev, int_qrt, num_gt1000, num_gt1400, num_gt2000, 
		num_gt2400, num_gt3000, num_gt3400, num_gt4000, num_gt4400, num_gt5000, num_gt5400, num_gt6000])


stats_variables = np.array(["all_pix", "num_columns", "min_zdc", "max_zdc", "mean_zdc", "median_zdc", "st_dev", "int_qrt", "num_gt1000", "num_gt1400",
	"num_gt2000", "num_gt2400", "num_gt3000", "num_gt3400", "num_gt4000", "num_gt4400", "num_gt5000", "num_gt5400", "num_gt6000"])



def get_indizes_for_all_stacked(stacked):
	"""Retrieves the indizes which are valid (>= 0)"""
	return [i for i in range(640*710) if not np.all(np.isnan(stacked[:,i]))]


def calculate_kruskal_cellwise(data, refdat, indizes):
	"""Calculates kruskal statistics for each cell!
	and returns only p-values
	- parallelized using starmap"""
	combinations = [list(tuple([data[:,i], refdat[:,i]])) for i in indizes]
	
	p = Pool()
	result = p.starmap(kruskal_exeption_handled, combinations)
	p.close()
	del p
	
	p_vals = [dat[1] for dat in result]
	
	return p_vals

def kruskal_exeption_handled(dat, ref):
	
	dat_gt0 = dat[np.where(dat >= 0)]
	inds = np.where(dat >= 0)
	ref_gt0 = ref[inds]
	
	
	
	try:
		result = kruskal(dat_gt0, ref_gt0, nan_policy="omit")
	except ValueError:
		return np.array([np.nan, 1.0])
	except ZeroDivisionError:
		return np.array([np.nan, np.nan])
	else:
		return result


# function which converts shape back to 640x710 grid
def back_2_640x710(value_list, indizes_list):
	"""This function returns a reshaped array with all p-values stored in
	provided indizes (shape = 640x710)"""
	
	out_arr = np.zeros((640*710))
	out_arr[:] = np.nan
	
	indizes = np.array(indizes_list)
	values = np.array(value_list)
	
	out_arr[indizes] = values
	
	return out_arr.reshape(640, 710)

# function which stores values in correct indizes
def correct_spatialP(value_list, indizes_list):
	"""This function returns a reshaped array with all p-values stored in
	provided indizes (shape = 640*710)"""
	
	out_arr = np.zeros((640*710))
	out_arr[:] = np.nan
	
	indizes = np.array(indizes_list)
	values = np.array(value_list)
	
	out_arr[indizes] = values
	
	return out_arr


def write_row_Allcolumns(filename, all_columns):
	"""This function appends columns to given column file"""
	csv_file = open(filename, "a")
	temp_writer = csv.writer(csv_file)
	for i in all_columns:
		temp_writer.writerow([i])
	
	csv_file.close()
	del csv_file


def plot_BOXPLOT_timestep(data_within, data_outside, timestep, combination, savedir, type_test):
	"""Function plots boxplot for comparison within vs. outside TRT-cells"""
	figname = timestep + "_" + type_test +"_boxplot.png"
	fig = plt.figure(figsize=(10,10))
	ax = fig.add_subplot(111)
	ax.set_ylim(0,10500)
	ax.boxplot([data_within, data_outside], showfliers=True, notch=False)
	ax.axhline(np.nanmedian(data_within))
	
	if type_test == "kruskal":
		sigtest = kruskal(data_within, data_outside)[1]
	
	if type_test == "mannwhitneyu":
		sigtest = mannwhitneyu(data_within, data_outside)[1]
	
	normal = [normaltest(data_within)[1], normaltest(data_outside)[1]]
	
	ax.set_xticklabels(["within TRTC", "outside TRTC"])
	ax.text(x=0.6, y=(ax.get_ybound()[1] - (ax.get_ybound()[1]/20)), s= type_test +" (p-val): %.3f" % sigtest)
	ax.text(x=0.6, y=(ax.get_ybound()[1] - (ax.get_ybound()[1]/20)*2), 
		s= "normtest (p-val): %.3f / %.3f" % (normal[0], normal[1]))
	ticks = ax.get_xticks()
	ax.text(x=ticks[0]+0.05, y=0.5, s="Num: " + str(len(data_within)))
	ax.text(x=ticks[1]+0.05, y=0.5, s="Num: " + str(len(data_outside)))
	zh = combination.split("_")[2]
	zdr = combination.split("_")[3]
	dattim = datetime.datetime.strptime(timestep, "%y%j%H%M")
	ax.set_title("Date-Time: " + str(dattim) + " / " + "ZDR={} ZH={}".format(zdr,zh))
	
	fig.savefig(os.path.join(figsavedir, figname))
	del fig


def createSumStats_AllColumns(filename):
	"""Creates Summary Stats of All Columns"""
	
	import pandas as pd
	data = np.array(pd.read_csv(filename).T)[0]
	
	return create_SummaryStats(data)

def write_rows_fields(filename, fields):
	""""This function writes fields"""
	csvfile = open(filename, "a")
	writer = csv.writer(csvfile)
	written = [writer.writerow(list(fields[:, i])) for i in range(640*710)]
	csvfile.close()
	del csvfile
	
	if all(written):
		return True
	else:
		return False


def write_row_indiv(filename, row):
	"""This functions aim to write individual timesteps"""
	csvfile = open(filename, "a")
	writer = csv.writer(csvfile)
	written = writer.writerow(row)
	csvfile.close()
	del csvfile
	
	if written:
		return True
	else:
		return False


################################################
# Get Command_line arguments (first is always script name)
# Arguments to specify:
#	-basepath: path to where data is stored; MCH-folder structure; one level higher than folder "year"
#	-year
#	-year_ds: yr-doy (year - day-of-year) e.g. 2 Aug 2017 = 17214, several yeardays can be given
args = sys.argv
args = args[1:]
#
#basepath = args[0]
#sensitivity_type = args[1]


basepath = args[0]

# yeardays=np.array(["17213", "17214"])
year_ds = args[1]
yeardays=np.array(year_ds.split(","))

#trt_IDs = set()
#previous_TRTC_cells = set()


outfoldername = "Maxfields"
timespan = 12
part = 0

#count_all_timesteps = 0


trt_indizes = {"traj_ID": 0, "yyyymmddHHMM": 1, "lon": 2, "lat": 3, "ell_L": 4, "ell_S": 5, "ell_or": 6, "area": 7, "vel_x": 8, "vel_y": 9,
		"det": 10, "RANKr": 11, "CG-": 12, "CG+": 13, "CG": 14, "%CG+": 15, "ET45": 16, "ET45m": 17, "ET15": 18, "ET15m": 19, "VIL": 20,
		"maxH": 21, "maxHm": 22, "POH": 23, "RANK": 24, "Dvel_x": 25, "Dvel_y": 26, "cell_contour_lon-lat": 27}

trt_description = {"traj_ID": {"title" : "Trajectory ID", "units" : None}, "yyyymmddHHMM": {"title" : "Time", "units" : None}, 
		"lon": {"title" : "Longitude", "units" : "degree"}, "lat": {"title" : "Latitude", "units" : "degree"}, 
		"ell_L": {"title" : "Diameter (long-side)", "units": "km"}, "ell_S": {"title" : "Diameter (short-side)", "units" : "km"}, 
		"ell_or": {"title" : "Ellipsis Orientation", "units": "degree"}, 
		"area": "Area [km]", "vel_x": "Cell Speed (W/E) [km/h]", "vel_y": {"title" : "Cell Speed (N/S)", "units": "km/h"}, 
		"det": {"title" : "Detection Threshold", "units" : "dBZ"}, "RANKr": {"title" : "Severity Ranking", "units" : None}, 
		"CG-": {"title" : "Negative Cloud-Ground Lightning (CG-)", "units" : None}, 
		"CG+": {"title" : "Positive Cloud-Ground Lightning (CG+)", "units" : None}, "CG": {"title" : "Total Cloud-Ground Lightning", "units" : None}, 
		"%CG+": {"title" : "Ratio of Positive CG-Lightning", "units" : "%"}, "ET45": {"title" : "EchoTop45 (max)", "units" : "km"}, 
		"ET45m": {"title" : "EchoTop45 (median)", "units" : "km"}, "ET15": {"title" : "EchoTop15 (max)", "units" : "km"}, 
		"ET15m": {"title" : "EchoTop15 (median)", "units" : "km"}, "VIL": {"title" : "Vertical Integrated Liquid", "units" : "km/m2"}, 
		"maxH": {"title" : "Height of maximum reflectivity", "units" : "km"}, 
		"maxHm": {"title" : "Height of maximum reflectivity (median)", "units" : "km"}, "POH" : {"title" : "Probability of Hail", "units": "%"}, 
		"RANK": {"title" : "Severity Rank (deprecated)", "units" : None}, 
		"Dvel_x": {"title" : "Cell Speed Standard Deviation (W/E, from previous)", "units" : "km/h"}, 
		"Dvel_y": {"title" : "Cell Speed Standard Deviation (N/S, from previous)", "units" : "km/h"}, 
		"cell_contour_lon-lat": {"title" : "Cell Contours", "units" : "lon-lat" }}

print("Starting Yearday-Loop")
# Loop through years
for count_yearday, yearday in enumerate(yeardays):
	
	# Specify initial variables
	year= "20" + yearday[0:2]
	day = yearday[2:]
	current_time = datetime.datetime.strptime(yearday, "%y%j")
	
	# Where the data is stored
	datadir= os.path.join(basepath, year, yearday)
	# folders in datadir
	folders = set(os.listdir(datadir))
	
	# Specifying different data_pathes (folder-structure)
	TRTC_zippath = get_productPATH(basepath, current_time, "TRTC", zipped=True)
	CZC_zippath = get_productPATH(basepath, current_time, "CZC", zipped=True)
	BZC_zippath = get_productPATH(basepath, current_time, "BZC", zipped=True)
	MZC_zippath = get_productPATH(basepath, current_time, "MZC", zipped=True)
	ZDC_zippath = get_productPATH(basepath, current_time, "ZDC", zipped=True)
	HZT_zippath = get_productPATH(basepath, current_time, "HZT", zipped=True)
	
	TRTC_path = get_productPATH(basepath, current_time, "TRTC")
	CZC_path = get_productPATH(basepath, current_time, "CZC")
	BZC_path = get_productPATH(basepath, current_time, "BZC")
	MZC_path = get_productPATH(basepath, current_time, "MZC")
	ZDC_path = get_productPATH(basepath, current_time, "ZDC")
	HZT_path = get_productPATH(basepath, current_time, "HZT")
	
	folders2delete = set([TRTC_path, ZDC_path, CZC_path, BZC_path, MZC_path, HZT_path])
	
	# Adjust for threshold_folder (FOR SENSITIVITY ANALYSIS ONLY!)-------------------------------------------
	# TODO: Implement here when Sensitivity Test = Filtering that folder is only filtering - folder!
	#zh_threshs = np.array(["0", "15", "20", "25", "28", "30"])
	zh_threshs = np.array(["0", "25", "30", "35", "40", "45"])
	zdr_threshs = np.array(["1.0", "0.95", "0.9", "0.85", "0.8", "0.74"])
	ZDC_SA_folders = ["ZDC_thresh_{}_{}".format(zh, zdr) for zh in zh_threshs for zdr in zdr_threshs]
	reference_folder = ZDC_SA_folders[0]
	ZDC_SA_folders = ZDC_SA_folders[1:]
	ZDC_paths = [os.path.join(ZDC_path, zdc_folder) for zdc_folder in ZDC_SA_folders]
	
	reference_path = os.path.join(ZDC_path, reference_folder)
	
	# Extraction Sensitivity Analysis
	extractAll([TRTC_zippath, ZDC_zippath, CZC_zippath, BZC_zippath, MZC_zippath, HZT_zippath], datadir)
	
	# Get all TRT-files + derived (available) timesteps
	TRTC_files = get_auxiliary_files(TRTC_path, current_time, full=True, product="TRTC")
	
	alltimesteps = [TRT_file[-15:-6] for TRT_file in TRTC_files]
	alldatetimes = convert_to_datetimes(alltimesteps)
	
	# 12-hour constraints (centered around event)
	# 17176 event
	if timespan == 12:
		if (count_yearday == 0)&(yearday == "17175"):
			at_which = alltimesteps.index("171752000")
			alltimesteps = alltimesteps[at_which:]
			alldatetimes = alldatetimes[at_which:]
			
		if (count_yearday == 1)&(yearday == "17176"):
			at_which = alltimesteps.index("171760800")
			alltimesteps = alltimesteps[:at_which]
			alldatetimes = alldatetimes[:at_which]
		
		# 17211 event
		if (count_yearday == 0)&(yearday == "17211"):
			at_which = alltimesteps.index("172111200")
			alltimesteps = alltimesteps[at_which:]
			alldatetimes = alldatetimes[at_which:]
		
		# 17214 event
		if (count_yearday == 0)&(yearday == "17213"):
			at_which = alltimesteps.index("172131300")
			alltimesteps = alltimesteps[at_which:]
			alldatetimes = alldatetimes[at_which:]
		
		if (count_yearday == 1)&(yearday == "17214"):
			#at_which = alltimesteps.index("172140730")
			at_which = alltimesteps.index("172140320")
			#at_which = alltimesteps.index("172140020")
			alltimesteps = alltimesteps[:at_which]
			alldatetimes = alldatetimes[:at_which]
		
		# 18150 event
		if (count_yearday == 0)&(yearday == "18150"):
			at_which = alltimesteps.index("181501000")
			alltimesteps = alltimesteps[at_which:]
			alldatetimes = alldatetimes[at_which:]
			
		# 18185 event
		if (count_yearday == 0)&(yearday == "18185"):
			at_which = alltimesteps.index("181850530")
			at_which_end = alltimesteps.index("181851730")
			alltimesteps = alltimesteps[at_which:at_which_end]
			alldatetimes = alldatetimes[at_which:at_which_end]
		
	if timespan == 12:
		if part == 1:
			if (count_yearday == 1)&(yearday == "17176"):
				at_which = alltimesteps.index("171760320")
				alltimesteps = alltimesteps[:at_which]
				alldatetimes = alldatetimes[:at_which]
			
			if (count_yearday == 0)&(yearday == "17211"):
				at_which = alltimesteps.index("172111920")
				alltimesteps = alltimesteps[:at_which]
				alldatetimes = alldatetimes[:at_which]
			
			if (count_yearday == 0)&(yearday == "17213"):
				at_which = alltimesteps.index("172132240")
				alltimesteps = alltimesteps[:at_which]
				alldatetimes = alldatetimes[:at_which]
			
			if (count_yearday == 0)&(yearday == "18150"):
				at_which = alltimesteps.index("181501920")
				alltimesteps = alltimesteps[:at_which]
				alldatetimes = alldatetimes[:at_which]
			
			if (count_yearday == 0)&(yearday == "18185"):
				at_which = alltimesteps.index("181851250")
				alltimesteps = alltimesteps[:at_which]
				alldatetimes = alldatetimes[:at_which]
		
		if part == 2:
			if (count_yearday == 0)&(yearday == "17176"):
				at_which = alltimesteps.index("171760105")
				at_which_end = alltimesteps.index("171760800")
				alltimesteps = alltimesteps[at_which:at_which_end]
				alldatetimes = alldatetimes[at_which:at_which_end]
			
			if (count_yearday == 0)&(yearday == "17211"):
				at_which = alltimesteps.index("172111705")
				alltimesteps = alltimesteps[at_which:]
				alldatetimes = alldatetimes[at_which:]
			
			if (count_yearday == 0)&(yearday == "17213"):
				at_which = alltimesteps.index("172132025")
				alltimesteps = alltimesteps[at_which:]
				alldatetimes = alldatetimes[at_which:]
			
			if (count_yearday == 0)&(yearday == "18150"):
				at_which = alltimesteps.index("181501705")
				alltimesteps = alltimesteps[at_which:]
				alldatetimes = alldatetimes[at_which:]
			
			if (count_yearday == 0)&(yearday == "18185"):
				at_which = alltimesteps.index("181851035")
				alltimesteps = alltimesteps[at_which:]
				alldatetimes = alldatetimes[at_which:]
			
			
	# ev
	
	# ONLY FOR TESTING
	#if count_yearday == 0:
	#	alltimesteps = alltimesteps[-20:]
	#	alldatetimes = alldatetimes[-20:]
	
	# update timestep counter
	#count_all_timesteps += len(alltimesteps)
	
	# Preparation for statistics
	# make TRT-polygons
	# TRT_dict for storing IDs to see whether one new cell was introduced
	# Rasterfiles of ZDC, and other products (in temporary folder)
	
	# LOOP THROUGH ALL TIMESTEPS OF ONE GIVEN DAY
	for index, timestep in enumerate(alltimesteps):
		
		# get datetime information
		current_datetime = alldatetimes[index]
		
		# get all files of current time step
		TRTC_filepath = os.path.join(TRTC_path, fnmatch.filter(TRTC_files, "*" + timestep + "*")[0])
		
		# Read TRTC-data
		TRTC_data = np.array(pyrad.io.read_trt_data(TRTC_filepath))
		
		# if no data in TRT_file continue
		if TRTC_data[0] is None:
			all_out = True
		else:
			all_out = False
			
		
		
		#if all_out:
		#	count_all_timesteps = count_all_timesteps - 1
		#	continue
		
		# ---------------------------------------------------------------------------------------------------------------
		
		# determine filepaths + reference file path
		ZDC_filepaths = [os.path.join(path, get_auxiliary_files(path, current_datetime)) for path in ZDC_paths]
		reference_filepath = os.path.join(reference_path, get_auxiliary_files(reference_path, current_datetime))
		
		# CONVERSION TO TEMPORARY GEOTIFF-FILES!  
		ZDC_data = [read_convert_METRANET(zdc_file, ZDC=True) for zdc_file in ZDC_filepaths]
		reference_data = read_convert_METRANET(reference_filepath, ZDC=True)
		
		# DIFFERENCES + DIFFERENCE STATS
		ZDC_differences = [np.subtract(threshcomb, reference_data) for threshcomb in ZDC_data]
		
		# FOLDER CREATION + STORING STRUCUTRE INITIALISATION
		
		if (index == 0)&(count_yearday == 0):
			# TEMPDIR
			tempdir = os.path.join(datadir, "Temporary")
			if not os.path.exists(tempdir):
				os.makedirs(tempdir)
			
			tempdir_reference = os.path.join(tempdir, reference_folder)
			if not os.path.exists(tempdir_reference):
				os.makedirs(tempdir_reference)
		
				
		# OUTDIRECTORY + FILE INITIALITATION
		if (index == 0)&(count_yearday == 0):
			outdir =  os.path.join(datadir, "Output")
			if not os.path.exists(outdir):
				os.makedirs(outdir)
			
			sa_dir = os.path.join(outdir, outfoldername)
			if not os.path.exists(sa_dir):
				os.makedirs(sa_dir)
			
			filenames = ["overall_field_mean", "overall_field_meandiff", "overall_field_max", "overall_field_maxdiff", "counts", "timesteps",
				"overall_fieldmax_timesteps", "overall_fieldmaxdiff_timesteps", "zdc_czc_max", "zdc_hzt_max", "zdc_czc_diffmax", 
				"zdc_hzt_diffmax"]
			
			file_dirs = [os.path.join(sa_dir, name + ".txt") for name in filenames]
			
			overall_field_mean = open(file_dirs[0], "a")
			ovfieldmean_writer = csv.writer(overall_field_mean)
			ovfieldmean_writer.writerow([reference_folder] + ZDC_SA_folders)
			
			overall_field_meandiff = open(file_dirs[1], "a")
			ovfieldmeandiff_writer = csv.writer(overall_field_meandiff)
			ovfieldmeandiff_writer.writerow(ZDC_SA_folders)
			
			overall_field_max = open(file_dirs[2], "a")
			ovfieldmax_writer = csv.writer(overall_field_max)
			ovfieldmax_writer.writerow([reference_folder] + ZDC_SA_folders)
			
			overall_field_maxdiff = open(file_dirs[3], "a")
			ovfieldmax_writer = csv.writer(overall_field_maxdiff)
			ovfieldmax_writer.writerow(ZDC_SA_folders)
			
			counts_file = open(file_dirs[4], "a")
			counts_writer = csv.writer(counts_file)
			counts_writer.writerow([reference_folder] + ZDC_SA_folders)
			
			timestepsfile = open(file_dirs[5], "a")
			timesteps_writer = csv.writer(timestepsfile)
			timesteps_writer.writerow(["timesteps"])
			
			overall_fmax_ts = open(file_dirs[6], "a")
			ov_fmaxts_writer = csv.writer(overall_fmax_ts)
			ov_fmaxts_writer.writerow([reference_folder] + ZDC_SA_folders)
			
			overall_fmaxdiff_ts = open(file_dirs[7], "a")
			ov_fmaxdiffts_writer = csv.writer(overall_fmaxdiff_ts)
			ov_fmaxdiffts_writer.writerow(ZDC_SA_folders)
			
			zdc_czc_maxfile = open(file_dirs[8], "a")
			zdc_czc_maxwriter = csv.writer(zdc_czc_maxfile)
			zdc_czc_maxwriter.writerow([reference_folder] + ZDC_SA_folders)
			
			zdc_hzt_maxfile = open(file_dirs[9], "a")
			zdc_hzt_maxwriter = csv.writer(zdc_hzt_maxfile)
			zdc_hzt_maxwriter.writerow([reference_folder] + ZDC_SA_folders)
			
			zdc_czc_diffmaxfile = open(file_dirs[10], "a")
			zdc_czc_diffmaxwriter = csv.writer(zdc_czc_diffmaxfile)
			zdc_czc_diffmaxwriter.writerow(ZDC_SA_folders)
			
			zdc_hzt_diffmaxfile = open(file_dirs[11], "a")
			zdc_hzt_diffmaxwriter = csv.writer(zdc_hzt_diffmaxfile)
			zdc_hzt_diffmaxwriter.writerow(ZDC_SA_folders)
			
			filelist = [overall_field_mean, overall_field_meandiff, overall_field_max, overall_field_maxdiff,
				counts_file, timestepsfile, overall_fmax_ts, overall_fmaxdiff_ts, zdc_czc_maxfile, zdc_hzt_maxfile,
				zdc_czc_diffmaxfile, zdc_hzt_diffmaxfile]
			
			[f.close() for f in filelist]
			del filelist
		
		
		# GEOTIFF CONVERSION
		if (index == 0)&(count_yearday == 0):
			converted = convertToGeoTIFF([reference_data], ["ZDC"], tempdir_reference, [current_datetime])
			if not converted:
				print("Failed to convert reference data to GeoTIFF on current-timestep!")
			
			# READ IN CREATED GeoTIFF FILES!
			# Specify ending + pathes
			tl = "_GeoTIFF.tiff"
			reference_tiffpath = os.path.join(tempdir_reference, get_productFileString("ZDC", current_datetime, tl))
		
		# Open TIFF-files
		reference_tiff = rasterio.open(reference_tiffpath)
		
		# TRT_POLYGON CREATION
		TRTC_multipolygon = TRT_Multi_Polygon(TRTC_data[trt_indizes["cell_contour_lon-lat"]], convertWGS84ToCH1903=True)
		
		# ASSESS STATISTICS_________________________________________________________________________________
		
		# Create TRTC-mask
		TRTC_mask = rasterio.mask.raster_geometry_mask(reference_tiff, TRTC_multipolygon)
		
		reference_tiff.close()
		del reference_tiff
		
		# Read in CZC for masking
		CZC_filepath = os.path.join(CZC_path, get_productFileString("CZC", current_datetime))
		CZC_data = read_convert_METRANET(CZC_filepath)
		if CZC_data is None:
			CZC_data = np.zeros((640,710))
			CZC_data[:,:] = np.nan
		
		
		# Read in BZC for max-field
		BZC_filepath = os.path.join(BZC_path, get_productFileString("BZC", current_datetime))
		BZC_data = read_convert_METRANET(BZC_filepath)
		if BZC_data is None:
			#alternative_time = current_datetime + datetime.timedelta(minutes=2)
			#BZC_filepath = os.path.join(BZC_path, get_productFileString("BZC", alternative_time))
			#BZC_data = read_convert_METRANET(BZC_filepath)
			BZC_data = np.zeros((640, 710))
			BZC_data[:,:] = np.nan
		
		
		# Read in MZC for max-field
		MZC_filepath = os.path.join(MZC_path, get_productFileString("MZC", current_datetime))
		MZC_data = read_convert_METRANET(MZC_filepath)
		if MZC_data is None:
			MZC_data = np.zeros((640, 710))
			MZC_data[:,:] = np.nan
		
		
		
		HZT_filepath = os.path.join(HZT_path, get_productFileString("HZT", current_datetime))
		HZT_data = read_convert_METRANET(HZT_filepath)
		if HZT_data is None:
			HZT_data = np.zeros((640,710))
			HZT_data[:,:] = np.nan
		
		
		# Initialize data_storage
		if (index == 0)&(count_yearday == 0):
			
			ZDC_alltimesteps = [np.zeros([640, 710]) for i in range(len(ZDC_data))]
			# for differences (thus reference not included)
			ZDC_differences_alltimesteps = [np.zeros([640, 710]) for i in range(len(ZDC_data))]
			
			ZDC_max_alltimesteps = [np.zeros([640, 710]) for i in range(len(ZDC_data))]
			ZDC_CZC_max_alltimesteps = [np.zeros([640,710]) for i in range(len(ZDC_data))]
			ZDC_HZT_max_alltimesteps = [np.zeros([640,710]) for i in range(len(ZDC_data))]
			
			ZDC_maxdiff_alltimesteps = [np.zeros([640,710]) for i in range(len(ZDC_differences))]
			ZDC_CZC_maxdiff_alltimesteps = [np.zeros([640,710]) for i in range(len(ZDC_differences))]
			ZDC_HZT_maxdiff_alltimesteps = [np.zeros([640,710]) for i in range(len(ZDC_differences))]
			
			counts_zdc = [np.zeros([640, 710]) for i in range(len(ZDC_data))]
			counts_zdc_diff = [np.zeros([640, 710]) for i in range(len(ZDC_differences))]
			# sum up all timesteps
			reference_alltimesteps = np.zeros([640,710])
			reference_max_alltimesteps = np.zeros([640, 710])
			reference_CZC_max_alltimesteps = np.zeros([640,710])
			reference_HZT_max_alltimesteps = np.zeros([640, 710])
			
			# set up counts (nan's will not be counted for final division!)
			counts_reference = np.zeros([640, 710])
			
			# occurrence time fields
			reference_max_occurrencetime = np.zeros([640,710]).astype(int)
			ZDC_max_occurrencetime = [np.zeros([640,710]).astype(int) for i in range(len(ZDC_data))]
			ZDC_maxdiff_occurrencetime = [np.zeros([640,710]).astype(int) for i in range(len(ZDC_differences))]
			
			# other maxfields
			TRTC_occurrencetime = np.zeros([640,710]).astype(int)
			TRTC_alltimesteps = np.zeros([640,710])
			BZC_occurrencetime = np.zeros([640,710]).astype(int)
			BZC_maxfield = np.zeros([640, 710])
			MZC_occurrencetime = np.zeros([640,710]).astype(int)
			MZC_maxfield = np.zeros([640, 710])
			CZC_occurrencetime = np.zeros([640,710]).astype(int)
			CZC_maxfield = np.zeros([640,710])
			
			# HZT MAX + MIN FIELDS
			HZT_maxfield = np.zeros([640,710])
			HZT_minfield = HZT_data.copy()
			HZT_maxfield_occurrencetime = np.zeros([640,710]).astype(int)
			HZT_minfield_occurrencetime = np.zeros([640,710]).astype(int)
			HZT_minfield_occurrencetime[:,:] = timestep
		
			
		# SUM UP DIFFERENCES + NORMAL COLUMNS
		gtgl0_ref = np.where(reference_data >= 0)
		gtgl0_data = [np.where(data >= 0) for data in ZDC_data]
		# differences gtgl0
		gtgl0_diff = [np.where(data >= 0) for data in ZDC_differences]
		
		# add reference data
		reference_alltimesteps[gtgl0_ref] = (reference_alltimesteps[gtgl0_ref] + reference_data[gtgl0_ref])
		counts_reference[gtgl0_ref] += 1
		
		# updating reference max alltimesteps
		toUpdate = np.where(reference_max_alltimesteps < reference_data)
		reference_max_alltimesteps[toUpdate] = reference_data[toUpdate]
		reference_max_occurrencetime[toUpdate] = int(timestep)
		
		if CZC_data is not None:
			reference_CZC_max_alltimesteps[toUpdate] = CZC_data[toUpdate]
		
		if HZT_data is not None:
			reference_HZT_max_alltimesteps[toUpdate] = HZT_data[toUpdate]
		
		# add threshcomb data
		for i in range(len(ZDC_data)):
			
			# Updating max array
			toUpdate = np.where(ZDC_max_alltimesteps[i] < ZDC_data[i])
			ZDC_max_alltimesteps[i][toUpdate] = ZDC_data[i][toUpdate]
			ZDC_max_occurrencetime[i][toUpdate] = int(timestep)
			
			if CZC_data is not None:
				ZDC_CZC_max_alltimesteps[i][toUpdate] = CZC_data[toUpdate]
			
			if HZT_data is not None:
				ZDC_HZT_max_alltimesteps[i][toUpdate] = HZT_data[toUpdate]
			
			
			# maxdiff array
			toUpdate = np.where(ZDC_maxdiff_alltimesteps[i] < ZDC_differences[i])
			ZDC_maxdiff_alltimesteps[i][toUpdate] = ZDC_differences[i][toUpdate]
			ZDC_maxdiff_occurrencetime[i][toUpdate] = int(timestep)
			
			if CZC_data is not None:
				ZDC_CZC_maxdiff_alltimesteps[i][toUpdate] = CZC_data[toUpdate]
			
			if HZT_data is not None:
				ZDC_HZT_maxdiff_alltimesteps[i][toUpdate] = HZT_data[toUpdate]
			
			
			ZDC_alltimesteps[i][gtgl0_data[i]] = (ZDC_alltimesteps[i][gtgl0_data[i]] + ZDC_data[i][gtgl0_data[i]])
			counts_zdc[i][gtgl0_data[i]] += 1
			ZDC_differences_alltimesteps[i][gtgl0_diff[i]] = (ZDC_differences_alltimesteps[i][gtgl0_diff[i]] + ZDC_differences[i][gtgl0_diff[i]])
			counts_zdc_diff[i][gtgl0_diff[i]] += 1
			
		
		# Update TRTC_overall_mask
		if TRTC_data is not None:
			where_cells = np.where(TRTC_mask[0] == False)
			TRTC_alltimesteps[where_cells] = 1
			TRTC_occurrencetime[where_cells] = int(timestep)
		
		# Update BZC maxfield
		if BZC_data is not None:
			toUpdate = np.where(BZC_maxfield < BZC_data)
			max_bzc2update = BZC_data[toUpdate]
			BZC_maxfield[toUpdate] = max_bzc2update
			BZC_occurrencetime[toUpdate] = int(timestep)
		
		# Update MZC maxfield
		if MZC_data is not None:
			toUpdate = np.where(MZC_maxfield < MZC_data)
			max_mzc2update = MZC_data[toUpdate]
			MZC_maxfield[toUpdate] = max_mzc2update
			MZC_occurrencetime[toUpdate] = int(timestep)
		
		if CZC_data is not None:
			toUpdate = np.where(CZC_maxfield < CZC_data)
			max_czc2update = CZC_data[toUpdate]
			CZC_maxfield[toUpdate] = max_czc2update
			CZC_occurrencetime[toUpdate] = int(timestep)
		
		
		
		if HZT_data is not None:
			toUpdate = np.where(HZT_maxfield < HZT_data)
			max_hzt2update = HZT_data[toUpdate]
			HZT_maxfield[toUpdate] = max_hzt2update
			HZT_maxfield_occurrencetime[toUpdate] = timestep
			
			toUpdate = np.where(HZT_minfield > HZT_data)
			min_hzt2update = HZT_data[toUpdate]
			HZT_minfield[toUpdate] = min_hzt2update
			HZT_minfield_occurrencetime[toUpdate] = timestep
		
		
		
		# Write timesteps
		write_row_indiv(file_dirs[5], [timestep])
		
		# DELETE TEMPORARY FOLDER HERE
		#shutil.rmtree(tempdir)
		print("Processes timestep: {}".format(timestep))
		
	
	# delete all folders
	[shutil.rmtree(folder) for folder in folders2delete]
	
	
# remove tempdir
shutil.rmtree(tempdir)

# DIVIDE BY COUNTS HERE
overall_reference = reference_alltimesteps / counts_reference
overall_zdc = [ZDC_alltimesteps[i] / counts_zdc[i] for i in range(len(counts_zdc))]
overall_differences = [ZDC_differences_alltimesteps[i] / counts_zdc_diff[i] for i in range(len(counts_zdc_diff))]
#overall_diffstats = [create_SummaryStats(dat) for dat in overall_differences]
#TBSS_overall = np.array(TBSS_overall) / count_all_timesteps
#TBSS_overall_ref /= count_all_timesteps

# restructuring maxfield
reference_max_alltimesteps = reference_max_alltimesteps.reshape(640*710)
ZDC_max_alltimesteps = [dat.reshape(640*710) for dat in ZDC_max_alltimesteps]

# restructuring ZDC_CZC + ZDC_HZT
reference_CZC_max_alltimesteps = reference_CZC_max_alltimesteps.reshape(640*710)
reference_HZT_max_alltimesteps = reference_HZT_max_alltimesteps.reshape(640*710)
ZDC_CZC_max_alltimesteps = [dat.reshape(640*710) for dat in ZDC_CZC_max_alltimesteps]
ZDC_HZT_max_alltimesteps = [dat.reshape(640*710) for dat in ZDC_HZT_max_alltimesteps]

ZDC_CZC_maxdiff_alltimesteps = [dat.reshape(640*710) for dat in ZDC_CZC_maxdiff_alltimesteps]
ZDC_HZT_maxdiff_alltimesteps = [dat.reshape(640*710) for dat in ZDC_HZT_maxdiff_alltimesteps]

# write ZDC_CZC_HZT MAX combinations
combined_ZDCCZC_max = np.array([reference_CZC_max_alltimesteps] + ZDC_CZC_max_alltimesteps)
combined_ZDCHZT_max = np.array([reference_HZT_max_alltimesteps] + ZDC_HZT_max_alltimesteps)

write_rows_fields(file_dirs[8], combined_ZDCCZC_max)
write_rows_fields(file_dirs[9], combined_ZDCHZT_max)

# write ZDC CZC HZT MAXDIFF combinations
combined_ZDCCZC_maxdiff = np.array(ZDC_CZC_maxdiff_alltimesteps)
combined_ZDCHZT_maxdiff = np.array(ZDC_HZT_maxdiff_alltimesteps)

write_rows_fields(file_dirs[10], combined_ZDCCZC_maxdiff)
write_rows_fields(file_dirs[11], combined_ZDCHZT_maxdiff)

# WRITE ALL FILES AND CLOSE THEM
# meandiff fields
overall_differences = [diffs.reshape(640*710) for diffs in overall_differences]
overall_differences = np.array(overall_differences)
write_rows_fields(file_dirs[1], overall_differences)
#[ovfieldmeandiff_writer.writerow(list(overall_differences[:, i])) for i in range(640*710)]

# mean fields (inkl reference)
overall_reference = [np.array(overall_reference).reshape(640*710)]
overall_zdc = [cols.reshape(640*710) for cols in overall_zdc]
combined_meanfields = overall_reference + overall_zdc
combined_meanfields = np.array(combined_meanfields)
write_rows_fields(file_dirs[0], combined_meanfields)
#[ovfieldmean_writer.writerow(list(combined_meanfields[:, i])) for i in range(640*710)]

# max fields
combined_maxfields = [reference_max_alltimesteps] + ZDC_max_alltimesteps
combined_maxfields = np.array(combined_maxfields)
write_rows_fields(file_dirs[2], combined_maxfields)
#[ovfieldmax_writer.writerow(list(combined_maxfields[:, i])) for i in range(640*710)]

# max fields timesteps
reference_max_occurrencetime = reference_max_occurrencetime.reshape(640*710)
ZDC_max_occurrencetime = [dat.reshape(640*710) for dat in ZDC_max_occurrencetime]
combined_maxtimesteps = [reference_max_occurrencetime] + ZDC_max_occurrencetime
combined_maxtimesteps = np.array(combined_maxtimesteps)
write_rows_fields(file_dirs[6], combined_maxtimesteps)

# max diff fields
maxdiff_fields = np.array([maxdiff.reshape(640*710) for maxdiff in ZDC_maxdiff_alltimesteps])
write_rows_fields(file_dirs[3], maxdiff_fields)

# maxdiff timesteps
ZDC_maxdiff_occurrencetime = [dat.reshape(640*710) for dat in ZDC_maxdiff_occurrencetime]
ZDC_maxdiff_occurrencetime = np.array(ZDC_maxdiff_occurrencetime)
write_rows_fields(file_dirs[7], ZDC_maxdiff_occurrencetime)

# save bzc max field
bzc_maxfieldname = os.path.join(sa_dir, "bzc_maxfield.npy")
np.save(bzc_maxfieldname, BZC_maxfield)

bzc_timestepsname = os.path.join(sa_dir, "bzc_timesteps.npy")
np.save(bzc_timestepsname, BZC_occurrencetime)

# save mzc max field
mzc_maxfieldname = os.path.join(sa_dir, "mzc_maxfield.npy")
np.save(mzc_maxfieldname, MZC_maxfield)

mzc_timestepsname = os.path.join(sa_dir, "mzc_timesteps.npy")
np.save(mzc_timestepsname, MZC_occurrencetime)

# save czc max field
czc_maxfieldname = os.path.join(sa_dir, "czc_maxfield.npy")
np.save(czc_maxfieldname, CZC_maxfield)

czc_timestepsname = os.path.join(sa_dir, "czc_timesteps.npy")
np.save(czc_timestepsname, CZC_occurrencetime)

# HZT_files
hzt_maxfieldname = os.path.join(sa_dir, "hzt_maxfield.npy")
np.save(hzt_maxfieldname, HZT_maxfield)
hzt_minfieldname = os.path.join(sa_dir, "hzt_minfield.npy")
np.save(hzt_minfieldname, HZT_minfield)

hzt_maxocc_name = os.path.join(sa_dir, "hzt_maxoccurrence.npy")
np.save(hzt_maxocc_name, HZT_maxfield_occurrencetime)

hzt_minocc_name = os.path.join(sa_dir, "hzt_minoccurrence.npy")
np.save(hzt_minocc_name, HZT_minfield_occurrencetime)

# saving counts
counts_reference = counts_reference.reshape(640*710)
counts_zdc = [dat.reshape(640*710) for dat in counts_zdc]
combined_counts = [counts_reference] + counts_zdc
combined_counts = np.array(combined_counts)
write_rows_fields(file_dirs[4], combined_counts)
#[counts_writer.writerow(list(combined_counts[:,i])) for i in range(640*710)]

# save overall TRTC_cells
cells_overall_name = "overall_trtc_cells.npy"
cells_overall_name = os.path.join(sa_dir, cells_overall_name)
np.save(cells_overall_name, TRTC_alltimesteps)

cells_timestepsname = os.path.join(sa_dir, "cells_timesteps.npy")
np.save(cells_timestepsname, TRTC_occurrencetime)

print("Processing finished!")
# ----------------------------------------------------------------
