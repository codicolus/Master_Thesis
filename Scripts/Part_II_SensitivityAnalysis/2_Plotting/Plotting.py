#!/store/msrad/utils/anaconda3/bin/python
############# General Information ##############
# Author: Christoph von Matt
# Created: 13.06.2019
# Purpose:  This script is for plotting individual surface plots of MCH-products
#
#
################################################
# load needed libraries
import os
import sys
import inspect
import fnmatch
import pyrad
import pyart
from pyproj import Proj, transform
from affine import Affine
# Append necessary paths for reading diverse metranet-files
sys.path.append("path_to_metranet_lib")
import metranet

# AUXILIARY FUNCTIONS FOR DATA READING
------------------------------------------
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
	#outProj = Proj(init="epsg:21781")
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
		lons, lats = transform_2_CH1903(lon, lat)
	else:
		lons = lon
		lats = lat
	
	coords = list(zip(lons, lats))
	
	return geometry.Polygon(coords)


# Function to create a Multipolygon out of all available TRT-cells within TRT-File
# Coordinates may be reprojected to Swiss Coordinates if necessary
def TRT_Multi_Polygon(TRT_cell_coordinates, convertWGS84ToCH1903):
	"""This function creates a MultiPolygon from all TRT-cells"""
	
	poly_list = [makeTRTPolygon(TRT_cell_coordinates[i]["lon"], TRT_cell_coordinates[i]["lat"], convertWGS84ToCH1903) for i in range(len(TRT_cell_coordinates))]
	
	return geometry.MultiPolygon(poly_list)



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




# PLOTTING RELATED AUXILIARY FUNCTIONS ------------------------------------------------------------------
# generate title
def get_date_product_string(date, product):
	return product + " " + str(date)[:-3] + " UTC"

import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.ticker as mticker
import rasterio
import rasterio.plot
import cartopy; print('cartopy', cartopy.__version__)
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

from mpl_toolkits.axes_grid1 import AxesGrid
from cartopy.mpl.geoaxes import GeoAxes
from mpl_toolkits.axes_grid1 import AxesGrid

# Data-Handling
import numpy as np
import pandas as pd
import os
import sys
import fnmatch
import scipy.ndimage
import datetime
import ntpath

# Polygons
import fiona
from shapely.geometry import shape, mapping, Polygon
from shapely import geometry
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch

# CARTOPY SETTINGS
# load image tiles
import cartopy.feature as cfeat

# set background projection
plot_crs = ccrs.Mercator()
resolution = "10m"
# features
# countries
countries = cartopy.feature.NaturalEarthFeature(
	category='cultural',
	name='admin_0_countries',
	scale=resolution,
	facecolor='none')

lakes_europe = cartopy.feature.NaturalEarthFeature(
	category='physical',
	name='lakes_europe',
	scale=resolution)

rivers_europe = cartopy.feature.NaturalEarthFeature(
	category='physical',
	name='rivers_europe',
	scale=resolution)



# BEGIN DATA ##############################################################################

# SECTION BACKGROUND DATA LOADING + PLOT NAME SPECIFICATIONS
# combination names
zh_threshs = np.array(["0", "25", "30", "35", "40", "45"])
zdr_threshs = np.array(["1.0", "0.95", "0.9", "0.85", "0.8", "0.74"])
comb_names = ["ZDC_thresh_{}_{}".format(zh, zdr) for zh in zh_threshs for zdr in zdr_threshs]

#--------------------------------------------------------------------------------------------------------------------------
# COLORMAP SPECIFICATIONS NEW -------------- FINAL
# TODO: COLORBARS ARE CHANGED HERE FOR ALL PRODUCTS
# ZDC
zdc_bounds = np.linspace(500,4500, int((4500-500)/500)+1)
# COLORBAR
cmap_r_zdc = plt.get_cmap("plasma", len(zdc_bounds)+1) #plasma
colors_zdc = list(cmap_r_zdc(np.arange(len(zdc_bounds)+1)))
cmap_r_zdc = mpl.colors.ListedColormap(colors_zdc[:-1], "")
# set over-color to last color of list
zdc_norm = mpl.colors.BoundaryNorm(zdc_bounds, cmap_r_zdc.N)
cmap_r_zdc.set_over(colors_zdc[-1])

#-------------------------------------------------------------
# COLORBAR SPECIFICATIONS FOR EVERY PRODUCT USED -------------------
# BZC
bzc_bounds = np.linspace(40,100, (100-40)/10+1)
cmap_bzc = plt.get_cmap("plasma", len(zdc_bounds)+1) #gnuplot_r # viridis
colors_bzc = list(cmap_bzc(np.arange(len(bzc_bounds)+1)))
cmap_bzc = mpl.colors.ListedColormap(colors_bzc[1:])
bzc_norm = mpl.colors.BoundaryNorm(bzc_bounds, cmap_bzc.N)
cmap_bzc.set_over(colors_bzc[-1])
cmap_bzc.set_under(colors_bzc[0])

# MZC
mzc_bounds = np.linspace(2, 10, 4+1)
cmap_mzc = plt.get_cmap("plasma", len(mzc_bounds)+1)
colors_mzc = list(cmap_mzc(np.arange(len(mzc_bounds)+1)))
cmap_mzc = mpl.colors.ListedColormap(colors_mzc[:-1])
mzc_norm = mpl.colors.BoundaryNorm(mzc_bounds, cmap_mzc.N)
cmap_mzc.set_over(colors_mzc[-1])

# HZT
hzt_bounds = np.linspace(0,7000, int(7000/500)+1)
hzt_norm = mpl.colors.BoundaryNorm(hzt_bounds, cmap_r.N)
# CZC
#czc_bounds = np.append(np.array([0,7]), np.linspace(13,61, (61-13)+1)[::3])
czc_bounds = np.linspace(15,55, (55-15)/5+1)
cmap_czc = plt.get_cmap("viridis", len(czc_bounds)+1)
colors_czc = list(cmap_czc(np.arange(len(czc_bounds)+1)))
cmap_czc = mpl.colors.ListedColormap(colors_czc[:-1])
czc_norm = mpl.colors.BoundaryNorm(czc_bounds, cmap_czc.N)
cmap_czc.set_over(colors_czc[-1])

#--------------------------------------------------------------------------------------------------------------------------


# Specification for LAT-LON values
x, y = np.meshgrid(np.linspace(0,710000, 710+1)[:-1]+255000, np.linspace(0,640000, 640+1)[:-1]-160000)

x_cont, y_cont = np.meshgrid(np.linspace(0, 710000, 3550+1)[:-1]+255000, np.linspace(0, 640000, 3200+1)[:-1]-160000)

# RADAR SPECIFICATIONS
radar_loc_proj = "lv03"
radar_names = ["Albis", "La Dôle", "Monte Lema", "Plaine-Morte", "Weissfluhgipfel"]
Albis = {"swiss": [681.201, 237.604], "wgs84": [47.284333, 8.511900], "lv03": [681201, 237604]}
Dole = {"swiss": [497.057, 142.408], "wgs84": [46.425113, 6.099415], "lv03":[497057, 142408]}
Lema = {"swiss": [707.957, 99.762], "wgs84": [46.040761, 8.833217], "lv03":[707957, 99762]}
PlMorte = {"swiss": [603.687, 135.476], "wgs84": [46.370646, 7.486552], "lv03":[603687, 135476]}
Weissfluh = {"swiss": [779.70, 189.79], "wgs84": [46.834974, 9.794458], "lv03":[779700, 189790]}

radars = [Albis[radar_loc_proj], Dole[radar_loc_proj], Lema[radar_loc_proj],
          PlMorte[radar_loc_proj], Weissfluh[radar_loc_proj]]

radar_points = [geometry.Point(r) for r in radars]
radar_points = geometry.MultiPoint(radar_points)
radar_extent160km = [p.buffer(160*1000) for p in radar_points]

# example tiff
tiff_example = "../example.tiff"
tiff_example = rasterio.open(tiff_example)
import rasterio.mask
radar_mask = rasterio.mask.raster_geometry_mask(tiff_example, radar_extent160km)
radar_flipped = np.flipud(radar_mask[0] == False).astype(float)

# ------------------------------------------
## ACTUAL BEGIN OF DATA - LOADING + PLOTTING
# ------------------------------------------

contours=True
zdc_conts=False

# DATA-PATH SPECIFICATION
# maxfields
year = "2018"
day = "18150"
name = "zoom"
# ANALYSES FOR: ZH=0,25, 30, 35, 40
# ZDR = 1.0, 0.85

zh_thresh = list([40])
zdr_thresh = list([1.0])
datatype="ZDC"

isZDC=False
if datatype == "ZDC":
	isZDC = True

if day == "17176":
	start_time = "171760210" # 15 0000
	end_time = "171760225" # 18 0400

if day == "17211":
	start_time = "172111500" # 1500
	end_time = "172111900" # 1900

if day == "17213":
	start_time = "172132200"
	end_time = "172132355" #2355

if day == "17214":
	start_time = "172140000"
	end_time = "172140200" #0200

if day == "18150":
	start_time = "181501750" #1500
	end_time = "181501815" #1800

if day == "18185":
	start_time = "181850900"
	end_time = "181851300" #1300


# set extents for case study days
# for 17214
if day == "17214":
	extent = [7.5, 9, 47.4, 48.6]
	# for 17214 (case Rafz)
	extent = [7, 9.5, 46.8, 48]
	# for 17214 (high_cols germany)
	#extent = [8.5, 9.5, 47.4, 48.3]

# for 17176
if day == "17176":
	extent = [8.75, 10, 45.6, 46.2]
	extent = [7.8, 10, 45.6, 46.8] #before
	extent = [8.4, 9.3, 45.75, 46.2] # Associations
	extent = [9, 9.9, 46, 46.5] #TRT-evolution

# for 17211
if day == "17211":
	extent = [6, 9, 46.8, 48]


if day == "17213":
	# for 17213 (case Marbach)
	#extent = [6.5, 8.5, 46.2, 47.4]
	extent = [6.6,9, 46.8, 48]

# for 18150
if day == "18150":
	#extent = [7, 9, 46.5, 48]
	extent = [7,10, 46.8, 48]
	extent = [8.4, 9.4, 47.3, 47.7]

# for 18185
if day == "18185":
	extent=[8,10, 46.8, 48]

if name in ["swiss", "swiss_nan600"]:
	extent = [5.5, 11, 45, 48.5]

# Specification of paths (MCH-folder structure, one level higher than "years")
trtc_path = "path_to_data" + year + "/" + day + "/TRTC"
bzc_path = "path_to_data" + year + "/" + day + "/BZC"
mzc_path = "path_to_data" + year + "/" + day + "/MZC"
outdir = "path_to_data" + year + "/" + day + "/Plots"
# TRTC_files
trtc_files = os.listdir(trtc_path)
trtc_files = fnmatch.filter(trtc_files, "*.trt")
bzc_files = os.listdir(bzc_path)
mzc_files = os.listdir(mzc_path)

for zh in zh_thresh:
	for zdr in zdr_thresh:
		
		outdir = "path_to_data" + year + "/" + day + "/Plots"
		
		if datatype == "ZDC":
			datapath = "path_to_data"+ year + "/" + day + "/ZDC/ZDC_thresh_{}_{}".format(zh, zdr)
		elif datatype == "CZC":
			datapath = "path_to_data" + year + "/" + day + "/CZC"
		elif datatype == "BZC":
			datapath = "path_to_data" + year + "/" + day + "/BZC"
		else:
			datapath = "path_to_data" + year + "/" + day + "/MZC"
		
		folder = ntpath.basename(datapath)
		
		
		# ZDC path (for countours)
		if datatype != "ZDC":
			ZDC_path = "path_to_data"+ year + "/" + day + "/ZDC/ZDC_thresh_{}_{}".format(zh, zdr)
		
		
		
		
		if not os.path.exists(outdir):
			os.makedirs(outdir)
		
		if folder:
			if not os.path.exists(os.path.join(outdir, folder)):
				outdir = os.path.join(outdir, folder)
				os.makedirs(outdir)
			else:
				outdir = os.path.join(outdir, folder)
		
		
		# ---- FILES + FILEPATHES ----
		datafiles = os.listdir(datapath)
		
		if datatype != "ZDC":
			ZDC_files = os.listdir(ZDC_path)
			ZDC_filepathes = [os.path.join(ZDC_path, f) for f in ZDC_files]
		
		
		datafilepathes = [os.path.join(datapath, f) for f in datafiles]
		trtc_filepathes = [os.path.join(trtc_path, f) for f in trtc_files]
		
		alltimesteps = [TRT_file[-15:-6] for TRT_file in trtc_files]
		alldatetimes = convert_to_datetimes(alltimesteps)
		
		# plt-nr (set to None if not numbered)
		nr = None
		
		index_start = alltimesteps.index(start_time)
		index_end = alltimesteps.index(end_time)
		
		alltimesteps = alltimesteps[index_start: index_end+1]
		alldatetimes = alldatetimes[index_start: index_end+1]
		trtc_filepathes = trtc_filepathes[index_start: index_end+1]
		
		
		
		for i in range(len(alltimesteps)):
			which_ts = i
			timestep = alltimesteps[which_ts]
			date = alldatetimes[which_ts]
			
			mzc_found = True
			bzc_found = True
			
			datafile = fnmatch.filter(datafilepathes, "*" + timestep + "*")[0]
			try:
				bzc_file = fnmatch.filter(bzc_files, "*" + timestep + "*")[0]
			except IndexError:
				bzc_found = False
				pass
			
			try:
				mzc_file = fnmatch.filter(mzc_files, "*" + timestep + "*")[0]
			except IndexError:
				mzc_found = False
				pass
			
			# read and smooth data for plotting
			# ToDo: alternatively use gaussian filter
			if bzc_found:
				bzc_data = read_convert_METRANET(os.path.join(bzc_path, bzc_file), ZDC=False)
				bzc_data[np.where(np.isnan(bzc_data))] = 0.
				bzc_data = np.flipud(bzc_data)
				smoothed_bzc = scipy.ndimage.zoom(bzc_data, 5)
			
			if mzc_found:
				mzc_data = read_convert_METRANET(os.path.join(mzc_path, mzc_file), ZDC=False)
				mzc_data[np.where(np.isnan(mzc_data))] = 0.
				mzc_data = np.flipud(mzc_data)
				smoothed_mzc = scipy.ndimage.zoom(mzc_data, 5)
			
			
			
			# read ZDC
			data = read_convert_METRANET(datafile, ZDC=isZDC)
			
			if datatype == "ZDC":
				data[np.where(data < 1000.)] = np.nan  # CHANGE HEIGHT THRESHOLD HERE
			
			if datatype == "CZC":
				data[np.where(data <= 0.)] = np.nan
			
			if datatype == "BZC":
				data[np.where(data < 80.)] = np.nan
			
			if datatype == "MZC":
				data[np.where(data < 2.)] = np.nan
			
			data_flipped = np.flipud(data)
			
			# trt-files
			trtc_data = pyrad.io.read_trt_data(trtc_filepathes[which_ts])[27]
			trtc_poly = TRT_Multi_Polygon(trtc_data, convertWGS84ToCH1903=True)
			
			
			outfile = os.path.join(outdir, datatype + timestep + name + ".png")
			
			
			# BEGIN OF CARTOPY-PLOTTING
			fig = plt.figure(figsize=(12, 10))
			ax = plt.axes(projection=plot_crs)
			#ax.set_global()
			#ax.coastlines()
			#ax.set_extent([2.5,12.5, 43, 50.5])
			#ax.set_extent([4.5, 12.5, 45, 50])
			
			# plotting features
			ax.add_feature(countries, edgecolor='black')
			ax.add_feature(lakes_europe, edgecolor='blue', facecolor='blue', alpha=0.25)
			ax.add_feature(rivers_europe, edgecolor='blue', facecolor='none')
			#ax.add_feature(urban_areas, edgecolor='brown', facecolor='brown', alpha=0.25)
			
			# Plotting TRT-cells
			if datatype == "CZC":
				ax.add_geometries(trtc_poly, crs=ccrs.epsg(21781), facecolor="None", edgecolor="#40ff00", lw=2) #ff0000
			else:
				ax.add_geometries(trtc_poly, crs=ccrs.epsg(21781), facecolor="None", edgecolor="#40ff00", lw=2) #3df808
				#ax.add_geometries(trtc_poly, facecolor="None", edgecolor="#e50000")
			#ax.add_geometries(trt_shp["geometry"], crs=ccrs.epsg(21781), facecolor="None", edgecolor="#e50000")
			
			# Plotting products
			if datatype == "CZC":
				img = ax.pcolormesh(x,y, data_flipped, transform=ccrs.epsg(21781), cmap=cmap_czc, norm=czc_norm)
			elif datatype == "ZDC":
				img = ax.pcolormesh(x,y, data_flipped, transform=ccrs.epsg(21781), cmap=cmap_r_zdc, norm=zdc_norm)
			elif datatype == "BZC":
				img = ax.pcolormesh(x,y, data_flipped, transform=ccrs.epsg(21781), cmap=cmap_bzc, norm=bzc_norm)
			elif datatype == "MZC":
				img = ax.pcolormesh(x,y, data_flipped, transform=ccrs.epsg(21781), cmap=cmap_mzc, norm=mzc_norm)
			
			#if name not in ["swiss", "swiss_nan600"]:
			ax.set_extent(extent)
			
			
			# SMOOTHED CONTOURS NEEEDED
			if contours:
				# add contours to plot (maybe other solution - See PYRAD!!!)
				ax.contour(x, y, radar_flipped, levels=[1.], colors=["green"], transform=ccrs.epsg(21781))
				
				if (datatype != "ZDC")&zdc_conts:
					ax.contour(x_cont, y_cont, smoothed_zdc, levels=[1000., 2000.], colors=["deeppink", "red"], transform=ccrs.epsg(21781))
				
				
				#if bzc_found:
				#	ax.contour(x_cont, y_cont, smoothed_bzc, levels=[80.], colors=["blue"], transform=ccrs.epsg(21781))
				#if mzc_found:
				#	ax.contour(x_cont, y_cont, smoothed_mzc, levels=[2.], colors=["green"], transform=ccrs.epsg(21781))
				
			
			# GRID LINES
			gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=1, color='gray', alpha=0.5, linestyle="--")
			gl.xlabels_top = False
			gl.ylabels_left = True
			gl.ylabels_right = False
			gl.xlines = True
			#gl.xlocator = mticker.FixedLocator(list(np.linspace(extent[0], extent[1], int((extent[1]-extent[0])/2)+1))) # 2.5, 12.5 before
			gl.xformatter = LONGITUDE_FORMATTER
			gl.yformatter = LATITUDE_FORMATTER
			gl.ylabel_style = {'size': 12}
			gl.xlabel_style = {'size':12}
			
			if day == "17176":
				shrink = 0.7
				padtit = 10
				padcbtit = 15
				sizetit = 20
				sizecb = 12
				padcb = 0.08
			elif day == "17211":
				shrink = 0.55
				padcb = 0.06
			elif day == "17213":
				shrink = 0.7
				padcb = 0.08
			elif day == "17214":
				shrink = 0.65
				padcb = 0.08
			elif day == "18150":
				shrink = 0.55
				padcb = 0.07
			elif day == "18185":
				shrink = 0.8
				padcb = 0.08
			else:
				shrink = 0.85
			
			# Other Plot specification
			if datatype == "ZDC":
				ax.set_title(get_date_product_string(date, "Z$_{DR}$ column height"), size=20, pad=10)
				cb = plt.colorbar(img, pad=padcb, shrink=shrink, ticks=[0,500,1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500], extend="max")
				cb.ax.set_title("Height (m)", fontweight="bold", pad=15, size=13)
				cb.ax.tick_params(labelsize=12)
			elif datatype == "CZC":
				ax.set_title(get_date_product_string(date, "MAXECHO"), size=20, pad=10)
				cb = plt.colorbar(img, pad=padcb, shrink=shrink, extend="max")
				cb.ax.set_title("dBZ", fontweight="bold", pad=15, size=13)
				cb.ax.tick_params(labelsize=12)
			elif datatype == "BZC":
				ax.set_title(get_date_product_string(date, "POH"), size=20, pad=10)
				cb = plt.colorbar(img, pad=padcb, shrink=shrink, extend="both")
				cb.ax.set_title("POH %", fontweight="bold", pad=15, size=13)
				cb.ax.tick_params(labelsize=12)
			elif datatype == "MZC":
				ax.set_title(get_date_product_string(date, "MESHS"), size=20, pad=10)
				cb = plt.colorbar(img, pad=padcb, shrink=shrink, extend="max")
				cb.ax.set_title("Size (cm)", fontweight="bold", pad=15, size=13)
				cb.ax.tick_params(labelsize=12)
			
			#plt.colorbar(img, pad=0.1, shrink=0.85, ticks=np.linspace(0,6000, 6+1))
			
			fig.savefig(outfile)
			plt.close(fig)



