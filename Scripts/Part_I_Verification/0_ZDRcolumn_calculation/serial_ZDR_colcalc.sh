#!/bin/bash

# This Script is for the automated serial ZDR-column calculation using
#	the ZDR-column detection algorithm written by M.Boscacci (ZDRCOL.sh)
#
#	Required specifications:
#		- Path to data home directory (folder structure according to MCH)
#		- Dates: Year + DOY (day of year)
#
# Written by Christoph von Matt

#Specify Year and Day
year=2017
day=${year:(-2)}211

#Specify and Export different paths
indir="path_to_data_home"/$year/$day
export indir
datadir=$indir/MLA
#echo $datadir
hztdir=$indir/HZT
#echo $hztdir
export hztdir
outdir=$indir
export outdir
echo $outdir

# GET ALL FILES IN DIRECTORY
filenames=`ls ${datadir}`
#echo $filenames


echo "Processing filenames"
# create substrings for time input in other scripts

times=()

for filename in ${filenames}
 do
 sub=${filename:3:11}
 #echo $sub
 times+=($sub)
done
#echo "Resulting strings:"
#echo ${times[@]}
echo "Processing done"

# Create unique time values
echo "Sorting out doubles:"
sorted=($(echo ${times[@]} | tr ' ' '\n' | sort -u | tr '\n' ' '))
echo ${sorted[@]}
echo "Process finished"


# ZDR COLUMN CALCULATION
# BE AWARE: DATADIR + OUTDIR defined in ZDRCOLC.sh
echo "Starting ZDR Calculation"
for time in ${sorted1[@]}
 do
 echo "time: $time"
 export time
 bash ./ZDRCOL.sh
done
echo "ZDR COLUMN Calculation finished"
