; This script is for preparation of all required input for serial (modified) POI-plot generation
; Required specifications are passed by the Script "IDL_automated_plotting_routines"
;
; Script written by Christoph von Matt

;Compile modified and own routines
.COMPILE serial_crosspoi4
.COMPILE modified_poi4
.COMPILE adjusted_colscale

paths= COMMAND_LINE_ARGS()
PRINT, paths

datadir=paths[0]
outdir=paths[1]
moment=paths[2]
chy1=float(paths[3])
chy2=float(paths[4])
chx1=float(paths[5])
chx2=float(paths[6])
trt=paths[7]
chy1_cross=float(paths[8])
chy2_cross=float(paths[9])
chx1_cross=float(paths[10])
chx2_cross=float(paths[11])
prd=paths[12]
howmany=int(paths[13])
location=int(paths[14])

PRINT, moment
PRINT, chy1
PRINT, chx1
PRINT, typename(chx1)

;gets all files stored in provided datadir
; only files of certain elevations are considered according to specific endings
; 	(e.g. .801 = -0.2 deg elevation)
; endings and filenames are handled depending on product type
CD, datadir
files=FILE_SEARCH()
IF prd EQ "ZDC" THEN files=files[where(strmatch(files, "*0000*"))]
IF (prd EQ "MLA") OR (prd EQ "MLD") OR (prd EQ "MLL") OR (prd EQ "MLP") OR (prd EQ "MLW") THEN files=files[where(strmatch(files,"*10400U*"))]
IF (prd EQ "YMA") OR (prd EQ "YMD") OR (prd EQ "YML") OR (prd EQ "YMP") OR (prd EQ "YMW") THEN files=files[where(strmatch(files,"*16207L*.801"))]
IF prd EQ "HZT" THEN files=files[where(strmatch(files,"*00000L.802"))] 
; files[where(strmatch(files,"*0000*.801"))], files[where(strmatch(files,"*0000*.802"))], files[where(strmatch(files,"*0000*.800"))] ]

;IF prd NE "ZDC" THEN files=[ files[where(strmatch(files,"*0050*.830"))], files[where(strmatch(files,"*0050*.840"))], files[where(strmatch(files,"*0030*.850"))] ]

PRINT, files[1]

PRINT, N_ELEMENTS(files)

serial_crosspoi4, files, datadir, moment, [chy1, chy2], [chx1, chx2], trt, [chy1_cross, chy2_cross], [chx1_cross, chx2_cross], howmany, location

exit
