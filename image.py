
from pixel import Pixel

class Image:
	"""
	Represents an image with a given width, height, and pixel values.
	"""
	def __init__(self, width: int, height: int, pixels: list[Pixel]):
		if width <= 0 or height <= 0:
			raise Exception('Invalid dimensions')
		if len(pixels) != width * height:
			raise Exception('Invalid number of pixels')
		
		self.width = width
		self.height = height
		self.pixels = pixels

	def __getitem__(self, pos: tuple[int, int]) -> Pixel:
		x, y = pos

		if x < 0 or x >= self.width or y < 0 or y >= self.height:
			raise IndexError('Index out of range')
		return self.pixels[y * self.width + x]

	def __setitem__(self, pos: tuple[int, int], pix: Pixel) -> None:
		x, y = pos

		if x < 0 or x >= self.width or y < 0 or y >= self.height:
			raise IndexError('Index out of range')
		self.pixels[y * self.width + x] = pix

	def __eq__(self, other: 'Image') -> bool:
		return self.width == other.width and self.height == other.height and self.pixels == other.pixels

	def __ne__(self, other: 'Image') -> bool: # not asked
		return not self == other
	
	def __str__(self) -> str: # not asked
		return f"Image: {self.width}x{self.height} \n{self.pixels}"

	def __repr__(self) -> str: # not asked
		return str(self)

