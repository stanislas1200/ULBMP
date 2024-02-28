import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QGraphicsScene, QGraphicsView
from PySide6.QtWidgets import QErrorMessage, QMessageBox, QInputDialog
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QColor, QPen


from encoding import Decoder, Encoder

from box import CustomDialog
import math
from PySide6.QtWidgets import QColorDialog

from image import Image
from pixel import Pixel

class MainWindow(QMainWindow):
	''' Main window of the application '''
	def __init__(self):
		super().__init__()

		self.setWindowTitle("ULBMP viewer")

		# Create a layout for the main window
		layout = QVBoxLayout()

		# Initialize the buttons
		self.init_buttons(layout)

		# Create a graphics view to display the image
		self.graphics_view = QGraphicsView()
		self.graphics_view.setMinimumWidth(640)
		self.graphics_view.setMinimumHeight(480)
		self.graphics_view.hide();
		layout.addWidget(self.graphics_view) 

		# Create a scene to hold the image
		self.scene = QGraphicsScene()
		self.graphics_view.setScene(self.scene)

		# Create a widget to hold the layout
		widget = QWidget()
		widget.setLayout(layout)
		self.setCentralWidget(widget)

		
	"""Drawing section"""
	# 	# Create a flag to track drawing state
	# 	self.drawing = False

	# 	# Create a pen for drawing
	# 	self.pen = QPen(Qt.black)
	# 	self.pen.setWidth(2)

	# 	# Connect mouse events to drawing functions
	# 	self.graphics_view.mousePressEvent = self.start_drawing
	# 	self.graphics_view.mouseMoveEvent = self.draw
	# 	self.graphics_view.mouseReleaseEvent = self.stop_drawing

	# 	# Create a color picker button
	# 	self.color_picker_button = QPushButton("Pick Color")
	# 	self.color_picker_button.clicked.connect(self.pick_color)
	# 	layout.addWidget(self.color_picker_button)

	# 	# Initialize the drawing color
	# 	self.drawing_color = Qt.black

	# def pick_color(self):
	# 	''' Open color picker dialog to choose drawing color '''
	# 	color = QColorDialog.getColor(self.drawing_color, self, "Pick Color")
	# 	if color.isValid():
	# 		self.drawing_color = color
	# 		self.pen.setColor(color)

	# def start_drawing(self, event=None):
	# 	''' Start drawing '''
	# 	self.drawing = True
	# 	if (event):
	# 		self.last_pos = event.pos()

	# def draw(self, event):
	# 	''' Draw on the image '''
	# 	if self.drawing:
	# 		current_pos = event.pos()
	# 		scene_pos = self.graphics_view.mapToScene(current_pos)
	# 		self.scene.addLine(self.last_pos.x(), self.last_pos.y(), scene_pos.x(), scene_pos.y(), self.pen)
	# 		self.last_pos = current_pos

	# def stop_drawing(self, event):
	# 	''' Stop drawing '''
	# 	self.drawing = False
	
	def init_buttons(self, layout: QVBoxLayout) -> None:
		''' Initialize the buttons '''
		load_button = QPushButton("Load Image")
		load_button.clicked.connect(self.load_image)
		load_button.setCursor(Qt.PointingHandCursor)
		load_button.setMinimumWidth(180)
		layout.addWidget(load_button)

		# Create a button to save the image
		self.save_button = QPushButton("Save Image")
		self.save_button.clicked.connect(self.save_image)
		layout.addWidget(self.save_button)
		self.save_button.setCursor(Qt.PointingHandCursor)
		self.save_button.setDisabled(True)

		# Create a button to convert
		self.convert_button = QPushButton("Convert Image")
		self.convert_button.clicked.connect(self.convert_image)
		layout.addWidget(self.convert_button)
		self.convert_button.setCursor(Qt.PointingHandCursor)
	
	def convert_image(self) -> None:
		''' Convert the image to a .ulbmp file '''
		file_dialog = QFileDialog()
		file_path, _ = file_dialog.getOpenFileName(self, "Load Image", "", "Image Files (*.png , *.jpg, *.jpeg, *.bmp)")
		
		if (file_path):
			try: 
				img = QImage(file_path)
				w = img.width()
				h = img.height()
				p = [Pixel(img.pixelColor(x, y).red(), img.pixelColor(x, y).green(), img.pixelColor(x, y).blue()) for y in range(h) for x in range(w)]
				img = Image(w, h, p)
				file_path = file_path.split(".")[0]
				Encoder(img, 1,).save_to(file_path + ".ulbmp")
				self.message("Success", "✔️ Image converted successfully!", "#00ED64", 3000)
			except Exception as e:
				self.error_message(f"Encoder error: {str(e)}")

	def error_message(self, message: str) -> None:
		''' Error message box '''
		error_dialog = QErrorMessage(self)
		error_dialog.setWindowTitle("Error")
		error_dialog.showMessage(message)
		error_dialog.setModal(True) # FIXME : not working and QError already is modal 
		error_dialog.exec()
	
	def message(self, title: str, message: str, color: str=None, timeout: int=0) -> QMessageBox:
		''' Custom message box '''
		message_box = QMessageBox()
		message_box.setWindowTitle(title)
		message_box.setText(message)
		message_box.setIcon(QMessageBox.NoIcon)
		if (color):
			message_box.setStyleSheet(f"QLabel{{color: {color}; font-weight: bold;}}")

		if (timeout > 0):
			timer = QTimer()
			timer.setSingleShot(True)
			timer.timeout.connect(message_box.close)
			timer.start(timeout)

		message_box.exec()
		return message_box

	def image_to_qimage(self) -> QImage:
		''' Create a QImage from the loaded image '''
		qimage = QImage(self.img.width, self.img.height, QImage.Format_RGB32)

		for y in range(self.img.height):
			for x in range(self.img.width):
				pixel = self.img[x, y]
				qimage.setPixelColor(x, y, QColor(pixel.red, pixel.green, pixel.blue))
		return qimage

	def load_image(self) -> None:
		''' Load an image from a file '''
		file_dialog = QFileDialog()
		file_path, _ = file_dialog.getOpenFileName(self, "Load Image", "", "Image Files (*.ulbmp)")

		if (not file_path):
			return

		# load = self.message("Loading", "Loading image...", "#FFA500", 1000)
		if (file_path.endswith(".ulbmp")):
			pixmap = None
			try:
				self.img = Decoder().load_from(file_path)
				pixmap = QPixmap.fromImage(self.image_to_qimage())
			except Exception as e:
				return self.error_message(f"Decoder error: {str(e)}")
			
			self.scene.clear()
			self.scene.addPixmap(pixmap)
			self.graphics_view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
			self.graphics_view.show()
			self.save_button.setDisabled(False)
			self.message("Success", "✔️ Image loaded successfully!", "#00ED64", 3000)
		else:
			self.error_message("Invalid file format. Please select a .ulbmp file.")
		# load.close()

	def save_image(self) -> None:
		''' Save the image to a file '''
		file_dialog = QFileDialog()
		file_path, _ = file_dialog.getSaveFileName(self, "Save Image", "", "Image Files (*.ulbmp)")

		if not file_path:
			return

		try:
			colors = self.getColors()
			print(len(colors))
			version, ok = QInputDialog.getInt(self, "Version", "Enter the version:", 1, 1, 3)

			if (not ok):
				return

			depth, checked = None, None
			if (version == 3):
				dialog = CustomDialog(self)
				dialog.setTitles("v3 parameters")
				dialog.setText("Enter the depth:", " RLE compression")
				x = str(int(math.log2(len(colors))))
				index = dialog.comboBox.findText(str(x), Qt.MatchExactly)

				if index == -1:  # If exact value is not found
					# Find the closest larger value
					for i in range(dialog.comboBox.count()):
						if int(dialog.comboBox.itemText(i)) > int(x):
							index = i
							break

				dialog.comboBox.setCurrentIndex(index)

				if (not dialog.exec()):
					return

				depth, checked = dialog.getValues()

			"""Save view section"""
			# image = self.graphics_view.grab().toImage()
			# # qimage to Image
			# w = image.width()
			# h = image.height()
			# p = [Pixel(image.pixelColor(x, y).red(), image.pixelColor(x, y).green(), image.pixelColor(x, y).blue()) for y in range(h) for x in range(w)]
			# img = Image(w, h, p)
			# image.save(file_path + ".png")
			# img =  Decoder().load_from(file_path + ".png")

			Encoder(self.img, version, depth=depth, rle=checked, colors=colors).save_to(file_path)
			self.message("Success", "✔️ Image saved successfully!", "#00ED64", 3000)
		except Exception as e:
			self.error_message(f"Encoder error: {str(e)}")
	
	def getColors(self) -> set:
		''' Return a set of colors from the image'''
		colors = set()

		for y in range(self.img.height):
			for x in range(self.img.width):
				pixel = self.img[x, y]
				colors.add(pixel)

		return colors

def load_stylesheet(file: str) -> str:
	''' Load a stylesheet from a file '''
	with open(file, "r") as f:
		return f.read()

if __name__ == "__main__":
	app = QApplication(sys.argv)
	app.setStyleSheet(load_stylesheet("stylesheet.qss"))

	window = MainWindow()
	window.show()

	sys.exit(app.exec())
