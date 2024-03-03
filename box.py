from PySide6.QtWidgets import QLabel, QDialog, QVBoxLayout, QCheckBox, QComboBox, QDialogButtonBox

class CustomDialog(QDialog):
	''' Custom dialog for the application '''
	def __init__(self, parent=None):
		super().__init__(parent)

		self.setWindowTitle("Custom Dialog")

		self.layout = QVBoxLayout(self)
		
		self.label = QLabel("Enter a value:", self)
		self.layout.addWidget(self.label)

		self.comboBox = QComboBox(self)
		self.comboBox.addItems(["1", "2", "4", "8", "24"])
		self.layout.addWidget(self.comboBox)

		self.checkBox = QCheckBox("Check me", self)
		self.layout.addWidget(self.checkBox)

		self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
		self.buttons.accepted.connect(self.accept)
		self.buttons.rejected.connect(self.reject)
		self.layout.addWidget(self.buttons)

	def setTitles(self, title: str) -> None:
		self.setWindowTitle(title)
	
	def setText(self, comboBox: str, checkBox: str) -> None:
		self.label.setText(comboBox)
		self.checkBox.setText(checkBox)

	def getValues(self) -> tuple[int, bool]:
		return int(self.comboBox.currentText()), self.checkBox.isChecked()
