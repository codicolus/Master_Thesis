; This is a file for automatized serial histogram calculation
; For each file detected in datadir a histogramm will be calculated using
; the routine "serial_histograms"
; Required specifications (passed by Script "IDL_automated_plotting_routines"):
;	- datadir
;	- outdir: where output will be stored
;	- input_type: moment (deprecated)
;
; Written by Christoph von Matt


;Compile own routines
.COMPILE serial_histograms

paths= COMMAND_LINE_ARGS()
PRINT, paths

datadir=paths[0]
outdir=paths[1]
input_type=paths[2]

;gets all files stored in provided datadir
CD, datadir
files=FILE_SEARCH()
PRINT, files[1] + "_hist"

PRINT, N_ELEMENTS(files)

serial_histograms, files, datadir, outdir

exit




