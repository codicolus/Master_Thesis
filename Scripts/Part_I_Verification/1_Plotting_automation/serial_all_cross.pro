; Routine for Plotting all files in a directory
; Makes use of a modified version of the MCH-POI-Plotting routine
;
; Written by Christoph von Matt

PRO serial_all_cross, files, datadir, mom, chy, chx, trt, chy_cross, chx_cross, howmany


	FOREACH element, files DO BEGIN
		product=strmid(element,0,3)
		IF product EQ "ZDC" THEN BEGIN
			thistime=strmid(element,3,9)
			thistime=thistime + strtrim(0,2)
			label=product+thistime
		ENDIF ELSE BEGIN
			thistime=strmid(element,3,9)
			PRINT, thistime
			label=product+thistime+strmid(element, strlen(element)-4, strlen(element)-1)
		ENDELSE
		
		IF ( (chy[0] NE 400) OR (chy[1] NE 900) OR (chx[0] NE 0) OR (chx[1] NE 360) ) THEN BEGIN
			label= label + "_ZOOM"
		ENDIF
		
		CD, datadir
		PRINT, trt
		;FOR i=0, howmany-1 DO BEGIN
			IF trt EQ "none" THEN BEGIN
				all_cross_poi,element,/set,/map,moment=mom, chyrange=chy, chxrange=chx, pngfile="plot_" + label + "_" + mom + "_" + "POI_cross" + "_ALL.png", chy_cross=chy_cross, chx_cross=chx_cross, howmany=howmany
				while !d.window ne -1 do wdelete, !d.window
			ENDIF ELSE BEGIN
				trt_file=trt+"CZC"+thistime+ strtrim(int(0),2) + "T.trt"
				PRINT, trt_file
				all_cross_poi,element,/set,/map,moment=mom, chyrange=chy, chxrange=chx, trt_plot=trt_file, pngfile="plot_" + label + "_" + mom + "_" + "TRT_POI_cross" + "_ALL.png", chy_cross=chy_cross, chx_cross=chx_cross, howmany=howmany
				while !d.window ne -1 do wdelete, !d.window
			ENDELSE
		;ENDFOR
	ENDFOREACH
END
