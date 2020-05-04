; Script produces and saves histogram data for all input files
;
; Written by Christoph von Matt

PRO serial_histograms, files, datadir, outdir

	FOREACH element, files DO BEGIN
		CD, datadir
		data=load_rad4(element)
		hist=histogram(data)
		CD, outdir
		WRITE_CSV,"hist_" + element + ".csv", hist
		DELVAR, data
		DELVAR, hist
		CD, datadir
	ENDFOREACH
END
