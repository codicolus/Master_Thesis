#!/usr/bin/bash

# This script is for the ZDR-Column calculation as serial process!
# It consists of following 2 parts:
#	0) Auxiliary Functions
# 	1) ZDR-Columns Processing
#
# NOTE: This script calculates ZDR-Columns in hourly bundles!
#
# Script written by Christoph von Matt 

################################################################################################
#											       #
#		Part 0 - Auxiliary Functions						       #
#											       #
#											       #
#											       #
################################################################################################

# Checking if the given year is a leap year
is_leap () {
 if [ $(($1%4)) != 0 ]
 then
  echo 0
 elif [ $(($1%100)) != 0 ]
 then
  echo 1
 elif [ $(($1%400)) == 0 ]
 then
  echo 1
 else
  echo 0
 fi
}

################################################################################################
#											       											   #
#		Part 1 - ZDR-Column Processing						       							   #
#											       											   #
#		Products used: ML*, HZT 															   #
#		Products stored additionally: TRTC, CZC					       						   #
#											       											   #
################################################################################################

# Path specifications
rootdir=$1
raddir="path_to_radar_data"
export rootdir
export raddir

verbose=$3
zh_threshold=$4
parallel=$5
zdr_threshold=$6
export verbose
export zh_threshold
export parallel
export zdr_threshold
# Products specifictaion
products="MLA MLD MLL MLP MLW HZT TRTC CZC"
export products

# BE VERY CAUTIOUS ON CHOOSING THE CORRECT TIMES AND DAYS!!!!
# Specify years
years="2017 2018 2019"

# Vector that will contain every yearday of specified years
alldays=""

# Creating a vector of all days of given years (leap year adjusted)
for year in $years
do
 # Specify sequence for days: e.g. 001-365
 days="$(seq -f '%03g' 1 365)"
 
 # leap year check
 leap=$(is_leap $year)
 
 #adjusting for leap years
 if [ $leap == 1 ]
 then
  days="$days 366"
 fi
 
 for day in $days
 do
  yd=${year:(-2)}$day
  alldays=$alldays$yd" "
 done
 #echo $alldays
done

alldays=$2

#loop days----------------------------------------------------------------------------------
for yrday in $alldays
do
 export yrday
 # Execute parallelized ZDR-column calculation
 bash $HOME/daily_PARALLEL.sh
#end day loop----------------------------------------------------------------------------------
done
