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

		if (self.version == 3 and not self.colors): # For tester...
			'''get a set of colors from the image'''
			self.colors = set()

			for y in range(self.img.height):
				for x in range(self.img.width):
					pixel = self.img[x, y]
					self.colors.add(pixel)

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
		"""version 2.0 of the ULBMP format using Run-Length Encoding"""
		i = 0

		while i < len(self.img.pixels):
			pixel = self.img.pixels[i]
			run_length = 1
			# fix overflow run_length < 255
			while run_length < 255 and (i + run_length) < len(self.img.pixels) and self.img.pixels[i + run_length] == pixel: # TODO : check if run_length < 255 1 byte
				run_length += 1

			file.write(run_length.to_bytes(1, byteorder='little'))
			self.write_pixel(file, pixel, ppb)
			i += run_length

	def v3(self, file) -> None:
		"""version 3.0 of the ULBMP format"""
		self.colors = list(self.colors)
		
		if (self.depth < 1 or self.depth > 24):
			raise Exception('Invalid depth')
		if (self.depth <= 8 and len(self.colors) > (1 << self.depth)):
			raise Exception(f'Invalid number of colors. \nGot {len(self.colors)}\nExpected {1 << self.depth}')
		
		if (self.depth > 8):
			self.v1(file) if (not self.rle) else self.v2(file)
			return

		pixels_per_byte = 8 // self.depth
		total_pixels = self.img.width * self.img.height
		pixels = self.img.pixels

		if self.depth == 8 and self.rle:
			# Run-Length Encoding
			i = 0
			while i < total_pixels:
				run_val = pixels[i]
				run_len = 1

				while (i + run_len < total_pixels) and (pixels[i + run_len] == run_val) and (run_len < 255):
					run_len += 1

				file.write(run_len.to_bytes(1, byteorder='little'))  # Write run length
				file.write(self.colors.index(run_val).to_bytes(1, byteorder='little'))  # Write run value

				i += run_len
		else:
			for i in range(0, total_pixels, pixels_per_byte):
				byte = 0

				for j in range(pixels_per_byte):
					if (i + j >= total_pixels):
						break

					byte |= (self.colors.index(pixels[i + j]) << ((pixels_per_byte - 1 - j) * self.depth))
				
				file.write(byte.to_bytes(1, byteorder='little'))

	def v4_bigDiff(self, type, DM, D2, D3, file) -> None:
		"""version 4.0 Big Block of the ULBMP format using QOL approach"""
		byte = type | ((DM + 128) & 0b11110000) >> 4
		byte1 = ((DM + 128) & 0b00001111) << 4 | ((D2 - DM + 32) & 0b111100) >> 2
		byte2 = ((D2 - DM + 32) & 0b00000011) << 6 | ((D3 - DM + 32) & 0b00111111)
		# print(bin(byte), bin(byte1), bin(byte2))
		file.write(byte.to_bytes(1, byteorder='little'))
		file.write(byte1.to_bytes(1, byteorder='little'))
		file.write(byte2.to_bytes(1, byteorder='little'))

	def v4(self, file) -> None:
		"""version 4.0 of the ULBMP format using QOL approach"""
		oldPixel = Pixel(0, 0, 0)
		for pixel in self.img.pixels:
			Dr = pixel.red - oldPixel.red
			Dg = pixel.green - oldPixel.green
			Db = pixel.blue - oldPixel.blue
			if -2 <= Dr <= 1 and -2 <= Dg <= 1 and -2 <= Db <= 1:
				# ULBMP_SMALL_DIFF
				byte = (Dr + 2) << 4 | ((Dg + 2) << 2) | ((Db + 2))
				file.write(byte.to_bytes(1, byteorder='little'))
			elif (-32 <= Dg <= 31) and (-8 <= Dr - Dg <= 7 and -8 <= Db - Dg <= 7):
				# ULBMP_INTERMEDIATE_DIFF
				byte = (1 << 6) | (Dg + 32)
				byte1 = ((Dr - Dg + 8) << 4) | (Db - Dg + 8)
				file.write(byte.to_bytes(1, byteorder='little'))
				file.write(byte1.to_bytes(1, byteorder='little'))
			elif (-128 <= Dr <= 127) and (-32 <= Dg - Dr <= 31 and -32 <= Db - Dr <= 31):
				# ULBMP_BIG_DIFF red
				self.v4_bigDiff(0b10000000, Dr, Dg, Db, file)
			elif (-128 <= Dg <= 127) and (-32 <= Dr - Dg <= 31 and -32 <= Db - Dg <= 31):
				# ULBMP_BIG_DIFF green
				self.v4_bigDiff(0b10010000, Dg, Dr, Db, file)
			elif (-128 <= Db <= 127) and (-32 <= Dr - Db <= 31 and -32 <= Dg - Db <= 31):
				# ULBMP_BIG_DIFF blue
				self.v4_bigDiff(0b10100000, Db, Dr, Dg, file)
			else:
				# ULBMP_NEW_PIXEL
				file.write((0b11111111).to_bytes(1, byteorder='little'))
				self.write_pixel(file, pixel)
			oldPixel = pixel

	def save_to(self, path: str) -> None:
		"""Save the image to a file in the ULBMP format."""
		with open(path, 'wb') as file:
			# TODO : write header function
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
				case 4:
					self.v4(file)
				case _:
					raise Exception(f'Unsupported version {self.version}') # TODO : raise before writing

class Decoder: # for tester...
	@staticmethod
	def load_from(path: str) -> Image:
		"""Load an image from a file in the ULBMP format."""
		return Decoder1().load_from(path)

class Decoder1: # TODO : static methode
	"""Decodes an image from the ULBMP format."""
	def load_from(self, path: str) -> Image:
		"""Load an image from a file in the ULBMP format."""
		# if (path.endswith('.ulbmp') == False): # removed for tester...
		# 	raise Exception('Invalid file format')
		
		# read bytes from file
		with open(path, 'rb') as file:
			bytes = file.read()
			self.read_header(bytes)
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

		if self.depth == 8 and self.compression:
			# Run-Length Encoding with 8bpp
			i = self.header_len
			while i < len(bytes):
				# Get the run length and the pixel color index
				run_length = bytes[i]
				pixel_index = bytes[i + 1]

				# Append the pixel color to the pixels list run_length times
				pixel = self.palette[pixel_index]
				pixels.extend([pixel] * run_length)

				# Move to the next run
				i += 2
		elif (self.depth <= 8):
			pixels_per_byte = 8 // self.depth
			total_pixels = self.width * self.height

			for i in range(self.header_len, len(bytes)):
				byte = bytes[i]

				for j in range(pixels_per_byte - 1, -1, -1):
					if len(pixels) >= total_pixels:
						break

					pixel_index = (byte >> (j * self.depth)) & ((1 << self.depth) - 1)
					pixel = self.palette[pixel_index]
					pixels.append(pixel)
		else:
			bytes_per_pixel = self.depth // 8  # Number of bytes per pixel

			if (self.compression):
				bytes_per_pixel += 1

			for i in range(self.header_len, len(bytes), bytes_per_pixel):
				if (self.depth == 24 and self.compression): # RLE
					for j in range(bytes[i]):
						pixels.append(Pixel(bytes[i+1], bytes[i+2], bytes[i+3]))
				else:
					pixels.append(Pixel(bytes[i], bytes[i+1], bytes[i+2]))
		return pixels
	
	"""
	ULBMP_NEW_PIXEL
	ULBMP_SMALL_DIFF
	ULBMP_INTERMEDIATE_DIFF
	ULBMP_BIG_DIFF

	∆R := r2 −r1
	∆R,G := ∆R −∆G

	−2 ≤∆R, ∆G, ∆B ≤1 ULBMP_SMALL_DIFF. 2 bits
	−32 ≤∆G ≤31 et −8 ≤∆R,G, ∆B,G ≤7 ULBMP_INTERMEDIATE_DIFF différence d’intensité en vert 6 bits other 4bits
	−128 ≤∆R ≤127 et −32 ≤∆G,R, ∆B,R ≤31 ULBMP_BIG_DIFF type Red 8 bits other 6bits
	2 bits type, 8 bits diff, 2 * 6 bits span other channels 


	"""
	def v4(self, bytes: bytes) -> list[Pixel]:
		"""version 4.0 of the ULBMP format usign QOL approach"""
		pixels = []
		#P’ = Pixel noir = (0, 0, 0)
		oldPixel = Pixel(0, 0, 0)
		i = self.header_len
		while i < len(bytes):
			# read a byte
			byte = bytes[i]
			# get the type
			if (byte == 0b11111111 == 0b11111111): # OK
				# ULBMP_NEW_PIXEL
				# read 3 bytes
				oldPixel = Pixel(bytes[i+1], bytes[i+2], bytes[i+3])
				pixels.append(oldPixel)

				i += 3
			elif (byte & 0b11000000 == 0b00000000): # OK
				# ULBMP_SMALL_DIFF
				# 2 bits r, 2 bits g, 2 bits b
				Dr = ((byte & 0b00110000) >> 4) -2
				Dg = ((byte & 0b00001100) >> 2) -2
				Db = ((byte & 0b00000011)) -2
				# get the new pixel
				# print("Small " , oldPixel.red + Dr, oldPixel.green + Dg, oldPixel.blue + Db)
				newPixel = Pixel(oldPixel.red + Dr, oldPixel.green + Dg, oldPixel.blue + Db)
				# append the new pixel
				pixels.append(newPixel)
				# update the old pixel
				oldPixel = newPixel

				# i += 1
			elif (byte & 0b11000000 == 0b01000000): # OK
				# print("ULBMP_INTERMEDIATE_DIFF")
				# ULBMP_INTERMEDIATE_DIFF
				# 2 bits type, 6 bits diff, 4 bits 
				Dg = (byte & 0b00111111) - 32
				Drg = ((bytes[i+1] & 0b11110000) >> 4) - 8
				Dbg = (bytes[i+1] & 0b00001111) - 8
				# get delta
				Dr = Drg + Dg
				Db = Dbg + Dg
				# get the new pixel
				# print("IT " , oldPixel.red + Dr, oldPixel.green + Dg, oldPixel.blue + Db)
				newPixel = Pixel(oldPixel.red + Dr, oldPixel.green + Dg, oldPixel.blue + Db)
				# append the new pixel
				pixels.append(newPixel)
				# update the old pixel
				oldPixel = newPixel

				i += 1
			elif (byte & 0b10000000 == 0b10000000): # ok
				# print("ULBMP_BIG_DIFF")
				# ULBMP_BIG_DIFF
				big_diff = (((byte & 0b00001111) << 4) | ((bytes[i+1] & 0b11110000) >> 4)) - 128
				D1 = (((bytes[i+1] & 0b00001111) << 2) | ((bytes[i+2] & 0b11000000) >> 6)) - 32
				D2 = ((bytes[i+2] & 0b00111111)) - 32

				if (byte & 0b11110000 == 0b10100000):
					# blue
					Dr = D1 + big_diff
					Dg = D2 + big_diff
					Db = big_diff
				elif (byte & 0b11110000 == 0b10010000):
					# green
					Dr = D1 + big_diff
					Db = D2 + big_diff
					Dg = big_diff
				else:
					# red
					Dg = D1 + big_diff
					Db = D2 + big_diff
					Dr = big_diff
				# get the new pixel
				newPixel = Pixel(oldPixel.red + Dr, oldPixel.green + Dg, oldPixel.blue + Db)
				# append the new pixel
				pixels.append(newPixel)
				# update the old pixel
				oldPixel = newPixel

				i += 2
			# else :
			# 	print(f'Unsupported version 4.0 byte {bin(byte)}')
			i += 1
		# print(pixels)
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
			case 4:
				pixels = self.v4(bytes)
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
		
		match self.version: # TODO : remake checker
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

