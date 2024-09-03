import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QPushButton, QComboBox, QFileDialog, 
                             QFormLayout, QScrollArea, QFrame)
from PyQt5.QtCore import Qt

class FileSection(QWidget):
    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.parent_window = parent
        self.initUI()
    
    def initUI(self):
        layout = QFormLayout()
        
        # Paradigm dropdown
        self.paradigm_combo = QComboBox()
        self.paradigm_combo.addItems(["Paradigm 1", "Paradigm 2", "Paradigm 3"])  # Add your paradigms here
        layout.addRow(QLabel(f"Paradigm {self.index + 1}:"), self.paradigm_combo)
        
        # RAW file upload
        self.raw_button = QPushButton("Upload .RAW file")
        self.raw_button.clicked.connect(self.uploadRAW)
        self.raw_label = QLabel("No file selected")
        layout.addRow(self.raw_button, self.raw_label)
        
        # MFF folder upload
        self.mff_button = QPushButton("Upload .MFF folder")
        self.mff_button.clicked.connect(self.uploadMFF)
        self.mff_label = QLabel("No folder selected")
        layout.addRow(self.mff_button, self.mff_label)
        
        self.setLayout(layout)

    def uploadRAW(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Select .RAW file", "", "RAW Files (*.raw);;All Files (*)", options=options)
        if filename:
            self.raw_label.setText(filename)
        self.parent_window.checkEnableAddButton()  # Notify parent to check enable status

    def uploadMFF(self):
        options = QFileDialog.Options()
        folder = QFileDialog.getExistingDirectory(self, "Select .MFF folder", "", options=options)
        if folder:
            self.mff_label.setText(folder)
        self.parent_window.checkEnableAddButton()  # Notify parent to check enable status

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        
        # Apply stylesheet after initialization
        self.setStyleSheet("""
            QMainWindow {
                background-color: #E6F3FF;
            }
            QLabel {
                font-size: 14px;
                color: #1A3A54;
            }
            QComboBox, QLineEdit, QDateEdit, QSpinBox {
                font-size: 14px;
                padding: 5px;
                border: 1px solid #4A90E2;
                border-radius: 4px;
                background-color: #FFFFFF;
                color: #1A3A54;
                width: 150px;
            }
            QPushButton {
                font-size: 16px;
                padding: 10px;
                background-color: #4A90E2;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3A7BC8;
            }
            QPushButton:disabled {
                background-color: #B0B0B0;  
                color: #7F7F7F;  
                
            }
            QCheckBox {
                font-size: 14px;
                color: #1A3A54;
            }
        """)

        
        self.setWindowTitle("File Input Form")
        self.setGeometry(100, 100, 600, 400)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout()
        
        # Text file input
        self.txt_button = QPushButton("Upload Notes (.txt) file")
        self.txt_button.clicked.connect(self.uploadTXT)
        self.txt_label = QLabel("No file selected")
        self.layout.addWidget(self.txt_button)
        self.layout.addWidget(self.txt_label)
        
        # Container for sections
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)
        
        # Add button
        self.add_button = QPushButton("Add Additional Paradigms")
        self.add_button.clicked.connect(self.addSection)
        self.add_button.setEnabled(False)
        self.layout.addWidget(self.add_button)
        
        # Add initial section
        self.sections = []
        self.addSection()  # Initialize with one section

        self.central_widget.setLayout(self.layout)
        
    def uploadTXT(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Select .txt file", "", "Text Files (*.txt);;All Files (*)", options=options)
        if filename:
            self.txt_label.setText(filename)
            self.checkEnableAddButton()

    def addSection(self):
        section = FileSection(len(self.sections), self)
        self.sections.append(section)
        self.scroll_layout.addWidget(section)
        
        # Add spacer or divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        self.scroll_layout.addWidget(divider)
        
        self.checkEnableAddButton()

    def checkEnableAddButton(self):
        # Check if the main .txt file has been selected
        if self.txt_label.text() == "No file selected":
            self.add_button.setEnabled(False)
            return
        
        # Get the latest section
        latest_section = self.sections[-1]
        
        # Check if the latest section's paradigm is selected
        if latest_section.paradigm_combo.currentIndex() == -1:
            self.add_button.setEnabled(False)
            return
        
        # Check if a .RAW file has been selected in the latest section
        if latest_section.raw_label.text() == "No file selected":
            self.add_button.setEnabled(False)
            return
        
        # Check if a .MFF folder has been selected in the latest section
        if latest_section.mff_label.text() == "No folder selected":
            self.add_button.setEnabled(False)
            return
        
        # If all checks pass, enable the add_button
        self.add_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
