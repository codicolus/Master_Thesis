; This script is for preparation of all required input for serial (modified) POI-plot generation
; Modifications include: plotting of cross sections or selected grid boxes
; Required specifications are passed by the Script "IDL_automated_plotting_routines"
;
; Script written by Christoph von Matt

;Compile modified and own routines
.COMPILE serial_modified
.COMPILE modified_poi4

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
prd=paths[12]

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
;IF prd NE "ZDC" THEN files=files[where(strmatch(files,"*.001"))]
;IF prd NE "ZDC" THEN files=[ files[where(strmatch(files,"*.830"))], files[where(strmatch(files,"*.840"))], files[where(strmatch(files,"*.850"))] ]
;IF prd NE "ZDC" THEN files=[ files[where(strmatch(files,"*.800"))], files[where(strmatch(files,"*.801"))], files[where(strmatch(files,"*.802"))], files[where(strmatch(files,"*.803"))] ]
PRINT, files[1]

PRINT, N_ELEMENTS(files)

serial_modified, files, datadir, moment, [chy1, chy2], [chx1, chx2], trt

exit
