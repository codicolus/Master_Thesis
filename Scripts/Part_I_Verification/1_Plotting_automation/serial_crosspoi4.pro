; Routine for Plotting all files in a directory
; Makes use of a modified version of the MCH-POI-Plotting routine
;
; Written by Christoph von Matt

PRO serial_crosspoi4, files, datadir, mom, chy, chx, trt, chy_cross, chx_cross, howmany, location


	FOREACH element, files DO BEGIN
		product=strmid(element,0,3)
		IF product EQ "ZDC" THEN BEGIN
			thistime=strmid(element,3,9)
			thistime=thistime + strtrim(0,2)
			label=product+thistime
		ENDIF ELSE BEGIN
			thistime=strmid(element,3,9)
			PRINT,thistime
			label=product+thistime+strmid(element, strlen(element)-4, strlen(element)-1)
		ENDELSE
		
		IF ( (chy[0] NE 400) OR (chy[1] NE 900) OR (chx[0] NE 0) OR (chx[1] NE 360) ) THEN BEGIN
			label= label + "_ZOOM"
		ENDIF
		
		CD, datadir
		PRINT, trt
		
		IF location EQ 1 THEN BEGIN
			IF trt EQ "none" THEN BEGIN
				;modified_poi4,element,/set,/map,moment=mom, chyrange=chy, chxrange=chx, pngfile="plot_" + label + "_" + mom + "_" + "POI_cross_location" + ".png", chy_cross=[chy_cross[0],chy_cross[1]], chx_cross=chx_cross, location=location
				;modified_poi4,element,/set,/map,moment=mom, chyrange=chy, chxrange=chx, pngfile="plot_" + label + "_" + mom + "_" + "POI_cross_location" + ".png", chy_cross=chy_cross, chx_cross=[chx_cross[0], chx_cross[1]], location=location
				while !d.window ne -1 do wdelete, !d.window
			ENDIF ELSE BEGIN
				trt_file=trt+"CZC"+thistime+ strtrim(int(0),2)+"T.trt"
				PRINT, trt_file
				modified_poi4,element,/set,/map,moment=mom, chyrange=chy, chxrange=chx, trt_plot=trt_file, pngfile="plot_" + label + "_" + mom + "_" + "TRT_POI_cross_location" + ".png", chy_cross=[chy_cross[0],chy_cross[1]], chx_cross=chx_cross, location=location
				;modified_poi4,element,/set,/map,moment=mom, chyrange=chy, chxrange=chx, trt_plot=trt_file, pngfile="plot_" + label + "_" + mom + "_" + "TRT_POI_cross_location" + ".png", chy_cross=chy_cross, chx_cross=[chx_cross[0], chx_cross[1]], location=location
				while !d.window ne -1 do wdelete, !d.window
			ENDELSE
		ENDIF ELSE BEGIN
			FOR i=0, howmany-1 DO BEGIN
				IF trt EQ "none" THEN BEGIN
					;modified_poi4,element,/set,/map,moment=mom, chyrange=chy, chxrange=chx, pngfile="plot_" + label + "_" + mom + "_" + "POI_cross" + strtrim(int(i+1),2) + ".png", chy_cross=[chy_cross[0]+(0.5*i),chy_cross[0]+(0.5*i)], chx_cross=chx_cross, location=location
					;modified_poi4,element,/set,/map,moment=mom, chyrange=chy, chxrange=chx, pngfile="plot_" + label + "_" + mom + "_" + "POI_cross" + strtrim(int(i+1),2) + ".png", chy_cross=chy_cross, chx_cross=[chx_cross[0]+(0.5*i), chx_cross[0]+(0.5*i)], location=location
					while !d.window ne -1 do wdelete, !d.window
				ENDIF ELSE BEGIN
					trt_file=trt+"CZC"+thistime+ strtrim(int(0),2)+"T.trt"
					PRINT, trt_file
					;modified_poi4,element,/set,/map,moment=mom, chyrange=chy, chxrange=chx, trt_plot=trt_file, pngfile="plot_" + label + "_" + mom + "_" + "TRT_POI_cross" + strtrim(int(i+1),2) + ".png", chy_cross=[chy_cross[0]+(0.5*i),chy_cross[1]+(0.5*i)], chx_cross=chx_cross, location=location
					modified_poi4,element,/set,/map,moment=mom, chyrange=chy, chxrange=chx, trt_plot=trt_file, pngfile="plot_" + label + "_" + mom + "_" + "TRT_POI_cross" + strtrim(int(i+1),2) + ".png", chy_cross=chy_cross, chx_cross=[chx_cross[0]+(0.5*i), chx_cross[1]+(0.5*i)], location=location
					while !d.window ne -1 do wdelete, !d.window
				ENDELSE
			ENDFOR
		ENDELSE
	ENDFOREACH
END
