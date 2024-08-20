import sys
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QComboBox, QTextEdit, 
                             QFileDialog, QMessageBox, QLineEdit, QDateEdit, 
                             QCheckBox, QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt, QSettings, QDate
from PyQt6.QtGui import QIcon, QFont
from ulid import ULID

class EEGFileProcessor(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("YourOrganization", "EEGFileProcessor")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Study dropdown
        study_layout = self.create_labeled_combo("Study:", ["ENTRAIN", "Other"])
        self.study_combo = study_layout.itemAt(1).widget()
        layout.addLayout(study_layout)

        # Visit number
        visit_layout = self.create_labeled_input("Visit number:")
        self.visit_input = visit_layout.itemAt(1).widget()
        layout.addLayout(visit_layout)

        # Subject ID
        subject_id_layout = self.create_labeled_input("Subject ID:")
        self.subject_id_input = subject_id_layout.itemAt(1).widget()
        layout.addLayout(subject_id_layout)

        # Subject initials
        subject_initials_layout = self.create_labeled_input("Subject initials:")
        self.subject_initials_input = subject_initials_layout.itemAt(1).widget()
        layout.addLayout(subject_initials_layout)

        # Date
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Date:"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(self.date_edit)
        layout.addLayout(date_layout)

        # Location dropdown
        location_layout = self.create_labeled_combo("Location:", ["S Lab Front Booth", "Other"])
        self.location_combo = location_layout.itemAt(1).widget()
        layout.addLayout(location_layout)

        # Net serial number
        net_serial_layout = self.create_labeled_input("Net serial number:")
        self.net_serial_input = net_serial_layout.itemAt(1).widget()
        layout.addLayout(net_serial_layout)

        # Modifiers
        modifiers_layout = QHBoxLayout()
        modifiers_layout.addWidget(QLabel("Modifiers:"))
        self.speakers_checkbox = QCheckBox("Speakers?")
        self.baby_cap_checkbox = QCheckBox("Baby cap?")
        modifiers_layout.addWidget(self.speakers_checkbox)
        modifiers_layout.addWidget(self.baby_cap_checkbox)
        layout.addLayout(modifiers_layout)

        # Other notes
        other_notes_layout = self.create_labeled_input("Other notes:")
        self.other_notes_input = other_notes_layout.itemAt(1).widget()
        layout.addLayout(other_notes_layout)

        # File selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        file_button = QPushButton("Add File")
        file_button.setIcon(QIcon.fromTheme("document-open"))
        file_button.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(file_button)
        layout.addLayout(file_layout)

        # File table
        self.file_table = QTableWidget(0, 2)
        self.file_table.setHorizontalHeaderLabels(["File type", "File path"])
        layout.addWidget(self.file_table)

        # Clear Data button
        clear_button = QPushButton("Clear Data")
        clear_button.clicked.connect(self.clear_data)
        layout.addWidget(clear_button)

        # Process button
        process_button = QPushButton("Back up EEG files")
        process_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        process_button.clicked.connect(self.process_file)
        layout.addWidget(process_button)

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        layout.addWidget(cancel_button)

        self.setLayout(layout)
        self.setWindowTitle('EEG File Processor')
        self.setGeometry(300, 300, 500, 600)
        self.setWindowIcon(QIcon.fromTheme("application-x-executable"))

    def create_labeled_combo(self, label, items):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        combo = QComboBox()
        combo.addItems(items)
        layout.addWidget(combo)
        return layout

    def create_labeled_input(self, label):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        line_edit = QLineEdit()
        layout.addWidget(line_edit)
        return layout

    def select_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select EEG File", "", "EEG Files (*.edf *.bdf);;All Files (*)")
        if file_name:
            row_position = self.file_table.rowCount()
            self.file_table.insertRow(row_position)
            self.file_table.setItem(row_position, 0, QTableWidgetItem("EEG File"))
            self.file_table.setItem(row_position, 1, QTableWidgetItem(file_name))

    def clear_data(self):
        self.study_combo.setCurrentIndex(0)
        self.visit_input.clear()
        self.subject_id_input.clear()
        self.subject_initials_input.clear()
        self.date_edit.setDate(QDate.currentDate())
        self.location_combo.setCurrentIndex(0)
        self.net_serial_input.clear()
        self.speakers_checkbox.setChecked(False)
        self.baby_cap_checkbox.setChecked(False)
        self.other_notes_input.clear()
        self.file_table.setRowCount(0)

    def process_file(self):
        if self.file_table.rowCount() == 0:
            self.show_error("Please add at least one file.")
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not output_dir:
            self.show_error("Please select an output directory.")
            return

        try:
            for row in range(self.file_table.rowCount()):
                file_path = self.file_table.item(row, 1).text()
                ulid = ULID()
                file_name = os.path.basename(file_path)
                file_creation_time = os.path.getctime(file_path)

                new_file_name = f"{ulid}_{file_name}"
                new_file_path = os.path.join(output_dir, new_file_name)

                # Copy the file instead of renaming
                with open(file_path, 'rb') as src, open(new_file_path, 'wb') as dst:
                    dst.write(src.read())

                sidecar_data = {
                    "original_filename": file_name,
                    "creation_date": datetime.fromtimestamp(file_creation_time).isoformat(),
                    "study": self.study_combo.currentText(),
                    "visit_number": self.visit_input.text(),
                    "subject_id": self.subject_id_input.text(),
                    "subject_initials": self.subject_initials_input.text(),
                    "date": self.date_edit.date().toString(Qt.ISODate),
                    "location": self.location_combo.currentText(),
                    "net_serial_number": self.net_serial_input.text(),
                    "modifiers": {
                        "speakers": self.speakers_checkbox.isChecked(),
                        "baby_cap": self.baby_cap_checkbox.isChecked()
                    },
                    "other_notes": self.other_notes_input.text(),
                    "processing_date": datetime.now().isoformat()
                }

                sidecar_file_path = f"{new_file_path}.json"
                with open(sidecar_file_path, 'w') as f:
                    json.dump(sidecar_data, f, indent=2)

            self.show_success(f"Files processed and backed up to: {output_dir}")
        except Exception as e:
            self.show_error(f"An error occurred: {str(e)}")

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def show_success(self, message):
        QMessageBox.information(self, "Success", message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ex = EEGFileProcessor()
    ex.show()
    sys.exit(app.exec())