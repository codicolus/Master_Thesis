; File for Plotting predefined RHI_crossections
; This script is for preparation of all required input for serial RHI-plot generation
; Required specifications are passed by the Script "IDL_automated_plotting_routines"
;
; Script written by Christoph von Matt

;Compile modified and own routines
.COMPILE serial_cross
.COMPILE rhi4_zerodeg
.COMPILE csi_modified
.COMPILE adjusted_colscale


paths= COMMAND_LINE_ARGS()
PRINT, paths

datadir=paths[0]
outdir=paths[1]
moment=paths[2]
chy1=int(paths[3])
chx1=int(paths[4])
chy2=int(paths[5])
chx2=int(paths[6])
min=int(paths[7])
max=int(paths[8])
howmany=int(paths[9])
prd=paths[10]
height_zero=float(paths[11])

PRINT, moment
PRINT, chy1
PRINT, chy2
PRINT, height_zero


;gets all files stored in provided datadir
; endings and filenames are handled depending on product type

CD, datadir
files=FILE_SEARCH()
IF prd EQ "ZDC" THEN files=files[where(strmatch(files, "*0000*"))]
IF (prd EQ "MLA") OR (prd EQ "MLD") OR (prd EQ "MLL") OR (prd EQ "MLP") OR (prd EQ "MLW") THEN files=files[where(strmatch(files,"*01350U*.001"))]
IF (prd EQ "YMA") OR (prd EQ "YMD") OR (prd EQ "YML") OR (prd EQ "YMP") OR (prd EQ "YMW") THEN files=files[where(strmatch(files,"*16207L*.801"))]
IF prd EQ "HZT" THEN files=files[where(strmatch(files,"*00000L.802"))]

;IF prd NE "ZDC" THEN files=files[where(strmatch(files,"*00000L.800"))]
;, files[where(strmatch(files,"*0000*.801"))], files[where(strmatch(files,"*0000*.802"))], files[where(strmatch(files,"*0000*.803"))] ]

;IF prd NE "ZDC" THEN files=[ files[where(strmatch(files,"*0030*.830"))], files[where(strmatch(files,"*0030*.840"))], files[where(strmatch(files,"*0030*.850"))] ]

PRINT, files

PRINT, N_ELEMENTS(files)

serial_cross, files, datadir, chy1, chx1, chy2, chx2, min, max, moment, howmany, height_zero

exit
