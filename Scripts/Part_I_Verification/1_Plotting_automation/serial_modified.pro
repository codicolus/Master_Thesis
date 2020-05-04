; Script for serial POI-plotting of all given files
; Makes use of a modified version of the MCH-POI-Plotting routine
;
; Written by Christoph von Matt

PRO serial_modified, files, datadir, mom, chy, chx, trt

	FOREACH element, files DO BEGIN
		product=strmid(element,0,3)
		IF product EQ "ZDC" THEN BEGIN
			thistime=strmid(element,3,9)
			thistime=thistime + strtrim(0,2)
			label=product+thistime
		ENDIF ELSE BEGIN
			thistime=strmid(element,3,10)
			label=product+thistime+strmid(element, strlen(element)-4, strlen(element)-1)
		ENDELSE
		
		IF ( (chy[0] NE 400) OR (chy[1] NE 900) OR (chx[0] NE 0) OR (chx[1] NE 360) ) THEN BEGIN
			label= label + "_ZOOM"
		ENDIF
		
		CD, datadir
		PRINT, trt
		
		IF trt EQ "none" THEN BEGIN
			modified_poi4,element,/set,/map,moment=mom, chyrange=chy, chxrange=chx, pngfile="plot_" + label + "_" + mom + "_" + "POI_mod.png", chy_cross=[0,0], chx_cross=[0,0]
			while !d.window ne -1 do wdelete, !d.window
		ENDIF ELSE BEGIN
			trt_file=trt+"CZC"+thistime+"T.trt"
			PRINT, trt_file
			modified_poi4,element,/set,/map,moment=mom, chyrange=chy, chxrange=chx, trt_plot=trt_file, pngfile="plot_" + label + "_" + mom + "_" + "TRT_POI.png", chy_cross=[0,0], chx_cross=[0,0]
			while !d.window ne -1 do wdelete, !d.window
		ENDELSE
	ENDFOREACH
END
