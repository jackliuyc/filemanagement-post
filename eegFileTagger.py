import sys
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QTextEdit, QFileDialog
from PyQt6.QtCore import Qt
from ulid import ULID

class EEGFileProcessor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # File selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        file_button = QPushButton("Select EEG File")
        file_button.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(file_button)
        layout.addLayout(file_layout)

        # Paradigm dropdown
        paradigm_layout = QHBoxLayout()
        paradigm_layout.addWidget(QLabel("Paradigm:"))
        self.paradigm_combo = QComboBox()
        self.paradigm_combo.addItems(["Resting", "Chirp", "Other"])
        paradigm_layout.addWidget(self.paradigm_combo)
        layout.addLayout(paradigm_layout)

        # EEG tech initials dropdown
        tech_layout = QHBoxLayout()
        tech_layout.addWidget(QLabel("EEG Tech Initials:"))
        self.tech_combo = QComboBox()
        self.tech_combo.addItems(["LE", "JD", "MK"])  # Add more initials as needed
        self.tech_combo.setEditable(True)
        tech_layout.addWidget(self.tech_combo)
        layout.addLayout(tech_layout)

        # Comments field
        layout.addWidget(QLabel("Comments:"))
        self.comments_text = QTextEdit()
        layout.addWidget(self.comments_text)

        # Process button
        process_button = QPushButton("Process File")
        process_button.clicked.connect(self.process_file)
        layout.addWidget(process_button)

        self.setLayout(layout)
        self.setWindowTitle('EEG File Processor')
        self.setGeometry(300, 300, 400, 300)

    def select_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select EEG File")
        if file_name:
            self.file_label.setText(file_name)

    def process_file(self):
        file_path = self.file_label.text()
        if file_path == "No file selected":
            print("Please select a file first.")
            return

        # Generate ULID
        ulid = ULID()

        # Get file info
        file_name = os.path.basename(file_path)
        file_creation_time = os.path.getctime(file_path)

        # Create new filename
        new_file_name = f"{ulid}_{file_name}"
        new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)

        # Rename the file
        os.rename(file_path, new_file_path)

        # Create sidecar JSON
        sidecar_data = {
            "original_filename": file_name,
            "creation_date": datetime.fromtimestamp(file_creation_time).isoformat(),
            "paradigm": self.paradigm_combo.currentText(),
            "eeg_tech": self.tech_combo.currentText(),
            "comments": self.comments_text.toPlainText()
        }

        # Save sidecar JSON
        sidecar_file_path = f"{new_file_path}.json"
        with open(sidecar_file_path, 'w') as f:
            json.dump(sidecar_data, f, indent=2)

        print(f"File processed: {new_file_path}")
        print(f"Sidecar JSON created: {sidecar_file_path}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = EEGFileProcessor()
    ex.show()
    sys.exit(app.exec())
