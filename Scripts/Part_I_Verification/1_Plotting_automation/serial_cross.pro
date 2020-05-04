; Script for a serial RHI-plot generation
; Makes use of a modified version of the MCH-RHI-Plotting routine
;
; Written by Christoph von Matt

PRO serial_cross, files, datadir, chy1, chx1, chy2, chx2, min, max, mom, howmany, height_zero
	
	FOREACH element, files DO BEGIN
		PRINT, element
		FOR i=0,howmany-1 DO BEGIN
			product=strmid(element,0,3)
			time=strmid(element,7,strlen(element)-1)
			label= product + time
			CD, datadir
			;rhi4_zerodeg, datadir + element,axis=[ [chy1 + (0.5*i),chx1], [chy2 + (0.5*i),chx2] ], min_h=min, max_h=max, moment=mom, pngfile="plot_" + label + "_"  + mom + "_" + "RHIcross" + strtrim(int(i+1),2) + ".png", height_zero=height_zero
			rhi4_zerodeg, datadir + element,axis=[ [chy1,chx1+(0.5*i)], [chy2,chx2+(0.5*i)] ], min_h=min, max_h=max, moment=mom, pngfile="plot_" + label + "_"  + mom + "_" + "RHIcross" + strtrim(int(i+1),2) + ".png", height_zero=height_zero
		while !d.window ne -1 do wdelete, !d.window
		
		ENDFOR
	ENDFOREACH
END
  
