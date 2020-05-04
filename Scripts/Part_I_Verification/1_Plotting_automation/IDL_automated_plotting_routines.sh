#!/usr/local/bin/tcsh
echo "TO load IDL module: module load idl"

# This Script is an automated plotting routine to modificated MCH-IDL-Plotting functions
# Required specifications:
#	- IDL-file: (string) Selection of the plotting routine (e.g. POIs or RHIs or Statistics)
#	- year
#	- day: doy (day-of-year)
#	- outfolder: specification whether outfolder already exists
#	- products: product selection
#	- trt_dir: directory of thunderstorm tracking files
#	- moment: which moment to plot
#	- specifications for POI-plots (see corresponding section)
#	- specifications for RHI-plots (see corresponding section)
#
# Written by Christoph von Matt

# IDL settings
# IDL_NO_XWINDOWS=1 required for automation
export IDL_DIR="idl_directory"
export IDL_STARTUP=$IDL_DIR/"setup_file.idl"
export IDL_NO_XWINDOWS=1
# load IDL-module
module load idl

#-----------------------------------------------------------------------------
#
#			USER SPECIFICATION SECTION
#
#-----------------------------------------------------------------------------
################################# GENERAL ATTRIBUTES #############################
# CHOOSE TASK________________________________________________________________
# currently: poi_plot, rhi_plot, ZDR_stats (histograms), poi_plotmodified, rhi_cross

IDL_file="poi_plotmodified"

year=2017
day=${year:(-2)}214

# REQUIRED FOLDERS ALREADY ESTABLISHED?
# Variable denotes if there is already a Outputfolder existing for specific
# Case Study (Day) in the specific section
# Naming of folder = "output"
# Exists = 0
outfolder=0

# CHOOSE PRODUCT
products="MLA MLD MLL MLP MLW HZT NHC BZC MZC LZC EZC OZC YMA YMD YML YMP YMW ZDC"
products="CZC"

###################### FOR LOOP 1 START #########################################
for prod in ${products}
do

#SPECIFY PATHS________________________________________________________________
DATADIR="path_to_data_home/"$year"/"$day"/"$prod"/"
OUTDIR="path_to_data_home/"$year"/"$day

echo $DATADIR
echo $OUTDIR


# Please give here the directory of the TRT-folder
trt_dir=$OUTDIR"/TRTC/"
#trt_dir="none"


# DEFINE PLOT SPECIFIC VARIABLES_____________________________________________
# possible values: ZH, ZV, Z, ZDR, KDP, PHI, RHO --"NONE" for ZDC
moments="RHO"

###################### FOR LOOP 2 START #########################################
for moment in ${moments}
do

################################# POI_PLOT ATTRIBUTES #############################
# Specification of POI-plot extents
#Default values: chyrange: 255,965 // chxrange: -160, 480
#CH_def: chyrange: 400,900 // chxrange: 0,360

chyrange1=700
chyrange2=800
chxrange1=200
chxrange2=300

################################# RHI ATTRIBUTES #################################
# Specifications of azimuths to be considered
#default=118
azimuth_start=118
azimuth_end=118

# Specification of range to be plotted
#	- start, end: horizontal
#	- min_h, max_h: vertical heights
#range specification [km] (x-axis)
start=0
end=120
#height specification [km] (y-axis)
min_h=0
max_h=15


################################# ATTRIBUTES INFLUENCING BOTH #################################
#ALTERNATIVELY: PREDEFINED CROSS SECTIONS
# For Plotting routines with combined cross-sections and POI outputs
# Locations information is required to represent cross section with a line on POI-plots
# Location specified = 1 (true) - only necessary for POIs
# Location = 1 will make a location square out of the given coordinates (poi_plotmodified)
# Location = 0 is used if cross sections should be drawn (poi_cross)
location=0
chy1=0
chy2=0
chx1=0
chx2=0

#Will make a lateral cross-translation of "howmany"-steps to the eastern (e.g. 50 results in 50 RHI cross sections starting from given coordinates and translating +0.5km in each step)
#default = 1
howmany=1

#Specify zero degree height (for rhi_cross) (in km)
# Will be drawn as horizontal line on RHI-plots
heightzero=4.25

#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
#
#		DO NOT CHANGE ANYTHING BELOW! EXECUTION SECTION!
#
#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
#current location of this bash-file
current=`pwd`
#echo $current

#Get Product Type
#prd="ZDC"
prd=${DATADIR:(-4)}
prd=${prd:0:3}
echo $prd

#---------------------------FOLDER CREATION________________________________________
# Check whether folder has to be created first
if [ $outfolder == 0 ]
then
 mkdir $OUTDIR"/output"
fi
OUTDIR=$OUTDIR"/output"

# if histograms: create separate folder in output-folder
# naming = "histograms"
if [ $IDL_file == "ZDR_stats" ]
then
 mkdir $OUTDIR"/histograms"
 OUTDIR=$OUTDIR"/histograms"
fi


#--------------------EXECUTION OF Plotting-TASK-FILES-----------------------------------------
# Execution of Task
if [ $IDL_file == "ZDR_stats" ] || [ $IDL_file == "poi_plot" ] || [ $IDL_file == "poi_plotmodified" ]
then
 idl $IDL_file -args $DATADIR $OUTDIR $moment $chyrange1 $chyrange2 $chxrange1 $chxrange2 $trt_dir $chy1 $chy2 $chx1 $chx2 $prd $howmany
fi
if [ $IDL_file == "rhi_plot" ]
then
 idl $IDL_file -args $DATADIR $OUTDIR $moment $azimuth_start $azimuth_end $start $end $min_h $max_h $howmany
fi
if [ $IDL_file == "rhi_cross" ]
then
 if [ $prd != "ZDC" ] || [ $prd != "HZT" ] || [ $prd != "OZC" ]
 then
 echo "do"
  #corridl $IDL_file -args $DATADIR $OUTDIR $moment $chy1 $chx1 $chy2 $chx2 $min_h $max_h $howmany $prd $heightzero
  #idl $IDL_file -args $DATADIR $OUTDIR $moment $chy2 $chx2 $chy1 $chx1 $min_h $max_h $howmany $prd $heightzero
 fi
 idl "poi_cross" -args $DATADIR $OUTDIR $moment $chyrange1 $chyrange2 $chxrange1 $chxrange2 $trt_dir $chy1 $chy2 $chx1 $chx2 $prd $howmany $location
 #idl "all_cross" -args $DATADIR $OUTDIR $moment $chyrange1 $chyrange2 $chxrange1 $chxrange2 $trt_dir $chy1 $chy2 $chx1 $chx2 $prd $howmany
fi
#------------------------------------------------------------------------------------
# 		Post-Plot-generation clean up: MOVING FILES INTO RIGHT DIRECTORY
#------------------------------------------------------------------------------------
# if necessary move plots to right directory
if [ $IDL_file != "ZDR_stats" ]
then
 mkdir $OUTDIR"/"$prd"_plots"
 OUTDIR=$OUTDIR"/"$prd"_plots"
 cd $DATADIR
 mv plot_${prd}*.png $OUTDIR #${} without brackets?
fi

###################### FOR LOOP 2 END #########################################
done

###################### FOR LOOP 1 END #########################################
done

