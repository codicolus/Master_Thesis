#!/usr/bin/bash

# This Script is for data fetching
# Required specifications:
#	- year
#	- day: doy (day-of-year)
#	- utc_start: data will be fetched starting at this timestamp
#	- hzt_time: corresponding nearest COSMO freezing level height output (hourly output, but 3-hourly timestamp changes)
#	- products: products to fetch
#
# Written by Christoph von Matt

datadir="path_to_local_data_storage"
raddir="path_to_data_storage"


# BE VERY CAUTIOUS ON CHOOSING THE CORRECT TIMES AND DAYS!!!!
# HZTs only EVERY 3H PRODUCED (DEPENDING ON UTC_START)
year=2017
day=${year:(-2)}176
utc_start=2000
hzt_time=18
# utc_end=2355

products="MLA MLD MLL MLP MLW HZT TRTC NHC BZC MZC LZC EZC OZC YMA YMD YML YMP YMW"
#products="MLA MLD MLL MLP MLW"
products="MLA"

#----------------------AUTOMATED PART----------------------------------------
## CREATE FOLDERS
mkdir $datadir""$year
mkdir $datadir""$year"/"$day
datadir=$datadir""$year"/"$day
cd $datadir

for prod in ${products}
do
 #echo $prod
 mkdir $prod
done
echo "Folders created"
#
# COPYING AVAILABLE DATA INTO FOLDERS
# note: could be refined by 5min timesteps
# now: always copies 1h of data
#echo `seq $utc_start 5 $utc_end`
#
for prod in ${products}
 do
  cd $datadir"/"$prod
  if [ $prod == "TRTC" ]
  then
   `unzip $raddir/$year/$day/$prod$day.zip CZC$day$utc_start* .`
  elif [ $prod == "HZT" ]
  then
   `unzip $raddir/$year/$day/$prod$day.zip $prod$day$hzt_time* .`
  else
   `unzip $raddir/$year/$day/$prod$day.zip $prod$day$utc_start* .`
  fi
  cd $datadir
done
echo "All available data copied to folders"

