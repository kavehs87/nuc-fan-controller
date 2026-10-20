	(footprint "Package_TO_SOT_SMD:TO-252-3_TabPin2"
		(version 20260206)
		(generator "kicad-footprint-generator")
		(layer "F.Cu")
		(descr "TO-252/DPAK SMD package, http://www.infineon.com/cms/en/product/packages/PG-TO252/PG-TO252-3-1/")
		(tags "DPAK TO-252 DPAK-3 TO-252-3 SOT-428")
		(property "Reference" "REF**"
			(at 0 -4.5 0)
			(layer "F.SilkS")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Value" "TO-252-3_TabPin2"
			(at 0 4.5 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "KiLib_Generator" "package/TO_SOT/SMD"
			(at 0 0 0)
			(layer "F.SilkS")
			(hide yes)
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(attr smd)
		(duplicate_pad_numbers_are_jumpers no)
		(fp_line
			(start -3.31 -3.45)
			(end -3.31 -3.18)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -3.31 3.45)
			(end -3.31 3.18)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.11 -3.45)
			(end -3.31 -3.45)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.11 3.45)
			(end -3.31 3.45)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_poly
			(pts
				(xy -5.04 -3.14)
				(xy -5.38 -3.61)
				(xy -4.7 -3.61)
			)
			(stroke
				(width 0.12)
				(type solid)
			)
			(fill yes)
			(layer "F.SilkS")
		)
		(fp_rect
			(start -6.39 -3.5)
			(end 4.71 3.5)
			(stroke
				(width 0.05)
				(type solid)
			)
			(fill no)
			(layer "F.CrtYd")
		)
		(fp_line
			(start -5.81 -2.655)
			(end -5.81 -1.905)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start -5.81 -1.905)
			(end -3.11 -1.905)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start -5.81 -0.375)
			(end -5.81 0.375)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start -5.81 0.375)
			(end -3.11 0.375)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start -5.81 1.905)
			(end -5.81 2.655)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start -5.81 2.655)
			(end -3.11 2.655)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start -3.11 -0.375)
			(end -5.81 -0.375)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start -3.11 1.905)
			(end -5.81 1.905)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start -2.705 -2.655)
			(end -5.81 -2.655)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start 3.11 -2.7)
			(end 4.11 -2.7)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start 4.11 -2.7)
			(end 4.11 2.7)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start 4.11 2.7)
			(end 3.11 2.7)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_poly
			(pts
				(xy 3.11 -3.25)
				(xy 3.11 3.25)
				(xy -3.11 3.25)
				(xy -3.11 -2.25)
				(xy -2.11 -3.25)
			)
			(stroke
				(width 0.1)
				(type solid)
			)
			(fill no)
			(layer "F.Fab")
		)
		(fp_text user "${REFERENCE}"
			(at 0 0 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(pad "" smd roundrect
			(at -0.415 -1.525)
			(size 3.05 2.75)
			(layers "F.Paste")
			(roundrect_rratio 0.090909)
		)
		(pad "" smd roundrect
			(at -0.415 1.525)
			(size 3.05 2.75)
			(layers "F.Paste")
			(roundrect_rratio 0.090909)
		)
		(pad "" smd roundrect
			(at 2.935 -1.525)
			(size 3.05 2.75)
			(layers "F.Paste")
			(roundrect_rratio 0.090909)
		)
		(pad "" smd roundrect
			(at 2.935 1.525)
			(size 3.05 2.75)
			(layers "F.Paste")
			(roundrect_rratio 0.090909)
		)
		(pad "1" smd roundrect
			(at -5.04 -2.28)
			(size 2.2 1.2)
			(layers "F.Cu" "F.Mask" "F.Paste")
			(roundrect_rratio 0.208333)
		)
		(pad "2" smd roundrect
			(at -5.04 0)
			(size 2.2 1.2)
			(layers "F.Cu" "F.Mask" "F.Paste")
			(roundrect_rratio 0.208333)
		)
		(pad "2" smd roundrect
			(at 1.26 0)
			(size 6.4 5.8)
			(layers "F.Cu" "F.Mask")
			(roundrect_rratio 0.043103)
		)
		(pad "3" smd roundrect
			(at -5.04 2.28)
			(size 2.2 1.2)
			(layers "F.Cu" "F.Mask" "F.Paste")
			(roundrect_rratio 0.208333)
		)
		(embedded_fonts no)
		(model "${KICAD10_3DMODEL_DIR}/Package_TO_SOT_SMD.3dshapes/TO-252-3_TabPin2.step"
			(offset
				(xyz 0 0 0)
			)
			(scale
				(xyz 1 1 1)
			)
			(rotate
				(xyz 0 0 0)
			)
		)
	)

	(footprint "Package_TO_SOT_THT:TO-220-3_Vertical"
		(version 20260206)
		(generator "kicad-footprint-generator")
		(layer "F.Cu")
		(descr "TO-220-3, Vertical, RM 2.54mm, see https://www.vishay.com/docs/66542/to-220-1.pdf")
		(tags "TO-220-3 Vertical RM 2.54mm")
		(property "Reference" "REF**"
			(at 2.54 -4.1 0)
			(layer "F.SilkS")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Value" "TO-220-3_Vertical"
			(at 2.54 2.2 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "KiLib_Generator" "package/TO_SOT/THT"
			(at 0 0 0)
			(layer "F.SilkS")
			(hide yes)
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(attr through_hole)
		(duplicate_pad_numbers_are_jumpers no)
		(fp_line
			(start -2.57 -3.26)
			(end 7.65 -3.26)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -2.57 -1.88)
			(end 7.65 -1.88)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -2.57 1.36)
			(end -2.57 -3.26)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 0.69 -3.26)
			(end 0.69 -1.88)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.39 -3.26)
			(end 4.39 -1.88)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 7.65 -3.26)
			(end 7.65 1.36)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 7.65 1.36)
			(end -2.57 1.36)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_rect
			(start -2.71 -3.4)
			(end 7.79 1.5)
			(stroke
				(width 0.05)
				(type solid)
			)
			(fill no)
			(layer "F.CrtYd")
		)
		(fp_line
			(start -2.46 -1.88)
			(end 7.54 -1.88)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start 0.69 -3.15)
			(end 0.69 -1.88)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start 4.39 -3.15)
			(end 4.39 -1.88)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_rect
			(start -2.46 -3.15)
			(end 7.54 1.25)
			(stroke
				(width 0.1)
				(type solid)
			)
			(fill no)
			(layer "F.Fab")
		)
		(fp_text user "${REFERENCE}"
			(at 2.54 -0.95 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(pad "1" thru_hole rect
			(at 0 0)
			(size 1.905 2)
			(drill 1.1)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(pad "2" thru_hole oval
			(at 2.54 0)
			(size 1.905 2)
			(drill 1.1)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(pad "3" thru_hole oval
			(at 5.08 0)
			(size 1.905 2)
			(drill 1.1)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(embedded_fonts no)
		(model "${KICAD10_3DMODEL_DIR}/Package_TO_SOT_THT.3dshapes/TO-220-3_Vertical.step"
			(offset
				(xyz 0 0 0)
			)
			(scale
				(xyz 1 1 1)
			)
			(rotate
				(xyz 0 0 0)
			)
		)
	)

	(footprint "Package_TO_SOT_THT:TO-92_Inline_Wide"
		(version 20260206)
		(generator "pcbnew")
		(generator_version "10.0")
		(layer "F.Cu")
		(descr "TO-92 leads in-line, wide, drill 0.75mm (see NXP sot054_po.pdf)")
		(tags "to-92 sc-43 sc-43a sot54 PA33 transistor")
		(property "Reference" "REF**"
			(at 2.54 -3.56 0)
			(layer "F.SilkS")
			
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Value" "TO-92_Inline_Wide"
			(at 2.54 2.79 0)
			(layer "F.Fab")
			
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Datasheet" ""
			(at 0 0 0)
			(unlocked yes)
			(layer "F.Fab")
			(hide yes)
			
			(effects
				(font
					(size 1.27 1.27)
					(thickness 0.15)
				)
			)
		)
		(property "Description" ""
			(at 0 0 0)
			(unlocked yes)
			(layer "F.Fab")
			(hide yes)
			
			(effects
				(font
					(size 1.27 1.27)
					(thickness 0.15)
				)
			)
		)
		(attr through_hole)
		(duplicate_pad_numbers_are_jumpers no)
		(fp_line
			(start 0.74 1.85)
			(end 4.34 1.85)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
			
		)
		(fp_arc
			(start 0.1836 -1.098807)
			(mid 1.143021 -2.192817)
			(end 2.54 -2.6)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
			
		)
		(fp_arc
			(start 0.74 1.85)
			(mid 0.446097 1.509328)
			(end 0.215816 1.122795)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
			
		)
		(fp_arc
			(start 2.54 -2.6)
			(mid 3.936979 -2.192818)
			(end 4.8964 -1.098807)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
			
		)
		(fp_arc
			(start 4.864184 1.122795)
			(mid 4.633903 1.509328)
			(end 4.34 1.85)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
			
		)
		(fp_line
			(start -1.01 -2.73)
			(end -1.01 2.01)
			(stroke
				(width 0.05)
				(type solid)
			)
			(layer "F.CrtYd")
			
		)
		(fp_line
			(start -1.01 -2.73)
			(end 6.09 -2.73)
			(stroke
				(width 0.05)
				(type solid)
			)
			(layer "F.CrtYd")
			
		)
		(fp_line
			(start 6.09 2.01)
			(end -1.01 2.01)
			(stroke
				(width 0.05)
				(type solid)
			)
			(layer "F.CrtYd")
			
		)
		(fp_line
			(start 6.09 2.01)
			(end 6.09 -2.73)
			(stroke
				(width 0.05)
				(type solid)
			)
			(layer "F.CrtYd")
			
		)
		(fp_line
			(start 0.8 1.75)
			(end 4.3 1.75)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
			
		)
		(fp_arc
			(start 0.786375 1.753625)
			(mid 0.248779 -0.949055)
			(end 2.54 -2.48)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
			
		)
		(fp_arc
			(start 2.54 -2.48)
			(mid 4.831221 -0.949055)
			(end 4.293625 1.753625)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
			
		)
		(fp_text user "${REFERENCE}"
			(at 2.54 0 0)
			(layer "F.Fab")
			
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(pad "1" thru_hole rect
			(at 0 0)
			(size 1.5 1.5)
			(drill 0.8)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
			
		)
		(pad "2" thru_hole circle
			(at 2.54 0)
			(size 1.5 1.5)
			(drill 0.8)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
			
		)
		(pad "3" thru_hole circle
			(at 5.08 0)
			(size 1.5 1.5)
			(drill 0.8)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
			
		)
		(embedded_fonts no)
		(model "${KICAD10_3DMODEL_DIR}/Package_TO_SOT_THT.3dshapes/TO-92_Inline_Wide.step"
			(offset
				(xyz 0 0 0)
			)
			(scale
				(xyz 1 1 1)
			)
			(rotate
				(xyz 0 0 0)
			)
		)
	)

	(footprint "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
		(version 20260206)
		(generator "kicad-footprint-generator")
		(layer "F.Cu")
		(descr "Through hole straight pin header, 1x02, 2.54mm pitch, single row")
		(tags "Through hole pin header THT 1x02 2.54mm single row")
		(property "Reference" "REF**"
			(at 0 -2.38 0)
			(layer "F.SilkS")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Value" "PinHeader_1x02_P2.54mm_Vertical"
			(at 0 4.92 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "KiLib_Generator" "connector/pin_header_socket"
			(at 0 0 0)
			(layer "F.SilkS")
			(hide yes)
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(attr through_hole)
		(duplicate_pad_numbers_are_jumpers no)
		(fp_line
			(start -1.38 -1.38)
			(end 0 -1.38)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -1.38 0)
			(end -1.38 -1.38)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -1.38 1.27)
			(end -1.38 3.92)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -1.38 1.27)
			(end 1.38 1.27)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -1.38 3.92)
			(end 1.38 3.92)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.38 1.27)
			(end 1.38 3.92)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_rect
			(start -1.77 -1.77)
			(end 1.77 4.32)
			(stroke
				(width 0.05)
				(type solid)
			)
			(fill no)
			(layer "F.CrtYd")
		)
		(fp_line
			(start -1.27 -0.635)
			(end -0.635 -1.27)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start -1.27 3.81)
			(end -1.27 -0.635)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start -0.635 -1.27)
			(end 1.27 -1.27)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start 1.27 -1.27)
			(end 1.27 3.81)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start 1.27 3.81)
			(end -1.27 3.81)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_text user "${REFERENCE}"
			(at 0 1.27 90)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(pad "1" thru_hole rect
			(at 0 0)
			(size 1.7 1.7)
			(drill 1)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(pad "2" thru_hole circle
			(at 0 2.54)
			(size 1.7 1.7)
			(drill 1)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(embedded_fonts no)
		(model "${KICAD10_3DMODEL_DIR}/Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x02_P2.54mm_Vertical.step"
			(offset
				(xyz 0 0 0)
			)
			(scale
				(xyz 1 1 1)
			)
			(rotate
				(xyz 0 0 0)
			)
		)
	)

	(footprint "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
		(version 20260206)
		(generator "kicad-footprint-generator")
		(layer "F.Cu")
		(descr "Through hole straight pin header, 1x04, 2.54mm pitch, single row")
		(tags "Through hole pin header THT 1x04 2.54mm single row")
		(property "Reference" "REF**"
			(at 0 -2.38 0)
			(layer "F.SilkS")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Value" "PinHeader_1x04_P2.54mm_Vertical"
			(at 0 10 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "KiLib_Generator" "connector/pin_header_socket"
			(at 0 0 0)
			(layer "F.SilkS")
			(hide yes)
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(attr through_hole)
		(duplicate_pad_numbers_are_jumpers no)
		(fp_line
			(start -1.38 -1.38)
			(end 0 -1.38)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -1.38 0)
			(end -1.38 -1.38)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -1.38 1.27)
			(end -1.38 9)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -1.38 1.27)
			(end 1.38 1.27)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -1.38 9)
			(end 1.38 9)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.38 1.27)
			(end 1.38 9)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_rect
			(start -1.77 -1.77)
			(end 1.77 9.39)
			(stroke
				(width 0.05)
				(type solid)
			)
			(fill no)
			(layer "F.CrtYd")
		)
		(fp_line
			(start -1.27 -0.635)
			(end -0.635 -1.27)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start -1.27 8.89)
			(end -1.27 -0.635)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start -0.635 -1.27)
			(end 1.27 -1.27)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start 1.27 -1.27)
			(end 1.27 8.89)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start 1.27 8.89)
			(end -1.27 8.89)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_text user "${REFERENCE}"
			(at 0 3.81 90)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(pad "1" thru_hole rect
			(at 0 0)
			(size 1.7 1.7)
			(drill 1)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(pad "2" thru_hole circle
			(at 0 2.54)
			(size 1.7 1.7)
			(drill 1)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(pad "3" thru_hole circle
			(at 0 5.08)
			(size 1.7 1.7)
			(drill 1)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(pad "4" thru_hole circle
			(at 0 7.62)
			(size 1.7 1.7)
			(drill 1)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(embedded_fonts no)
		(model "${KICAD10_3DMODEL_DIR}/Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x04_P2.54mm_Vertical.step"
			(offset
				(xyz 0 0 0)
			)
			(scale
				(xyz 1 1 1)
			)
			(rotate
				(xyz 0 0 0)
			)
		)
	)

	(footprint "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical"
		(version 20260206)
		(generator "kicad-footprint-generator")
		(layer "F.Cu")
		(descr "Through hole straight pin header, 1x05, 2.54mm pitch, single row")
		(tags "Through hole pin header THT 1x05 2.54mm single row")
		(property "Reference" "REF**"
			(at 0 -2.38 0)
			(layer "F.SilkS")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Value" "PinHeader_1x05_P2.54mm_Vertical"
			(at 0 12.54 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "KiLib_Generator" "connector/pin_header_socket"
			(at 0 0 0)
			(layer "F.SilkS")
			(hide yes)
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(attr through_hole)
		(duplicate_pad_numbers_are_jumpers no)
		(fp_line
			(start -1.38 -1.38)
			(end 0 -1.38)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -1.38 0)
			(end -1.38 -1.38)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -1.38 1.27)
			(end -1.38 11.54)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -1.38 1.27)
			(end 1.38 1.27)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -1.38 11.54)
			(end 1.38 11.54)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.38 1.27)
			(end 1.38 11.54)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_rect
			(start -1.77 -1.77)
			(end 1.77 11.93)
			(stroke
				(width 0.05)
				(type solid)
			)
			(fill no)
			(layer "F.CrtYd")
		)
		(fp_line
			(start -1.27 -0.635)
			(end -0.635 -1.27)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start -1.27 11.43)
			(end -1.27 -0.635)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start -0.635 -1.27)
			(end 1.27 -1.27)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start 1.27 -1.27)
			(end 1.27 11.43)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start 1.27 11.43)
			(end -1.27 11.43)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_text user "${REFERENCE}"
			(at 0 5.08 90)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(pad "1" thru_hole rect
			(at 0 0)
			(size 1.7 1.7)
			(drill 1)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(pad "2" thru_hole circle
			(at 0 2.54)
			(size 1.7 1.7)
			(drill 1)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(pad "3" thru_hole circle
			(at 0 5.08)
			(size 1.7 1.7)
			(drill 1)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(pad "4" thru_hole circle
			(at 0 7.62)
			(size 1.7 1.7)
			(drill 1)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(pad "5" thru_hole circle
			(at 0 10.16)
			(size 1.7 1.7)
			(drill 1)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(embedded_fonts no)
		(model "${KICAD10_3DMODEL_DIR}/Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x05_P2.54mm_Vertical.step"
			(offset
				(xyz 0 0 0)
			)
			(scale
				(xyz 1 1 1)
			)
			(rotate
				(xyz 0 0 0)
			)
		)
	)

	(footprint "Connector:FanPinHeader_1x04_P2.54mm_Vertical"
		(version 20260206)
		(generator "pcbnew")
		(generator_version "10.0")
		(layer "F.Cu")
		(descr "4-pin CPU fan Through hole pin header, e.g. for Wieson part number 2366C888-007 Molex 47053-1000, Foxconn HF27040-M1, Tyco 1470947-1 or equivalent, see http://www.formfactors.org/developer%5Cspecs%5Crev1_2_public.pdf")
		(tags "pin header 4-pin CPU fan")
		(property "Reference" "REF**"
			(at 4 -3.55 0)
			(layer "F.SilkS")
			
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Value" "FanPinHeader_1x04_P2.54mm_Vertical"
			(at 4.05 4.35 0)
			(layer "F.Fab")
			
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Datasheet" ""
			(at 0 0 0)
			(unlocked yes)
			(layer "F.Fab")
			(hide yes)
			
			(effects
				(font
					(size 1.27 1.27)
					(thickness 0.15)
				)
			)
		)
		(property "Description" ""
			(at 0 0 0)
			(unlocked yes)
			(layer "F.Fab")
			(hide yes)
			
			(effects
				(font
					(size 1.27 1.27)
					(thickness 0.15)
				)
			)
		)
		(attr through_hole)
		(duplicate_pad_numbers_are_jumpers no)
		(fp_line
			(start -1.35 -2.6)
			(end 4.4 -2.6)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
			
		)
		(fp_line
			(start -1.35 3.4)
			(end -1.35 -2.6)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
			
		)
		(fp_line
			(start 0 2.29)
			(end 5.08 2.29)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
			
		)
		(fp_line
			(start 0 3.3)
			(end 0 2.29)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
			
		)
		(fp_line
			(start 5.08 2.29)
			(end 5.08 3.3)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
			
		)
		(fp_line
			(start 5.75 -2.55)
			(end 8.95 -2.55)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
			
		)
		(fp_line
			(start 8.95 -2.55)
			(end 8.95 3.4)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
			
		)
		(fp_line
			(start 8.95 3.4)
			(end -1.35 3.4)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
			
		)
		(fp_line
			(start -1.75 3.8)
			(end -1.75 -3.2)
			(stroke
				(width 0.05)
				(type solid)
			)
			(layer "F.CrtYd")
			
		)
		(fp_line
			(start -1.75 3.8)
			(end 9.35 3.8)
			(stroke
				(width 0.05)
				(type solid)
			)
			(layer "F.CrtYd")
			
		)
		(fp_line
			(start 9.35 -3.2)
			(end -1.75 -3.2)
			(stroke
				(width 0.05)
				(type solid)
			)
			(layer "F.CrtYd")
			
		)
		(fp_line
			(start 9.35 -3.2)
			(end 9.35 3.8)
			(stroke
				(width 0.05)
				(type solid)
			)
			(layer "F.CrtYd")
			
		)
		(fp_line
			(start -1.25 -2.5)
			(end 4.4 -2.5)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
			
		)
		(fp_line
			(start -1.25 3.3)
			(end -1.25 -2.5)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
			
		)
		(fp_line
			(start -1.2 3.3)
			(end -1.25 3.3)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
			
		)
		(fp_line
			(start 0 2.3)
			(end 0 3.3)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
			
		)
		(fp_line
			(start 5.1 2.3)
			(end 0 2.3)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
			
		)
		(fp_line
			(start 5.1 3.3)
			(end 5.1 2.3)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
			
		)
		(fp_line
			(start 5.75 -2.5)
			(end 8.85 -2.5)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
			
		)
		(fp_line
			(start 8.85 -2.5)
			(end 8.85 3.3)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
			
		)
		(fp_line
			(start 8.85 3.3)
			(end -1.2 3.3)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
			
		)
		(fp_text user "${REFERENCE}"
			(at 1.85 -1.75 0)
			(layer "F.Fab")
			
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(pad "" np_thru_hole circle
			(at 5.08 -2.16 90)
			(size 1.1 1.1)
			(drill 1.1)
			(layers "*.Cu" "*.Mask")
			
		)
		(pad "1" thru_hole rect
			(at 0 0 90)
			(size 2.03 1.73)
			(drill 1.02)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
			
		)
		(pad "2" thru_hole oval
			(at 2.54 0 90)
			(size 2.03 1.73)
			(drill 1.02)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
			
		)
		(pad "3" thru_hole oval
			(at 5.08 0 90)
			(size 2.03 1.73)
			(drill 1.02)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
			
		)
		(pad "4" thru_hole oval
			(at 7.62 0 90)
			(size 2.03 1.73)
			(drill 1.02)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
			
		)
		(embedded_fonts no)
		(model "${KICAD10_3DMODEL_DIR}/Connector.3dshapes/FanPinHeader_1x04_P2.54mm_Vertical.step"
			(offset
				(xyz 0 0 0)
			)
			(scale
				(xyz 1 1 1)
			)
			(rotate
				(xyz 0 0 0)
			)
		)
	)

	(footprint "TestPoint:TestPoint_Pad_D1.5mm"
		(version 20260206)
		(generator "pcbnew")
		(generator_version "10.0")
		(layer "F.Cu")
		(descr "SMD pad as test Point, diameter 1.5mm")
		(tags "test point SMD pad")
		(property "Reference" "REF**"
			(at 0 -1.648 0)
			(layer "F.SilkS")
			
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Value" "TestPoint_Pad_D1.5mm"
			(at 0 1.75 0)
			(layer "F.Fab")
			
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Datasheet" ""
			(at 0 0 0)
			(unlocked yes)
			(layer "F.Fab")
			(hide yes)
			
			(effects
				(font
					(size 1.27 1.27)
					(thickness 0.15)
				)
			)
		)
		(property "Description" ""
			(at 0 0 0)
			(unlocked yes)
			(layer "F.Fab")
			(hide yes)
			
			(effects
				(font
					(size 1.27 1.27)
					(thickness 0.15)
				)
			)
		)
		(attr exclude_from_pos_files exclude_from_bom)
		(duplicate_pad_numbers_are_jumpers no)
		(fp_circle
			(center 0 0)
			(end 0 0.95)
			(stroke
				(width 0.12)
				(type solid)
			)
			(fill no)
			(layer "F.SilkS")
			
		)
		(fp_circle
			(center 0 0)
			(end 1.25 0)
			(stroke
				(width 0.05)
				(type solid)
			)
			(fill no)
			(layer "F.CrtYd")
			
		)
		(fp_text user "${REFERENCE}"
			(at 0 -1.65 0)
			(layer "F.Fab")
			
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(pad "1" smd circle
			(at 0 0)
			(size 1.5 1.5)
			(layers "F.Cu" "F.Mask")
			
		)
		(embedded_fonts no)
	)

	(footprint "MountingHole:MountingHole_3.2mm_M3"
		(version 20260206)
		(generator "kicad-footprint-generator")
		(layer "F.Cu")
		(descr "Mounting Hole 3.2mm, M3, no annular, generated by kicad-footprint-generator mountinghole.py")
		(tags "mountinghole M3")
		(property "Reference" "REF**"
			(at 0 -4.15 0)
			(layer "F.SilkS")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Value" "MountingHole_3.2mm_M3"
			(at 0 4.15 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "KiLib_Generator" "mounting_hardware/mounting_hole"
			(at 0 0 0)
			(layer "F.SilkS")
			(hide yes)
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(attr exclude_from_pos_files exclude_from_bom)
		(duplicate_pad_numbers_are_jumpers no)
		(fp_circle
			(center 0 0)
			(end 3.2 0)
			(stroke
				(width 0.15)
				(type solid)
			)
			(fill no)
			(layer "Cmts.User")
		)
		(fp_circle
			(center 0 0)
			(end 3.45 0)
			(stroke
				(width 0.05)
				(type solid)
			)
			(fill no)
			(layer "F.CrtYd")
		)
		(fp_text user "${REFERENCE}"
			(at 0 0 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(pad "" np_thru_hole circle
			(at 0 0)
			(size 3.2 3.2)
			(drill 3.2)
			(layers "*.Cu" "*.Mask")
		)
		(embedded_fonts no)
	)

	(footprint "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"
		(version 20260206)
		(generator "kicad-footprint-generator")
		(layer "F.Cu")
		(descr "CP, Radial series, Radial, pin pitch=3.50mm, diameter=8mm, height=12mm, Electrolytic Capacitor")
		(tags "CP Radial series Radial pin pitch 3.50mm diameter 8mm height 12mm Electrolytic Capacitor")
		(property "Reference" "REF**"
			(at 1.75 -5.25 0)
			(layer "F.SilkS")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Value" "CP_Radial_D8.0mm_P3.50mm"
			(at 1.75 5.25 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "KiLib_Generator" "capacitor/THT/other"
			(at 0 0 0)
			(layer "F.SilkS")
			(hide yes)
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(attr through_hole)
		(duplicate_pad_numbers_are_jumpers no)
		(fp_line
			(start -2.659698 -2.315)
			(end -1.859698 -2.315)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -2.259698 -2.715)
			(end -2.259698 -1.915)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.75 -4.08)
			(end 1.75 4.08)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.79 -4.08)
			(end 1.79 4.08)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.83 -4.079)
			(end 1.83 4.079)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.87 -4.078)
			(end 1.87 4.078)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.91 -4.077)
			(end 1.91 4.077)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.95 -4.075)
			(end 1.95 4.075)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.99 -4.073)
			(end 1.99 4.073)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.03 -4.07)
			(end 2.03 4.07)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.07 -4.068)
			(end 2.07 4.068)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.11 -4.064)
			(end 2.11 4.064)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.15 -4.061)
			(end 2.15 4.061)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.19 -4.056)
			(end 2.19 4.056)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.23 -4.052)
			(end 2.23 4.052)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.27 -4.047)
			(end 2.27 4.047)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.31 -4.042)
			(end 2.31 4.042)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.35 -4.036)
			(end 2.35 4.036)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.39 -4.03)
			(end 2.39 4.03)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.43 -4.023)
			(end 2.43 4.023)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.47 -4.017)
			(end 2.47 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.47 1.04)
			(end 2.47 4.017)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.51 -4.009)
			(end 2.51 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.51 1.04)
			(end 2.51 4.009)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.55 -4.002)
			(end 2.55 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.55 1.04)
			(end 2.55 4.002)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.59 -3.993)
			(end 2.59 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.59 1.04)
			(end 2.59 3.993)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.63 -3.985)
			(end 2.63 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.63 1.04)
			(end 2.63 3.985)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.67 -3.976)
			(end 2.67 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.67 1.04)
			(end 2.67 3.976)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.71 -3.967)
			(end 2.71 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.71 1.04)
			(end 2.71 3.967)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.75 -3.957)
			(end 2.75 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.75 1.04)
			(end 2.75 3.957)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.79 -3.947)
			(end 2.79 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.79 1.04)
			(end 2.79 3.947)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.83 -3.936)
			(end 2.83 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.83 1.04)
			(end 2.83 3.936)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.87 -3.925)
			(end 2.87 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.87 1.04)
			(end 2.87 3.925)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.91 -3.913)
			(end 2.91 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.91 1.04)
			(end 2.91 3.913)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.95 -3.901)
			(end 2.95 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.95 1.04)
			(end 2.95 3.901)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.99 -3.889)
			(end 2.99 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.99 1.04)
			(end 2.99 3.889)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.03 -3.876)
			(end 3.03 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.03 1.04)
			(end 3.03 3.876)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.07 -3.863)
			(end 3.07 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.07 1.04)
			(end 3.07 3.863)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.11 -3.849)
			(end 3.11 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.11 1.04)
			(end 3.11 3.849)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.15 -3.835)
			(end 3.15 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.15 1.04)
			(end 3.15 3.835)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.19 -3.82)
			(end 3.19 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.19 1.04)
			(end 3.19 3.82)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.23 -3.805)
			(end 3.23 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.23 1.04)
			(end 3.23 3.805)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.27 -3.789)
			(end 3.27 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.27 1.04)
			(end 3.27 3.789)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.31 -3.773)
			(end 3.31 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.31 1.04)
			(end 3.31 3.773)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.35 -3.757)
			(end 3.35 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.35 1.04)
			(end 3.35 3.757)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.39 -3.74)
			(end 3.39 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.39 1.04)
			(end 3.39 3.74)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.43 -3.722)
			(end 3.43 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.43 1.04)
			(end 3.43 3.722)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.47 -3.704)
			(end 3.47 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.47 1.04)
			(end 3.47 3.704)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.51 -3.685)
			(end 3.51 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.51 1.04)
			(end 3.51 3.685)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.55 -3.666)
			(end 3.55 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.55 1.04)
			(end 3.55 3.666)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.59 -3.646)
			(end 3.59 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.59 1.04)
			(end 3.59 3.646)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.63 -3.626)
			(end 3.63 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.63 1.04)
			(end 3.63 3.626)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.67 -3.605)
			(end 3.67 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.67 1.04)
			(end 3.67 3.605)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.71 -3.584)
			(end 3.71 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.71 1.04)
			(end 3.71 3.584)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.75 -3.562)
			(end 3.75 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.75 1.04)
			(end 3.75 3.562)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.79 -3.539)
			(end 3.79 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.79 1.04)
			(end 3.79 3.539)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.83 -3.516)
			(end 3.83 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.83 1.04)
			(end 3.83 3.516)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.87 -3.493)
			(end 3.87 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.87 1.04)
			(end 3.87 3.493)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.91 -3.468)
			(end 3.91 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.91 1.04)
			(end 3.91 3.468)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.95 -3.443)
			(end 3.95 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.95 1.04)
			(end 3.95 3.443)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.99 -3.418)
			(end 3.99 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.99 1.04)
			(end 3.99 3.418)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.03 -3.392)
			(end 4.03 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.03 1.04)
			(end 4.03 3.392)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.07 -3.365)
			(end 4.07 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.07 1.04)
			(end 4.07 3.365)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.11 -3.337)
			(end 4.11 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.11 1.04)
			(end 4.11 3.337)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.15 -3.309)
			(end 4.15 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.15 1.04)
			(end 4.15 3.309)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.19 -3.28)
			(end 4.19 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.19 1.04)
			(end 4.19 3.28)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.23 -3.25)
			(end 4.23 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.23 1.04)
			(end 4.23 3.25)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.27 -3.219)
			(end 4.27 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.27 1.04)
			(end 4.27 3.219)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.31 -3.188)
			(end 4.31 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.31 1.04)
			(end 4.31 3.188)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.35 -3.156)
			(end 4.35 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.35 1.04)
			(end 4.35 3.156)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.39 -3.123)
			(end 4.39 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.39 1.04)
			(end 4.39 3.123)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.43 -3.089)
			(end 4.43 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.43 1.04)
			(end 4.43 3.089)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.47 -3.055)
			(end 4.47 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.47 1.04)
			(end 4.47 3.055)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.51 -3.019)
			(end 4.51 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.51 1.04)
			(end 4.51 3.019)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.55 -2.982)
			(end 4.55 2.982)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.59 -2.945)
			(end 4.59 2.945)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.63 -2.906)
			(end 4.63 2.906)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.67 -2.867)
			(end 4.67 2.867)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.71 -2.826)
			(end 4.71 2.826)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.75 -2.784)
			(end 4.75 2.784)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.79 -2.741)
			(end 4.79 2.741)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.83 -2.696)
			(end 4.83 2.696)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.87 -2.651)
			(end 4.87 2.651)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.91 -2.604)
			(end 4.91 2.604)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.95 -2.555)
			(end 4.95 2.555)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.99 -2.505)
			(end 4.99 2.505)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.03 -2.453)
			(end 5.03 2.453)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.07 -2.4)
			(end 5.07 2.4)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.11 -2.344)
			(end 5.11 2.344)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.15 -2.287)
			(end 5.15 2.287)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.19 -2.227)
			(end 5.19 2.227)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.23 -2.165)
			(end 5.23 2.165)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.27 -2.101)
			(end 5.27 2.101)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.31 -2.034)
			(end 5.31 2.034)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.35 -1.964)
			(end 5.35 1.964)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.39 -1.89)
			(end 5.39 1.89)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.43 -1.813)
			(end 5.43 1.813)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.47 -1.731)
			(end 5.47 1.731)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.51 -1.644)
			(end 5.51 1.644)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.55 -1.552)
			(end 5.55 1.552)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.59 -1.453)
			(end 5.59 1.453)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.63 -1.346)
			(end 5.63 1.346)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.67 -1.228)
			(end 5.67 1.228)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.71 -1.097)
			(end 5.71 1.097)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.75 -0.947)
			(end 5.75 0.947)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.79 -0.768)
			(end 5.79 0.768)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.83 -0.533)
			(end 5.83 0.533)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_circle
			(center 1.75 0)
			(end 5.87 0)
			(stroke
				(width 0.12)
				(type solid)
			)
			(fill no)
			(layer "F.SilkS")
		)
		(fp_circle
			(center 1.75 0)
			(end 6 0)
			(stroke
				(width 0.05)
				(type solid)
			)
			(fill no)
			(layer "F.CrtYd")
		)
		(fp_line
			(start -1.676759 -1.7475)
			(end -0.876759 -1.7475)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start -1.276759 -2.1475)
			(end -1.276759 -1.3475)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_circle
			(center 1.75 0)
			(end 5.75 0)
			(stroke
				(width 0.1)
				(type solid)
			)
			(fill no)
			(layer "F.Fab")
		)
		(fp_text user "${REFERENCE}"
			(at 1.75 0 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(pad "1" thru_hole roundrect
			(at 0 0)
			(size 1.6 1.6)
			(drill 0.8)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
			(roundrect_rratio 0.15625)
		)
		(pad "2" thru_hole circle
			(at 3.5 0)
			(size 1.6 1.6)
			(drill 0.8)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(embedded_fonts no)
		(model "${KICAD10_3DMODEL_DIR}/Capacitor_THT.3dshapes/CP_Radial_D8.0mm_P3.50mm.step"
			(offset
				(xyz 0 0 0)
			)
			(scale
				(xyz 1 1 1)
			)
			(rotate
				(xyz 0 0 0)
			)
		)
	)

	(footprint "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm"
		(version 20260206)
		(generator "kicad-footprint-generator")
		(layer "F.Cu")
		(descr "CP, Radial series, Radial, pin pitch=2.50mm, diameter=6.3mm, height=7mm, Electrolytic Capacitor")
		(tags "CP Radial series Radial pin pitch 2.50mm diameter 6.3mm height 7mm Electrolytic Capacitor")
		(property "Reference" "REF**"
			(at 1.25 -4.4 0)
			(layer "F.SilkS")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Value" "CP_Radial_D6.3mm_P2.50mm"
			(at 1.25 4.4 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "KiLib_Generator" "capacitor/THT/other"
			(at 0 0 0)
			(layer "F.SilkS")
			(hide yes)
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(attr through_hole)
		(duplicate_pad_numbers_are_jumpers no)
		(fp_line
			(start -2.250241 -1.839)
			(end -1.620241 -1.839)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -1.935241 -2.154)
			(end -1.935241 -1.524)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.25 -3.23)
			(end 1.25 3.23)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.29 -3.23)
			(end 1.29 3.23)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.33 -3.229)
			(end 1.33 3.229)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.37 -3.228)
			(end 1.37 3.228)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.41 -3.226)
			(end 1.41 3.226)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.45 -3.224)
			(end 1.45 3.224)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.49 -3.221)
			(end 1.49 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.49 1.04)
			(end 1.49 3.221)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.53 -3.218)
			(end 1.53 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.53 1.04)
			(end 1.53 3.218)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.57 -3.214)
			(end 1.57 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.57 1.04)
			(end 1.57 3.214)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.61 -3.21)
			(end 1.61 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.61 1.04)
			(end 1.61 3.21)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.65 -3.205)
			(end 1.65 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.65 1.04)
			(end 1.65 3.205)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.69 -3.2)
			(end 1.69 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.69 1.04)
			(end 1.69 3.2)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.73 -3.195)
			(end 1.73 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.73 1.04)
			(end 1.73 3.195)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.77 -3.188)
			(end 1.77 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.77 1.04)
			(end 1.77 3.188)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.81 -3.182)
			(end 1.81 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.81 1.04)
			(end 1.81 3.182)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.85 -3.174)
			(end 1.85 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.85 1.04)
			(end 1.85 3.174)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.89 -3.167)
			(end 1.89 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.89 1.04)
			(end 1.89 3.167)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.93 -3.159)
			(end 1.93 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.93 1.04)
			(end 1.93 3.159)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.97 -3.15)
			(end 1.97 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 1.97 1.04)
			(end 1.97 3.15)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.01 -3.14)
			(end 2.01 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.01 1.04)
			(end 2.01 3.14)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.05 -3.131)
			(end 2.05 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.05 1.04)
			(end 2.05 3.131)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.09 -3.12)
			(end 2.09 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.09 1.04)
			(end 2.09 3.12)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.13 -3.109)
			(end 2.13 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.13 1.04)
			(end 2.13 3.109)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.17 -3.098)
			(end 2.17 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.17 1.04)
			(end 2.17 3.098)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.21 -3.086)
			(end 2.21 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.21 1.04)
			(end 2.21 3.086)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.25 -3.073)
			(end 2.25 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.25 1.04)
			(end 2.25 3.073)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.29 -3.06)
			(end 2.29 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.29 1.04)
			(end 2.29 3.06)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.33 -3.047)
			(end 2.33 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.33 1.04)
			(end 2.33 3.047)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.37 -3.032)
			(end 2.37 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.37 1.04)
			(end 2.37 3.032)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.41 -3.017)
			(end 2.41 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.41 1.04)
			(end 2.41 3.017)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.45 -3.002)
			(end 2.45 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.45 1.04)
			(end 2.45 3.002)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.49 -2.986)
			(end 2.49 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.49 1.04)
			(end 2.49 2.986)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.53 -2.969)
			(end 2.53 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.53 1.04)
			(end 2.53 2.969)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.57 -2.952)
			(end 2.57 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.57 1.04)
			(end 2.57 2.952)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.61 -2.934)
			(end 2.61 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.61 1.04)
			(end 2.61 2.934)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.65 -2.915)
			(end 2.65 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.65 1.04)
			(end 2.65 2.915)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.69 -2.896)
			(end 2.69 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.69 1.04)
			(end 2.69 2.896)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.73 -2.876)
			(end 2.73 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.73 1.04)
			(end 2.73 2.876)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.77 -2.855)
			(end 2.77 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.77 1.04)
			(end 2.77 2.855)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.81 -2.834)
			(end 2.81 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.81 1.04)
			(end 2.81 2.834)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.85 -2.812)
			(end 2.85 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.85 1.04)
			(end 2.85 2.812)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.89 -2.789)
			(end 2.89 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.89 1.04)
			(end 2.89 2.789)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.93 -2.765)
			(end 2.93 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.93 1.04)
			(end 2.93 2.765)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.97 -2.741)
			(end 2.97 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 2.97 1.04)
			(end 2.97 2.741)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.01 -2.716)
			(end 3.01 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.01 1.04)
			(end 3.01 2.716)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.05 -2.69)
			(end 3.05 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.05 1.04)
			(end 3.05 2.69)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.09 -2.663)
			(end 3.09 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.09 1.04)
			(end 3.09 2.663)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.13 -2.636)
			(end 3.13 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.13 1.04)
			(end 3.13 2.636)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.17 -2.607)
			(end 3.17 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.17 1.04)
			(end 3.17 2.607)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.21 -2.577)
			(end 3.21 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.21 1.04)
			(end 3.21 2.577)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.25 -2.547)
			(end 3.25 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.25 1.04)
			(end 3.25 2.547)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.29 -2.516)
			(end 3.29 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.29 1.04)
			(end 3.29 2.516)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.33 -2.483)
			(end 3.33 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.33 1.04)
			(end 3.33 2.483)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.37 -2.45)
			(end 3.37 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.37 1.04)
			(end 3.37 2.45)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.41 -2.415)
			(end 3.41 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.41 1.04)
			(end 3.41 2.415)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.45 -2.379)
			(end 3.45 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.45 1.04)
			(end 3.45 2.379)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.49 -2.342)
			(end 3.49 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.49 1.04)
			(end 3.49 2.342)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.53 -2.304)
			(end 3.53 -1.04)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.53 1.04)
			(end 3.53 2.304)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.57 -2.264)
			(end 3.57 2.264)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.61 -2.223)
			(end 3.61 2.223)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.65 -2.181)
			(end 3.65 2.181)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.69 -2.137)
			(end 3.69 2.137)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.73 -2.091)
			(end 3.73 2.091)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.77 -2.044)
			(end 3.77 2.044)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.81 -1.995)
			(end 3.81 1.995)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.85 -1.943)
			(end 3.85 1.943)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.89 -1.89)
			(end 3.89 1.89)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.93 -1.834)
			(end 3.93 1.834)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.97 -1.775)
			(end 3.97 1.775)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.01 -1.714)
			(end 4.01 1.714)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.05 -1.649)
			(end 4.05 1.649)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.09 -1.581)
			(end 4.09 1.581)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.13 -1.509)
			(end 4.13 1.509)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.17 -1.432)
			(end 4.17 1.432)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.21 -1.35)
			(end 4.21 1.35)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.25 -1.261)
			(end 4.25 1.261)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.29 -1.165)
			(end 4.29 1.165)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.33 -1.058)
			(end 4.33 1.058)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.37 -0.939)
			(end 4.37 0.939)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.41 -0.801)
			(end 4.41 0.801)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.45 -0.633)
			(end 4.45 0.633)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 4.49 -0.402)
			(end 4.49 0.402)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_circle
			(center 1.25 0)
			(end 4.52 0)
			(stroke
				(width 0.12)
				(type solid)
			)
			(fill no)
			(layer "F.SilkS")
		)
		(fp_circle
			(center 1.25 0)
			(end 4.65 0)
			(stroke
				(width 0.05)
				(type solid)
			)
			(fill no)
			(layer "F.CrtYd")
		)
		(fp_line
			(start -1.443972 -1.3735)
			(end -0.813972 -1.3735)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start -1.128972 -1.6885)
			(end -1.128972 -1.0585)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_circle
			(center 1.25 0)
			(end 4.4 0)
			(stroke
				(width 0.1)
				(type solid)
			)
			(fill no)
			(layer "F.Fab")
		)
		(fp_text user "${REFERENCE}"
			(at 1.25 0 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(pad "1" thru_hole roundrect
			(at 0 0)
			(size 1.6 1.6)
			(drill 0.8)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
			(roundrect_rratio 0.15625)
		)
		(pad "2" thru_hole circle
			(at 2.5 0)
			(size 1.6 1.6)
			(drill 0.8)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(embedded_fonts no)
		(model "${KICAD10_3DMODEL_DIR}/Capacitor_THT.3dshapes/CP_Radial_D6.3mm_P2.50mm.step"
			(offset
				(xyz 0 0 0)
			)
			(scale
				(xyz 1 1 1)
			)
			(rotate
				(xyz 0 0 0)
			)
		)
	)

	(footprint "Capacitor_THT:C_Disc_D6.0mm_W2.5mm_P5.00mm"
		(version 20260206)
		(generator "kicad-footprint-generator")
		(layer "F.Cu")
		(descr "C, Disc series, Radial, pin pitch=5.00mm, diameter*width=6*2.5mm^2, Capacitor, http://cdn-reichelt.de/documents/datenblatt/B300/DS_KERKO_TC.pdf")
		(tags "C Disc series Radial pin pitch 5.00mm diameter 6mm width 2.5mm Capacitor")
		(property "Reference" "REF**"
			(at 2.5 -2.5 0)
			(layer "F.SilkS")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Value" "C_Disc_D6.0mm_W2.5mm_P5.00mm"
			(at 2.5 2.5 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "KiLib_Generator" "capacitor/THT/other"
			(at 0 0 0)
			(layer "F.SilkS")
			(hide yes)
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(attr through_hole)
		(duplicate_pad_numbers_are_jumpers no)
		(fp_line
			(start -0.62 -1.37)
			(end 5.62 -1.37)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -0.62 -0.835)
			(end -0.62 -1.37)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -0.62 1.37)
			(end -0.62 0.835)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.62 -1.37)
			(end 5.62 -0.835)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.62 0.835)
			(end 5.62 1.37)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 5.62 1.37)
			(end -0.62 1.37)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_rect
			(start -1.05 -1.5)
			(end 6.05 1.5)
			(stroke
				(width 0.05)
				(type solid)
			)
			(fill no)
			(layer "F.CrtYd")
		)
		(fp_rect
			(start -0.5 -1.25)
			(end 5.5 1.25)
			(stroke
				(width 0.1)
				(type solid)
			)
			(fill no)
			(layer "F.Fab")
		)
		(fp_text user "${REFERENCE}"
			(at 2.5 0 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(pad "1" thru_hole circle
			(at 0 0)
			(size 1.6 1.6)
			(drill 0.8)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(pad "2" thru_hole circle
			(at 5 0)
			(size 1.6 1.6)
			(drill 0.8)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(embedded_fonts no)
		(model "${KICAD10_3DMODEL_DIR}/Capacitor_THT.3dshapes/C_Disc_D6.0mm_W2.5mm_P5.00mm.step"
			(offset
				(xyz 0 0 0)
			)
			(scale
				(xyz 1 1 1)
			)
			(rotate
				(xyz 0 0 0)
			)
		)
	)

	(footprint "Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm"
		(version 20260206)
		(generator "kicad-footprint-generator")
		(layer "F.Cu")
		(descr "C, Disc series, Radial, pin pitch=2.50mm, diameter*width=3.8*2.6mm^2, Capacitor, http://www.vishay.com/docs/45233/krseries.pdf")
		(tags "C Disc series Radial pin pitch 2.50mm diameter 3.8mm width 2.6mm Capacitor")
		(property "Reference" "REF**"
			(at 1.25 -2.55 0)
			(layer "F.SilkS")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Value" "C_Disc_D3.8mm_W2.6mm_P2.50mm"
			(at 1.25 2.55 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "KiLib_Generator" "capacitor/THT/other"
			(at 0 0 0)
			(layer "F.SilkS")
			(hide yes)
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(attr through_hole)
		(duplicate_pad_numbers_are_jumpers no)
		(fp_line
			(start -0.77 -1.42)
			(end 3.27 -1.42)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -0.77 -0.699)
			(end -0.77 -1.42)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start -0.77 1.42)
			(end -0.77 0.699)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.27 -1.42)
			(end 3.27 -0.699)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.27 0.699)
			(end 3.27 1.42)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.27 1.42)
			(end -0.77 1.42)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_rect
			(start -1.05 -1.55)
			(end 3.55 1.55)
			(stroke
				(width 0.05)
				(type solid)
			)
			(fill no)
			(layer "F.CrtYd")
		)
		(fp_rect
			(start -0.65 -1.3)
			(end 3.15 1.3)
			(stroke
				(width 0.1)
				(type solid)
			)
			(fill no)
			(layer "F.Fab")
		)
		(fp_text user "${REFERENCE}"
			(at 1.25 0 0)
			(layer "F.Fab")
			(effects
				(font
					(size 0.76 0.76)
					(thickness 0.114)
				)
			)
		)
		(pad "1" thru_hole circle
			(at 0 0)
			(size 1.6 1.6)
			(drill 0.8)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(pad "2" thru_hole circle
			(at 2.5 0)
			(size 1.6 1.6)
			(drill 0.8)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(embedded_fonts no)
		(model "${KICAD10_3DMODEL_DIR}/Capacitor_THT.3dshapes/C_Disc_D3.8mm_W2.6mm_P2.50mm.step"
			(offset
				(xyz 0 0 0)
			)
			(scale
				(xyz 1 1 1)
			)
			(rotate
				(xyz 0 0 0)
			)
		)
	)

	(footprint "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal"
		(version 20260206)
		(generator "kicad-footprint-generator")
		(layer "F.Cu")
		(descr "Diode, DO-41_SOD81 series, Axial, Horizontal, pin pitch=10.16mm, length*diameter=5.2*2.7mm^2, https://www.diodes.com/assets/Package-Files/DO-41-Plastic.pdf")
		(tags "Diode DO-41_SOD81 series Axial Horizontal pin pitch 10.16mm  length 5.2mm diameter 2.7mm")
		(property "Reference" "REF**"
			(at 5.08 -2.47 0)
			(layer "F.SilkS")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Value" "D_DO-41_SOD81_P10.16mm_Horizontal"
			(at 5.08 2.47 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "KiLib_Generator" "diode/THT"
			(at 0 0 0)
			(layer "F.SilkS")
			(hide yes)
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(attr through_hole)
		(duplicate_pad_numbers_are_jumpers no)
		(fp_line
			(start 1.34 0)
			(end 2.36 0)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.14 -1.47)
			(end 3.14 1.47)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.26 -1.47)
			(end 3.26 1.47)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 3.38 -1.47)
			(end 3.38 1.47)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 8.82 0)
			(end 7.8 0)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_rect
			(start 2.36 -1.47)
			(end 7.8 1.47)
			(stroke
				(width 0.12)
				(type solid)
			)
			(fill no)
			(layer "F.SilkS")
		)
		(fp_rect
			(start -1.35 -1.6)
			(end 11.51 1.6)
			(stroke
				(width 0.05)
				(type solid)
			)
			(fill no)
			(layer "F.CrtYd")
		)
		(fp_line
			(start 0 0)
			(end 2.48 0)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start 3.16 -1.35)
			(end 3.16 1.35)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start 3.26 -1.35)
			(end 3.26 1.35)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start 3.36 -1.35)
			(end 3.36 1.35)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start 10.16 0)
			(end 7.68 0)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_rect
			(start 2.48 -1.35)
			(end 7.68 1.35)
			(stroke
				(width 0.1)
				(type solid)
			)
			(fill no)
			(layer "F.Fab")
		)
		(fp_text user "K"
			(at 0 -2.1 0)
			(layer "F.SilkS")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(fp_text user "K"
			(at 0 -2.1 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(fp_text user "${REFERENCE}"
			(at 5.47 0 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(pad "1" thru_hole roundrect
			(at 0 0)
			(size 2.2 2.2)
			(drill 1.1)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
			(roundrect_rratio 0.113636)
		)
		(pad "2" thru_hole circle
			(at 10.16 0)
			(size 2.2 2.2)
			(drill 1.1)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(embedded_fonts no)
		(model "${KICAD10_3DMODEL_DIR}/Diode_THT.3dshapes/D_DO-41_SOD81_P10.16mm_Horizontal.step"
			(offset
				(xyz 0 0 0)
			)
			(scale
				(xyz 1 1 1)
			)
			(rotate
				(xyz 0 0 0)
			)
		)
	)

	(footprint "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal"
		(version 20260206)
		(generator "kicad-footprint-generator")
		(layer "F.Cu")
		(descr "Resistor, Axial_DIN0204 series, Axial, Horizontal, pin pitch=5.08mm, 0.167W, length*diameter=3.6*1.6mm^2, http://cdn-reichelt.de/documents/datenblatt/B400/1_4W%23YAG.pdf")
		(tags "Resistor Axial_DIN0204 series Axial Horizontal pin pitch 5.08mm 0.167W length 3.6mm diameter 1.6mm")
		(property "Reference" "REF**"
			(at 2.54 -1.92 0)
			(layer "F.SilkS")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "Value" "R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal"
			(at 2.54 1.92 0)
			(layer "F.Fab")
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(property "KiLib_Generator" "resistor/THT"
			(at 0 0 0)
			(layer "F.SilkS")
			(hide yes)
			(effects
				(font
					(size 1 1)
					(thickness 0.15)
				)
			)
		)
		(attr through_hole)
		(duplicate_pad_numbers_are_jumpers no)
		(fp_line
			(start 0.62 -0.92)
			(end 4.46 -0.92)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_line
			(start 0.62 0.92)
			(end 4.46 0.92)
			(stroke
				(width 0.12)
				(type solid)
			)
			(layer "F.SilkS")
		)
		(fp_rect
			(start -0.95 -1.05)
			(end 6.03 1.05)
			(stroke
				(width 0.05)
				(type solid)
			)
			(fill no)
			(layer "F.CrtYd")
		)
		(fp_line
			(start 0 0)
			(end 0.74 0)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_line
			(start 5.08 0)
			(end 4.34 0)
			(stroke
				(width 0.1)
				(type solid)
			)
			(layer "F.Fab")
		)
		(fp_rect
			(start 0.74 -0.8)
			(end 4.34 0.8)
			(stroke
				(width 0.1)
				(type solid)
			)
			(fill no)
			(layer "F.Fab")
		)
		(fp_text user "${REFERENCE}"
			(at 2.54 0 0)
			(layer "F.Fab")
			(effects
				(font
					(size 0.72 0.72)
					(thickness 0.108)
				)
			)
		)
		(pad "1" thru_hole circle
			(at 0 0)
			(size 1.4 1.4)
			(drill 0.7)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(pad "2" thru_hole circle
			(at 5.08 0)
			(size 1.4 1.4)
			(drill 0.7)
			(layers "*.Cu" "*.Mask")
			(remove_unused_layers no)
		)
		(embedded_fonts no)
		(model "${KICAD10_3DMODEL_DIR}/Resistor_THT.3dshapes/R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal.step"
			(offset
				(xyz 0 0 0)
			)
			(scale
				(xyz 1 1 1)
			)
			(rotate
				(xyz 0 0 0)
			)
		)
	)
