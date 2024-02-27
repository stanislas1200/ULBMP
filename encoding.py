from image import Image
from pixel import Pixel

MB = "\u001b[38;2;44;236;246m"
PINK = "\u001b[38;2;255;126;219m"
C = "\u001b[0m"

# TODO : map version to method

class Encoder:
	"""Encodes an image to the ULBMP format."""
	def __init__(self, img: Image, version: int=1, **kwargs): # TODO : version 3, 4 # FIXME : asked __init__(self, img: Image)
		self.img = img
		self.version = version
		self.depth = kwargs.get('depth', 0)
		self.rle: bool = kwargs.get('rle', 0)
		self.colors = kwargs.get('colors', 0)

	def write_pixel(self, file, pixel: Pixel, ppb: int=1) -> None:
		"""Write a pixel to the file.
		:param file: The file to write to. This should be a file-like object (i.e., an object that has a `write()` method).
		"""
		file.write(pixel.red.to_bytes(ppb, byteorder='little'))
		file.write(pixel.green.to_bytes(ppb, byteorder='little'))
		file.write(pixel.blue.to_bytes(ppb, byteorder='little'))

	def v1(self, file) -> None:
		"""version 1.0 of the ULBMP format"""
		for pixel in self.img.pixels:
			self.write_pixel(file, pixel)

	def v2(self, file, ppb: int=1) -> None:
		"""version 2.0 of the ULBMP format"""
		i = 0

		while i < len(self.img.pixels):
			pixel = self.img.pixels[i]
			run_length = 1

			while (i + run_length) < len(self.img.pixels) and self.img.pixels[i + run_length] == pixel: # TODO : check if run_length < 255 1 byte
				run_length += 1

			file.write(run_length.to_bytes(1, byteorder='little'))
			self.write_pixel(file, pixel, ppb)
			i += run_length

	def v3(self, file) -> None:
		"""version 3.0 of the ULBMP format"""
		self.colors = list(self.colors)
		# print(self.depth, self.rle, self.colors)
		#chekc valid values
		if (self.depth < 1 or self.depth > 24):
			raise Exception('Invalid depth')
		if (self.depth <= 8 and len(self.colors) > (1 << self.depth)):
			raise Exception(f'Invalid number of colors. \nGot {len(self.colors)}\nExpected {1 << self.depth}')
		if (self.depth <= 8): # TODO : check if always works + rle
			pixels_per_byte = 8 // self.depth
			total_pixels = self.img.width * self.img.height
			pixels = self.img.pixels
			
			for i in range(0, total_pixels, pixels_per_byte):
				byte = 0

				for j in range(pixels_per_byte):
					if (i + j >= total_pixels):
						break
					print(self.colors.index(pixels[i + j]))
					byte |= (self.colors.index(pixels[i + j]) << ((pixels_per_byte - 1 - j) * self.depth))
				
				file.write(byte.to_bytes(1, byteorder='little'))
		else:
			if (not self.rle):
				self.v1(file)
			else:
				self.v2(file)




	def save_to(self, path: str) -> None: #TODO: Implement this method using ULBMP any version
		"""Save the image to a file in the ULBMP format."""
		with open(path, 'wb') as file:
			file.write(b"ULBMP")
			file.write(self.version.to_bytes(1, byteorder='little')) # 1.0 version
			if (self.version == 3):
				if (self.depth <= 8):
					file.write((14 + len(self.colors) * 3).to_bytes(2, byteorder='little'))
				else:
					file.write((14).to_bytes(2, byteorder='little'))
			else:
				file.write((12).to_bytes(2, byteorder='little')) # header size 12 little endian
			file.write(self.img.width.to_bytes(2, byteorder='little'))
			file.write(self.img.height.to_bytes(2, byteorder='little'))

			match self.version:
				case 1:
					self.v1(file)
				case 2:
					self.v2(file)
				case 3:
					file.write(self.depth.to_bytes(1, byteorder='little'))
					file.write(self.rle.to_bytes(1, byteorder='little'))
					if (self.depth <= 8):
						for color in self.colors:
							self.write_pixel(file, color)
					self.v3(file)
				case _:
					raise Exception(f'Unsupported version {self.version}') # TODO : raise before writing

class Decoder:
	"""Decodes an image from the ULBMP format."""
	def load_from(self, path: str) -> Image: #TODO: Implement this method using ULBMP any version
		"""Load an image from a file in the ULBMP format."""
		if (path.endswith('.ulbmp') == False):
			raise Exception('Invalid file format')
		
		# read bytes from file
		with open(path, 'rb') as file:
			bytes = file.read()
			self.read_header(bytes)
			print(self)
			pixels = self.read_pixels(bytes)
			return Image(self.width, self.height, pixels)

	def v1(self, bytes: bytes) -> list[Pixel]:
		"""version 1.0 of the ULBMP format"""
		pixels = []

		for i in range(self.header_len, len(bytes), 3):
			pixels.append(Pixel(bytes[i], bytes[i+1], bytes[i+2]))

		return pixels
	
	def v2(self, bytes: bytes) -> list[Pixel]:
		"""version 2.0 of the ULBMP format"""
		pixels = []

		for i in range(self.header_len, len(bytes), 4):
			for j in range(bytes[i]):
				pixels.append(Pixel(bytes[i+1], bytes[i+2], bytes[i+3]))

		return pixels
	
	def v3(self, bytes: bytes) -> list[Pixel]:
		"""version 3.0 of the ULBMP format
		
		00000000  55 4c 42 4d 50 | 03 | 0e 00 | 00 01 | 03 00 | 18 | 00 | ff 00  |ULBMP...........|
					U  L  B  M  P  | 3  | 14    | 256   | 3     | 24 | 0 | 
					FORMAT | VERSION | HEADER | WIDTH | HEIGHT | depth | COMPRESSION | PALETTE | PIXELS
					
		00000010  00 fe 00 00 fd 00 00 fc  00 00 fb 00 00 fa 00 00  |................|
		"""
		pixels = []

		if (self.depth <= 8):
			pixels_per_byte = 8 // self.depth
			total_pixels = self.width * self.height

			for i in range(self.header_len, len(bytes)):
				byte = bytes[i]

				for j in range(pixels_per_byte - 1, -1, -1):
					if len(pixels) >= total_pixels:
						break

					pixel_index = (byte >> (j * self.depth)) & ((1 << self.depth) - 1)
					# print(pixel_index, self.palette[pixel_index])
					pixel = self.palette[pixel_index]
					pixels.append(pixel)
		else:
			bytes_per_pixel = self.depth // 8  # Number of bytes per pixel

			if (self.compression):
				bytes_per_pixel += 1

			for i in range(self.header_len, len(bytes), bytes_per_pixel):
				if ((self.depth == 8 or self.depth == 24) and self.compression): # RLE
					for j in range(bytes[i]):
						pixels.append(Pixel(bytes[i+1], bytes[i+2], bytes[i+3]))
				else:
					pixels.append(Pixel(bytes[i], bytes[i+1], bytes[i+2]))

		# print(len(pixels))
		# print(self.width * self.height)
		return pixels

	def read_pixels(self, bytes: bytes) -> list[Pixel]:
		"""Read the pixels from the file."""
		pixels = []

		match self.version:
			case 1:
				pixels = self.v1(bytes)
			case 2:
				pixels = self.v2(bytes)
			case 3:
				pixels = self.v3(bytes)
			case _:
				raise Exception(f'Unsupported version {self.version}')
		return pixels

	def read_header(self, bytes: bytes) -> None:
		self.depth = 0
		self.compression = 0
		self.palette = None
		data_size = len(bytes)

		if (data_size < 12): # Format + Version + Header size + width + height | 15 for 1 pixel ?
			raise Exception('Invalid file format')
		
		self.format = bytes[0:5].decode('utf-8')
		if (self.format != "ULBMP"):
			raise Exception('Invalid file format')
		
		self.version = bytes[5]
		self.header_len = int.from_bytes(bytes[6:8], byteorder='little')
		self.width = int.from_bytes(bytes[8:10], byteorder='little')
		self.height = int.from_bytes(bytes[10:12], byteorder='little')
		
		if (self.width <= 0 or self.height <= 0):
			raise Exception('Invalid dimensions')
		
		match self.version:
			case 1:
				if (self.header_len < 12):
					raise Exception('Invalid header size')
			case 2:
				if (self.header_len < 12):
					raise Exception('Invalid header size')
			case 3:
				if (self.header_len < 12):
					raise Exception('Invalid header size')
				self.depth = bytes[12]
				self.compression = bytes[13]
				self.palette = []
				for i in range(14, self.header_len, 3):
					self.palette.append(Pixel(bytes[i], bytes[i+1], bytes[i+2]))
				# print(self.depth, self.compression, self.palette)

			case 4:
				if (self.header_len < 12):
					raise Exception('Invalid header size')
			case _:
				raise Exception(f'Unsupported version {self.version}') 
		# TODO : check valid values


	def __repr__(self) -> str: # not asked
		return f"Image:\n {PINK}- Format: {MB}{self.format}\n {PINK}- Version: {MB}{self.version}\n {PINK}- Header size: {MB}{self.header_len}\n \
{PINK}- width: {MB}{self.width}\n {PINK}- height: {MB}{self.height}\n \
{PINK}- depth: {MB}{self.depth}\n {PINK}- compression: {MB}{self.compression}\n{C}{self.palette}\n"

