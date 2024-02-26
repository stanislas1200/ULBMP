import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QGraphicsScene, QGraphicsView
from PySide6.QtWidgets import QErrorMessage, QMessageBox, QInputDialog
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QColor


from encoding import Decoder, Encoder



class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()

		self.setWindowTitle("Image Editor")

		# Create a layout for the main window
		layout = QVBoxLayout()

		# Create a label to display the loaded image
		# self.image_label = QLabel()
		# layout.addWidget(self.image_label)

		# Create a button to load an image
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

		# Create a graphics view to display the image
		self.graphics_view = QGraphicsView()
		self.graphics_view.setFixedWidth(640)
		self.graphics_view.setFixedHeight(480)
		self.graphics_view.hide();
		layout.addWidget(self.graphics_view) 

		# Create a scene to hold the image
		self.scene = QGraphicsScene()
		self.graphics_view.setScene(self.scene)

		# Create a widget to hold the layout
		widget = QWidget()
		widget.setLayout(layout)
		self.setCentralWidget(widget)

	def error_message(self, message):
		''' Error message box '''
		error_dialog = QErrorMessage(self)
		error_dialog.setWindowTitle("Error")
		error_dialog.showMessage(message)
		error_dialog.setModal(True) # FIXME : not working and QError already is modal 
		error_dialog.exec()
	
	def message(self, title, message, color=None, timeout=0):
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

	def image_to_qimage(self):
		''' Create a QImage from the loaded image '''
		qimage = QImage(self.img.width, self.img.height, QImage.Format_RGB32)

		for y in range(self.img.height):
			for x in range(self.img.width):
				pixel = self.img[x, y]
				qimage.setPixelColor(x, y, QColor(pixel.red, pixel.green, pixel.blue))
		return qimage

	def load_image(self):
		''' Load an image from a file '''
		file_dialog = QFileDialog()
		file_path, _ = file_dialog.getOpenFileName(self, "Load Image", "", "Image Files (*.png , *.ulbmp)")
		
		if file_path:
			load = self.message("Loading", "Loading image...", "#FFA500", 1000)
			if (file_path.endswith(".ulbmp")):
				try:
					self.img = Decoder().load_from(file_path)
				except Exception as e:
					return self.error_message(f"Decoder error: {str(e)}")
				
				pixmap = QPixmap.fromImage(self.image_to_qimage())
				self.scene.clear()
				self.scene.addPixmap(pixmap)
				self.graphics_view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
				self.graphics_view.show()
				self.save_button.setDisabled(False)
				self.message("Success", "✔️ Image loaded successfully!", "#00ED64", 3000)
			else:
				self.error_message("Invalid file format. Please select a .ulbmp file.")
			# load.close()

	def save_image(self):
		''' Save the image to a file '''
		file_dialog = QFileDialog()
		file_path, _ = file_dialog.getSaveFileName(self, "Save Image", "", "Image Files (*.ulbmp)")
		if file_path:
			try :
				version, ok = QInputDialog.getInt(self, "Version", "Enter the version:", 1, 1, 2)
				if ok:
					Encoder(self.img, version).save_to(file_path)
			except Exception as e:
				return self.error_message(f"Encoder error: {str(e)}")
			self.message("Success", "✔️ Image saved successfully!", "#00ED64", 3000)


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
