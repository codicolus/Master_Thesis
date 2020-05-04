#!/usr/bin/bash
# This is a helper-script for the ZDR_DAILY_REFACTORED.sh file
# All tasks which are beyond daily-level are stored in this script to allow a certain degree of parallelization
#
# Script written by Christoph von Matt

################################################################################################
#											       #
#		Part 0 - Auxiliary Functions						       #
#											       #
#											       #
#											       #
################################################################################################
#function to get corresponding hzt_time
get_hzt () {
 if [ $1 -lt 03 ]
 then
  echo 0000
 elif [ $1 -lt 06 ]
 then
  echo 0300
 elif [ $1 -lt 09 ]
 then
  echo 0600
 elif [ $1 -lt 12 ]
 then
  echo 0900
 elif [ $1 -lt 15 ]
 then
  echo 1200
 elif [ $1 -lt 18 ]
 then
  echo 1500
 elif [ $1 -lt 21 ]
 then
  echo 1800
 else
  echo 2100
 fi
}
 
# Create Day-ID for data downloads
# deducing year + day variables
year="$(echo $yrday | head -c 2)"
year="20"$year
day=${yrday:(-3)}

echo $year" "$day
## CREATE FOLDERS FOR EVERY PRODUCT ////////////
mkdir $rootdir"/"$year
mkdir $rootdir"/"$year"/"$yrday

# Specify Data-Directory (within root-directory)
datadir=$rootdir"/"$year"/"$yrday
export datadir

#specify hours
hours="$(seq -f '%02g' 0 23)"
#hours="23"
#loop hours-------------------------------------------------------------------------------
for hour in $hours
do
 echo $hour
 hzt_time="$(get_hzt $hour)"
 
 utc_start=${hour}
 
 ############################# TASK 1.1 - COPY NECESSARY FILES #############################
 
 # Changing Directory
 cd $datadir
 
 # Create ZIP-File for storage of Filtering Output
 if [ $verbose -eq 1 ]
 then
  touch test.txt
  zip filtering_files.zip test.txt
  zip -d filtering_files.zip test.txt
  rm test.txt
 fi
 
 # folder for converted polar 2 cartesian for TBSS analysis (deprecated)
 mkdir "TBSS"
 mkdir "ZDC"
 
 # folder for specific threshold
 threshold_dir="ZDC_thresh_"$zh_threshold"_"$zdr_threshold
 export threshold_dir
 
 mkdir "ZDC/"$threshold_dir
 
 for prod in $products
 do
  mkdir $prod
 done
 echo "Folders created!"
 
 ## COPYING AVAILABLE DATA INTO FOLDERS /////////////
 for prod in $products
 do
  cd $datadir"/"$prod
  if [ $prod == "TRTC" ]
  then
   `unzip $raddir/$year/$yrday/$prod$yrday.zip CZC$yrday$utc_start* .`
  elif [ $prod == "HZT" ]
  then
   `unzip $raddir/$year/$yrday/$prod$yrday.zip $prod$yrday$hzt_time* .`
  else
   `unzip $raddir/$year/$yrday/$prod$yrday.zip $prod$yrday$utc_start* .`
  fi
  cd $datadir
 done
 echo "All available data copied to folders!"
 
 ######################### TASK 1.2 - ZDR-COLUMN CALCULATION #################################
 
 # Specify and export different paths
 echo $datadir
 indir=$datadir
 export indir
 outdir=$datadir
 export outdir
 hztdir=$datadir/HZT
 export hztdir
 tbss_dir=$datadir/TBSS
 export tbss_dir
  
 # Specify sequence for 5-minute steps: e.g. 00-55
 minutes="$(seq -f '%02g' 0 5 55)"
 
 echo $indir
 echo $outdir
 echo $hztdir
 
 time=""
 times_mask=""
 for minute in $minutes
 do
  time=$time$yrday$hour$minute"0U "
  times_mask=$times_mask$yrday$hour$minute" "
 done
 echo "TimesMASK: "$times_mask
 
 #time="1721400300U 1721400350U 1721400400U 1721400450U"
 #times_mask="172140030 172140035 172140040 172140045"
 
 # Execute parallelized ZDR-column calculation
 if [ $parallel -eq 1 ]
 then
  printf %s\\n ${time[@]} | xargs -n1 -P4 bash $HOME/batch_ZDR_outsourced.sh
 else
  printf %s\\n ${time[@]} | xargs -n1 bash $HOME/batch_ZDR_outsourced.sh
 fi
 
 # Convert produced csv-Files to a more adequate format
 
 # IDL SPECIFIC SETTINGS
 cd $HOME
 echo "TO load IDL module: module load idl"
 export IDL_OTLDIR="path_to_IDL"
 export IDL_STARTUP=$IDL_OTLDIR/"setup_file.idl"
 export IDL_NO_XWINDOWS=1
 
# for time_mask in $times_mask
# do
#  idl "pol2cart_execution" -args $datadir $tbss_dir $time_mask "CZC"
# done
# 
# Rscript IDLCSV_Converter.R $tbss_dir
# Rscript TBSS_masking_CZC.R $tbss_dir
 cd $datadir
 ######################### TASK 1.3 - REMOVE ALL FOLDERS (ex. ZDC) ###########################
 
 #REMOVE ALL FOLDERS CREATED IN TASK 1.1 ////////////
 #Print current directory
 echo "The current directory (datadir) is:"
 echo $PWD
  
 # Removing all downloaded products
 for prod in $products
 do
  if [ $prod == "TRTC" ] || [ $prod == "CZC" ] || [ $prod == "BZC" ] || [ $prod == "MZC" ] || [ $prod == "RZC" ]
  then
   continue
  fi
  rm -r $datadir"/"$prod
 done
 echo "All folders but ZDC deleted!"   
#end hours loop-------------------------------------------------------------------------------
done

#Zipping CZC + TRTC (if not already existing)
toZIP="None"
for prod in $toZIP
do
 if [ ! -f $prod.zip ]
 then
  echo $prod
  zip -r $prod.zip $prod
  #zip -r $prod.zip $datadir"/"$prod
 fi
done

# Special case for ZDC
zip -r "ZDC.zip" ./ZDC/$threshold_dir
 
rm -r $datadir"/ZDC"
rm -r $datadir"/TRTC"
rm -r $datadir"/CZC"
rm -r $datadir"/TBSS"
rm -r $datadir"/BZC"
rm -r $datadir"/MZC"
rm -r $datadir"/RZC"
