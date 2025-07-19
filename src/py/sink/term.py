from typing import ClassVar
import os

# --
# Defines colors

# -- prompt
# Can you write a Python function `termcolor(r:int, g:int, b:int, bold:bool=False, invert:bool=False)->str`
# that takes `r` as red, `g` as green, `b` as blue in 8bit integer (0-255) and returns
# a string that when printed will setup the terminal to output text in the color
# by defined `(r,g,b)` in sRGB space, with the text in bold when `bold` is `True`,
# and inverted if `invert` is `True`.
NO_COLOR = "NO_COLOR" in os.environ


def termcolor(r: int, g: int, b: int, bold: bool = False, invert: bool = False) -> str:
	"""Returns an ANSI escape sequence for setting the terminal color.

	Args:
	        r: An integer between 0 and 255 representing the red component of the color.
	        g: An integer between 0 and 255 representing the green component of the color.
	        b: An integer between 0 and 255 representing the blue component of the color.
	        bold: A boolean indicating whether the text should be bold.
	        invert: A boolean indicating whether the background and text colors should be inverted.

	Returns:
	        A string containing the ANSI escape sequence to set the terminal color.

	"""
	if NO_COLOR:
		return ""

	# Start with the escape code for setting the foreground color
	escape_sequence = f"\033[38;2;{r};{g};{b}"

	# Add escape code for setting the background color to be inverted, if specified
	if invert:
		escape_sequence += ";7"

	# Add escape code for setting the text to be bold, if specified
	if bold:
		escape_sequence += ";1"

	# End the escape sequence
	escape_sequence += "m"

	# Return the complete escape sequence
	return escape_sequence


# -- prompt
#  Can you create a class now that is like so:
#
# ```
# class Colors:
#    AliceBlue:ClassVar[str] = termcolor(240,248,255)
# ```
#
# where `Colors` has class variables for each color of the HTML standard colors?


class TermFont:
	Bold: ClassVar[str] = "\033[1m"
	Invert: ClassVar[str] = "\033[7m"
	Reset: ClassVar[str] = "\033[0m"


class TermColor:
	# Define class variables for each HTML standard color using the termcolor function
	AliceBlue: ClassVar[str] = termcolor(240, 248, 255)
	AntiqueWhite: ClassVar[str] = termcolor(250, 235, 215)
	Aqua: ClassVar[str] = termcolor(0, 255, 255)
	Aquamarine: ClassVar[str] = termcolor(127, 255, 212)
	Azure: ClassVar[str] = termcolor(240, 255, 255)
	Beige: ClassVar[str] = termcolor(245, 245, 220)
	Bisque: ClassVar[str] = termcolor(255, 228, 196)
	Black: ClassVar[str] = termcolor(0, 0, 0)
	BlanchedAlmond: ClassVar[str] = termcolor(255, 235, 205)
	Blue: ClassVar[str] = termcolor(0, 0, 255)
	BlueViolet: ClassVar[str] = termcolor(138, 43, 226)
	Brown: ClassVar[str] = termcolor(165, 42, 42)
	BurlyWood: ClassVar[str] = termcolor(222, 184, 135)
	CadetBlue: ClassVar[str] = termcolor(95, 158, 160)
	Chartreuse: ClassVar[str] = termcolor(127, 255, 0)
	Chocolate: ClassVar[str] = termcolor(210, 105, 30)
	Coral: ClassVar[str] = termcolor(255, 127, 80)
	CornflowerBlue: ClassVar[str] = termcolor(100, 149, 237)
	Cornsilk: ClassVar[str] = termcolor(255, 248, 220)
	Crimson: ClassVar[str] = termcolor(220, 20, 60)
	Cyan: ClassVar[str] = termcolor(0, 255, 255)
	DarkBlue: ClassVar[str] = termcolor(0, 0, 139)
	DarkCyan: ClassVar[str] = termcolor(0, 139, 139)
	DarkGoldenRod: ClassVar[str] = termcolor(184, 134, 11)
	DarkGray: ClassVar[str] = termcolor(169, 169, 169)
	DarkGrey: ClassVar[str] = termcolor(169, 169, 169)
	DarkGreen: ClassVar[str] = termcolor(0, 100, 0)
	DarkKhaki: ClassVar[str] = termcolor(189, 183, 107)
	DarkMagenta: ClassVar[str] = termcolor(139, 0, 139)
	DarkOliveGreen: ClassVar[str] = termcolor(85, 107, 47)
	DarkOrange: ClassVar[str] = termcolor(255, 140, 0)
	DarkOrchid: ClassVar[str] = termcolor(153, 50, 204)
	DarkRed: ClassVar[str] = termcolor(139, 0, 0)
	DarkSalmon: ClassVar[str] = termcolor(233, 150, 122)
	DarkSeaGreen: ClassVar[str] = termcolor(143, 188, 143)
	DarkSlateBlue: ClassVar[str] = termcolor(72, 61, 139)
	DarkSlateGray: ClassVar[str] = termcolor(47, 79, 79)
	DarkSlateGrey: ClassVar[str] = termcolor(47, 79, 79)
	DarkTurquoise: ClassVar[str] = termcolor(0, 206, 209)
	DarkViolet: ClassVar[str] = termcolor(148, 0, 211)
	DeepPink: ClassVar[str] = termcolor(255, 20, 147)
	DeepSkyBlue: ClassVar[str] = termcolor(0, 191, 255)
	DimGray: ClassVar[str] = termcolor(105, 105, 105)
	DimGrey: ClassVar[str] = termcolor(105, 105, 105)
	DodgerBlue: ClassVar[str] = termcolor(30, 144, 255)
	FireBrick: ClassVar[str] = termcolor(178, 34, 34)
	FloralWhite: ClassVar[str] = termcolor(255, 250, 240)
	ForestGreen: ClassVar[str] = termcolor(34, 139, 34)
	Fuchsia: ClassVar[str] = termcolor(255, 0, 255)
	Gainsboro: ClassVar[str] = termcolor(220, 220, 220)
	GhostWhite: ClassVar[str] = termcolor(248, 248, 255)
	Gold: ClassVar[str] = termcolor(255, 215, 0)
	GoldenRod: ClassVar[str] = termcolor(218, 165, 32)
	Gray: ClassVar[str] = termcolor(128, 128, 128)
	Grey: ClassVar[str] = termcolor(128, 128, 128)
	Green: ClassVar[str] = termcolor(0, 128, 0)
	GreenYellow: ClassVar[str] = termcolor(173, 255, 47)
	HoneyDew: ClassVar[str] = termcolor(240, 255, 240)
	HotPink: ClassVar[str] = termcolor(255, 105, 180)
	IndianRed: ClassVar[str] = termcolor(205, 92, 92)
	Indigo: ClassVar[str] = termcolor(75, 0, 130)
	Ivory: ClassVar[str] = termcolor(255, 255, 240)
	Khaki: ClassVar[str] = termcolor(240, 230, 140)
	Lavender: ClassVar[str] = termcolor(230, 230, 250)
	LavenderBlush: ClassVar[str] = termcolor(255, 240, 245)
	LawnGreen: ClassVar[str] = termcolor(124, 252, 0)
	LemonChiffon: ClassVar[str] = termcolor(255, 250, 205)
	LightBlue: ClassVar[str] = termcolor(173, 216, 230)
	LightCoral: ClassVar[str] = termcolor(240, 128, 128)
	LightCyan: ClassVar[str] = termcolor(224, 255, 255)
	LightGoldenRodYellow: ClassVar[str] = termcolor(250, 250, 210)
	LightGray: ClassVar[str] = termcolor(211, 211, 211)
	LightGrey: ClassVar[str] = termcolor(211, 211, 211)
	LightGreen: ClassVar[str] = termcolor(144, 238, 144)
	LightPink: ClassVar[str] = termcolor(255, 182, 193)
	LightSalmon: ClassVar[str] = termcolor(255, 160, 122)
	LightSeaGreen: ClassVar[str] = termcolor(32, 178, 170)
	LightSkyBlue: ClassVar[str] = termcolor(135, 206, 250)
	LightSlateGray: ClassVar[str] = termcolor(119, 136, 153)
	LightSlateGrey: ClassVar[str] = termcolor(119, 136, 153)
	LightSteelBlue: ClassVar[str] = termcolor(176, 196, 222)
	LightYellow: ClassVar[str] = termcolor(255, 255, 224)
	Lime: ClassVar[str] = termcolor(0, 255, 0)
	LimeGreen: ClassVar[str] = termcolor(50, 205, 50)
	Linen: ClassVar[str] = termcolor(250, 240, 230)
	Magenta: ClassVar[str] = termcolor(255, 0, 255)
	Maroon: ClassVar[str] = termcolor(128, 0, 0)
	MediumAquaMarine: ClassVar[str] = termcolor(102, 205, 170)
	MediumBlue: ClassVar[str] = termcolor(0, 0, 205)
	MediumOrchid: ClassVar[str] = termcolor(186, 85, 211)
	MediumPurple: ClassVar[str] = termcolor(147, 112, 219)
	MediumSeaGreen: ClassVar[str] = termcolor(60, 179, 113)
	MediumSlateBlue: ClassVar[str] = termcolor(123, 104, 238)
	MediumSpringGreen: ClassVar[str] = termcolor(0, 250, 154)
	MediumTurquoise: ClassVar[str] = termcolor(72, 209, 204)
	MediumVioletRed: ClassVar[str] = termcolor(199, 21, 133)
	MidnightBlue: ClassVar[str] = termcolor(25, 25, 112)
	MintCream: ClassVar[str] = termcolor(245, 255, 250)
	MistyRose: ClassVar[str] = termcolor(255, 228, 225)
	Moccasin: ClassVar[str] = termcolor(255, 228, 181)
	NavajoWhite: ClassVar[str] = termcolor(255, 222, 173)
	Navy: ClassVar[str] = termcolor(0, 0, 128)
	OldLace: ClassVar[str] = termcolor(253, 245, 230)
	Olive: ClassVar[str] = termcolor(128, 128, 0)
	OliveDrab: ClassVar[str] = termcolor(107, 142, 35)
	Orange: ClassVar[str] = termcolor(255, 165, 0)
	OrangeRed: ClassVar[str] = termcolor(255, 69, 0)
	Orchid: ClassVar[str] = termcolor(218, 112, 214)
	PaleGoldenRod: ClassVar[str] = termcolor(238, 232, 170)
	PaleGreen: ClassVar[str] = termcolor(152, 251, 152)
	PaleTurquoise: ClassVar[str] = termcolor(175, 238, 238)
	PaleVioletRed: ClassVar[str] = termcolor(219, 112, 147)
	PapayaWhip: ClassVar[str] = termcolor(255, 239, 213)
	PeachPuff: ClassVar[str] = termcolor(255, 218, 185)
	Peru: ClassVar[str] = termcolor(205, 133, 63)
	Pink: ClassVar[str] = termcolor(255, 192, 203)
	Plum: ClassVar[str] = termcolor(221, 160, 221)
	PowderBlue: ClassVar[str] = termcolor(176, 224, 230)
	Purple: ClassVar[str] = termcolor(128, 0, 128)
	RebeccaPurple: ClassVar[str] = termcolor(102, 51, 153)
	Red: ClassVar[str] = termcolor(255, 0, 0)
	RosyBrown: ClassVar[str] = termcolor(188, 143, 143)
	RoyalBlue: ClassVar[str] = termcolor(65, 105, 225)
	SaddleBrown: ClassVar[str] = termcolor(139, 69, 19)
	Salmon: ClassVar[str] = termcolor(250, 128, 114)
	SandyBrown: ClassVar[str] = termcolor(244, 164, 96)
	SeaGreen: ClassVar[str] = termcolor(46, 139, 87)
	SeaShell: ClassVar[str] = termcolor(255, 245, 238)
	Sienna: ClassVar[str] = termcolor(160, 82, 45)
	Silver: ClassVar[str] = termcolor(192, 192, 192)
	SkyBlue: ClassVar[str] = termcolor(135, 206, 235)
	SlateBlue: ClassVar[str] = termcolor(106, 90, 205)
	SlateGray: ClassVar[str] = termcolor(112, 128, 144)
	SlateGrey: ClassVar[str] = termcolor(112, 128, 144)
	Snow: ClassVar[str] = termcolor(255, 250, 250)
	SpringGreen: ClassVar[str] = termcolor(0, 255, 127)
	SteelBlue: ClassVar[str] = termcolor(70, 130, 180)
	Tan: ClassVar[str] = termcolor(210, 180, 140)
	Teal: ClassVar[str] = termcolor(0, 128, 128)
	Thistle: ClassVar[str] = termcolor(216, 191, 216)
	Tomato: ClassVar[str] = termcolor(255, 99, 71)
	Turquoise: ClassVar[str] = termcolor(64, 224, 208)
	Violet: ClassVar[str] = termcolor(238, 130, 238)
	Wheat: ClassVar[str] = termcolor(245, 222, 179)
	White: ClassVar[str] = termcolor(255, 255, 255)
	WhiteSmoke: ClassVar[str] = termcolor(245, 245, 245)
	Yellow: ClassVar[str] = termcolor(255, 255, 0)
	YellowGreen: ClassVar[str] = termcolor(154, 205, 50)


# EOF
