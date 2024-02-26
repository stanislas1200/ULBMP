def rgb(r, g, b): return f"\u001b[38;2;{r};{g};{b}m" # not asked

class Pixel:
	"""Represents a pixel in an image with a given red, green, and blue value."""
	def __init__(self, red: int, green: int, blue: int):
		if (red < 0 or red > 255 or green < 0 or green > 255 or blue < 0 or blue > 255):
			raise Exception('Invalid color value')
		
		self._red = red
		self._green = green
		self._blue = blue

	def __str__(self): # not asked
		return f"{rgb(self._red, self._green, self._blue)}██\u001b[0m"

	def __repr__(self): # not asked
		return str(self)
	
	def __eq__(self, other: 'Pixel'):
		if isinstance(other, Pixel):
			return self._red == other._red and self._green == other._green and self._blue == other._blue
		return False
	
	@property
	def red(self) -> int:
		return self._red
	
	@property
	def green(self) -> int:
		return self._green
	
	@property
	def blue(self) -> int:
		return self._blue
