#!/usr/bin/bash

# Script allows different options for output-postprocessing of the ZDR-column detection algorithm
# and is an auxiliary script depending on daily_PARALLEL.sh
# Verbose output could be piped in R-Script transforming it to a CSV-file
# The generated CSV-file may be further processed in the Filtering.py script for maximum filtering or moving-average purposes
#
#
# Script written by Christoph von Matt

time=$1
#time_file=$yrday$hour$minute
time_file="$(echo $time | head -c 9)"
echo $time
echo $time_file
export time

# ZDR-Column Calculation
echo "Starting ZDR Calculation"

cd $HOME

if [ $verbose -eq 0 ]
then
 bash $HOME/ZDRCOL.sh
fi
#bash ./ZDRCOL.sh | grep "DBG:" > $datadir"/"$time".txt"
if [ $verbose -eq 1 ]
then
 bash ./ZDRCOL.sh | grep "DBG:" | Rscript DBG_to_CSV.R $datadir $time_file
fi

cd $datadir/ZDC

mv ZDC*.801 ./$threshold_dir

cd $datadir



# Zipping generated CSV-file
if [ $verbose -eq 1 ]
then
 zip filtering_files.zip $time_file".csv"
 rm $datadir"/"$time_file.csv
fi