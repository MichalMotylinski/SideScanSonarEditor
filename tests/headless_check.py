from PyQt6.QtWidgets import QApplication
from SideScanSonarEditor.app import MyWindow

app = QApplication([])
win = MyWindow()
win.show()

print("SideScanSonarEditor initialized successfully.")
