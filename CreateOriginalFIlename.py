import sys
import json
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QFormLayout, QWidget, QLabel, QLineEdit, QComboBox, 
                             QPushButton, QDateEdit, QCheckBox, QSpinBox, QMessageBox,
                             QScrollArea, QFrame, QToolTip, QFileDialog, QTabWidget,
                             QTextEdit)
from PyQt6.QtCore import (Qt, QDate, QTimer, QPoint, QPropertyAnimation, 
                          QEasingCurve, QSettings)
from PyQt6.QtGui import (QFont, QColor, QPalette, QIcon, QPixmap, 
                         QCursor, QDesktopServices)


# Write config to file
# with open('filename_config.json', 'w') as f:
#    json.dump(FILENAME_CONFIG, f, indent=4)

# Read config from file
with open('filename_config.json', 'r') as f:
    FILENAME_CONFIG = json.load(f)

class FilenameGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EEG Filename Generator")
        self.setGeometry(100, 100, 600, 800)
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
                width: 150;
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
            QCheckBox {
                font-size: 14px;
                color: #1A3A54;
            }
        """)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        # Filename Generator Tab
        self.filename_tab = QWidget()
        self.filename_layout = QVBoxLayout(self.filename_tab)
        self.tab_widget.addTab(self.filename_tab, "Filename Generator")
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(FILENAME_CONFIG.keys())
        self.preset_combo.currentTextChanged.connect(self.load_preset)
        self.filename_layout.addWidget(QLabel("Select Preset:"))
        self.filename_layout.addWidget(self.preset_combo)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet("background-color: white")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_area.setWidget(self.scroll_content)
        self.filename_layout.addWidget(self.scroll_area)
        
        self.inputs = {}

        
        # Add validation status box
        self.validation_frame = QFrame()
        self.validation_frame.setStyleSheet("""
            QFrame {
                background-color: #E8F5E9;
                border-radius: 8px;
                padding: 10px;
                margin-top: 10px;
                margin-bottom: 10px;
            }
        """)
        self.validation_layout = QVBoxLayout(self.validation_frame)
        self.validation_label = QLabel("Please fill in the fields to generate a filename.")
        self.validation_label.setStyleSheet("font-size: 14px; color: #2E7D32;")
        self.validation_layout.addWidget(self.validation_label)
        self.filename_layout.addWidget(self.validation_frame)

        # Modify result frame (preview box)
        self.result_frame = QFrame()
        self.result_frame.setStyleSheet("""
            QFrame {
                background-color: #E8F5E9;
                border: 2px solid #4CAF50;
                border-radius: 6px;
                padding: 8px;
                margin-top: 8px;
                margin-bottom: 8px;
            }
        """)
        self.result_layout = QHBoxLayout(self.result_frame)
        self.result_label = QLabel()
        self.result_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2E7D32;")
        self.result_layout.addWidget(self.result_label)
        self.copy_button = QPushButton("Copy")
        self.copy_button.setIcon(QIcon.fromTheme("edit-copy"))
        self.copy_button.setToolTip("Copy to Clipboard")
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.copy_button.setEnabled(False)  # Initially disabled
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3A7BC8;
            }
            QPushButton:disabled {
                background-color: #A0A0A0;
            }
        """)
        self.result_layout.addWidget(self.copy_button)
        
        self.filename_layout.addWidget(self.result_frame)
        
        self.lock_button = QPushButton("Lock Filename")
        self.lock_button.clicked.connect(self.lock_filename)
        self.lock_button.setEnabled(False)  # Initially disabled
        self.lock_button.setStyleSheet("""
            QPushButton:disabled {
                background-color: #A0A0A0;
            }
        """)
        self.filename_layout.addWidget(self.lock_button)
        
        # JSON Sidecar Builder Tab
        self.json_tab = QWidget()
        self.json_layout = QVBoxLayout(self.json_tab)
        self.tab_widget.addTab(self.json_tab, "JSON Sidecar Builder")
        self.tab_widget.setTabEnabled(1, False)  # Disable JSON tab initially
        
        self.notes_label = QLabel("Notes about the recording:")
        self.json_layout.addWidget(self.notes_label)
        
        self.notes_text = QTextEdit()
        self.json_layout.addWidget(self.notes_text)
        
        self.save_json_button = QPushButton("Save JSON Sidecar")
        self.save_json_button.clicked.connect(self.save_json_sidecar)
        self.json_layout.addWidget(self.save_json_button)
        
        self.indicators = {}  # Add this line to store the indicator labels

        self.load_preset("BIO")

    def load_preset(self, preset_name):
        self.clear_form()
        preset = FILENAME_CONFIG[preset_name]
        
        # Create a new widget for the scroll area content
        self.scroll_content = QWidget()
        
        # Create a horizontal layout for two columns
        columns_layout = QHBoxLayout(self.scroll_content)
        left_form = QFormLayout()
        right_form = QFormLayout()
        columns_layout.addLayout(left_form)
        columns_layout.addLayout(right_form)
        
        # Set the new widget as the scroll area's widget
        self.scroll_area.setWidget(self.scroll_content)
        
        total_fields = len(preset["segments"]) + len(preset["optional_suffixes"])
        fields_per_column = (total_fields + 1) // 2  # Round up division
        
        field_count = 0
        for segment in preset["segments"]:
            widget = self.create_widget(segment)
            row_layout = QHBoxLayout()
            row_layout.addWidget(widget)
            
            if segment.get("editable", True):
                indicator = QLabel("❌")  # Red X
                indicator.setStyleSheet("color: red; font-size: 16px;")
                self.indicators[segment["name"]] = indicator
                row_layout.addWidget(indicator)
            
            row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            
            if field_count < fields_per_column:
                left_form.addRow(segment["label"], row_layout)
            else:
                right_form.addRow(segment["label"], row_layout)
            
            self.inputs[segment["name"]] = widget
            field_count += 1
        
        for suffix in preset["optional_suffixes"]:
            widget = QCheckBox(suffix["label"])
            widget.stateChanged.connect(lambda state, name=suffix["name"]: self.update_indicator(name, state))
            
            if field_count < fields_per_column:
                left_form.addRow("", widget)
            else:
                right_form.addRow("", widget)
            
            self.inputs[suffix["name"]] = widget
            field_count += 1

        # Set initial preview template
        self.update_preview(initial=True)

    def create_widget(self, segment):
        if segment["type"] == "text":
            widget = QLineEdit()
            widget.setMinimumHeight(30)
            if "default" in segment:
                widget.setText(segment["default"])
            if "editable" in segment and not segment["editable"]:
                widget.setReadOnly(True)
                widget.setStyleSheet("font-size: 14px; background-color: #F0F0F0;")  # Grey out non-editable fields
            else:
                widget.textChanged.connect(lambda text, name=segment["name"]: self.validate_field(name))
                widget.setStyleSheet("font-size: 14px;")
        elif segment["type"] == "combo":
            widget = QComboBox()
            widget.setMinimumHeight(30)
            widget.addItems(segment["options"])
            if segment.get("editable", True):
                widget.currentTextChanged.connect(lambda text, name=segment["name"]: self.validate_field(name))
            else:
                widget.setEnabled(False)
            widget.setStyleSheet("font-size: 14px;")
        elif segment["type"] == "date":
            widget = QDateEdit()
            widget.setMinimumHeight(30)
            widget.setCalendarPopup(True)
            widget.setDate(QDate.currentDate())
            if segment.get("editable", True):
                widget.dateChanged.connect(lambda date, name=segment["name"]: self.validate_field(name))
            else:
                widget.setReadOnly(True)
            widget.setStyleSheet("font-size: 14px;")
        elif segment["type"] == "spinbox":
            widget = QSpinBox()
            widget.setMinimumHeight(30)
            widget.setMinimum(1)
            if segment.get("editable", True):
                widget.valueChanged.connect(lambda value, name=segment["name"]: self.validate_field(name))
            else:
                widget.setReadOnly(True)
            widget.setStyleSheet("font-size: 14px;")
        elif segment["type"] == "hidden":
            widget = QLineEdit()
            widget.setVisible(False)
        return widget

    def clear_form(self):
        if self.scroll_content.layout() is not None:
            # Clear the existing layouts
            for i in reversed(range(self.scroll_content.layout().count())):
                layout = self.scroll_content.layout().itemAt(i).layout()
                if layout is not None:
                    for j in reversed(range(layout.rowCount())):
                        layout.removeRow(j)
            # Remove the column layouts
            while self.scroll_content.layout().count() > 0:
                item = self.scroll_content.layout().takeAt(0)
                if item.layout():
                    item.layout().setParent(None)
        self.inputs.clear()
        self.indicators.clear()

    def validate_field(self, field_name):
        preset = FILENAME_CONFIG[self.preset_combo.currentText()]
        segment = next((s for s in preset["segments"] if s["name"] == field_name), None)
        if segment and "validation" in segment and segment["type"] != "hidden":
            value = self.get_input_value(field_name)
            if re.match(segment["validation"], value):
                self.inputs[field_name].setStyleSheet("border: 1px solid green;")
                self.update_indicator(field_name, True)
            else:
                self.inputs[field_name].setStyleSheet("border: 1px solid red;")
                self.update_indicator(field_name, False)
        elif segment and segment["type"] != "hidden":
            # If no validation is present, consider it valid after interaction
            self.inputs[field_name].setStyleSheet("")
            self.update_indicator(field_name, True)
        self.update_preview()

    def update_indicator(self, field_name, is_valid):
        if field_name in self.indicators:
            self.indicators[field_name].setText("✅" if is_valid else "❌")
            self.indicators[field_name].setStyleSheet("color: green;" if is_valid else "color: red;")

    def update_preview(self, initial=False):
        filename_parts = []
        preset = FILENAME_CONFIG[self.preset_combo.currentText()]
        error_messages = []
        
        for segment in preset["segments"]:
            if initial:
                value = f"<{segment['name']}>"
            else:
                value = self.get_input_value(segment["name"])
                if "validation" in segment:
                    if not re.match(segment["validation"], value):
                        error_messages.append(segment["error_message"])
            filename_parts.append(value)
        
        filename = ""
        for i, part in enumerate(filename_parts):
            if i > 0 and not preset["segments"][i].get("no_leading_underscore", False):
                filename += "_"
            filename += part
        
        for suffix in preset["optional_suffixes"]:
            if initial or self.inputs[suffix["name"]].isChecked():
                filename += f"_{suffix['name']}"
        
        if error_messages:
            self.validation_label.setText("Validation errors:\n" + "\n".join(error_messages))
            self.validation_frame.setStyleSheet("""
                QFrame {
                    background-color: #FFEBEE;
                    border-radius: 8px;
                    padding: 10px;
                    margin-top: 10px;
                    margin-bottom: 10px;
                }
            """)
            self.validation_label.setStyleSheet("font-size: 14px; color: #C62828;")
            self.copy_button.setEnabled(False)
            self.lock_button.setEnabled(False)
        else:
            self.validation_label.setText("All fields are valid.")
            self.validation_frame.setStyleSheet("""
                QFrame {
                    background-color: #E8F5E9;
                    border-radius: 8px;
                    padding: 10px;
                    margin-top: 10px;
                    margin-bottom: 10px;
                }
            """)
            self.validation_label.setStyleSheet("font-size: 14px; color: #2E7D32;")
            self.copy_button.setEnabled(True)
            self.lock_button.setEnabled(True)
        
        self.result_label.setText(filename)

    def generate_filename(self):
        self.update_preview()
        if not any("validation" in segment and not re.match(segment["validation"], self.get_input_value(segment["name"])) for segment in FILENAME_CONFIG[self.preset_combo.currentText()]["segments"] if "validation" in segment):
            self.animate_result_frame()

    def get_input_value(self, name):
        widget = self.inputs[name]
        if isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, QComboBox):
            return widget.currentText()
        elif isinstance(widget, QDateEdit):
            return widget.date().toString("MM-dd-yyyy")
        elif isinstance(widget, QSpinBox):
            return str(widget.value())
        return ""

    def copy_to_clipboard(self):
        filename = self.result_label.text()
        QApplication.clipboard().setText(filename)
        
        self.copy_button.setText("Copied!")
        QTimer.singleShot(2000, self.reset_copy_button)
        
        QToolTip.showText(self.copy_button.mapToGlobal(QPoint(0, 0)), f"Copied: {filename}", self.copy_button)
    
    def reset_copy_button(self):
        self.copy_button.setText("Copy")
        QToolTip.hideText()

    def animate_result_frame(self):
        animation = QPropertyAnimation(self.result_frame, b"geometry")
        animation.setDuration(300)
        animation.setStartValue(self.result_frame.geometry().adjusted(0, 50, 0, 50))
        animation.setEndValue(self.result_frame.geometry())
        animation.setEasingCurve(QEasingCurve.Type.OutBack)
        animation.start()

    def lock_filename(self):
        self.generate_filename()
        if not self.validation_label.text().startswith("Validation errors"):
            self.tab_widget.setTabEnabled(1, True)
            self.tab_widget.setCurrentIndex(1)
            filename = self.result_label.text()
            self.tab_widget.setTabText(1, f"{filename}_metadata.json")

    def save_json_sidecar(self):
        filename = self.result_label.text()
        json_data = {
            "filename": filename,
            "notes": self.notes_text.toPlainText()
        }
        
        # Add all data from the first tab
        for segment in FILENAME_CONFIG[self.preset_combo.currentText()]["segments"]:
            json_data[segment["name"]] = self.get_input_value(segment["name"])
        
        for suffix in FILENAME_CONFIG[self.preset_combo.currentText()]["optional_suffixes"]:
            json_data[suffix["name"]] = self.inputs[suffix["name"]].isChecked()
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Save JSON Sidecar", f"{filename}_metadata.json", "JSON Files (*.json)")
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(json_data, f, indent=4)
            QMessageBox.information(self, "Success", "JSON sidecar saved successfully!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FilenameGenerator()
    window.show()
    sys.exit(app.exec())