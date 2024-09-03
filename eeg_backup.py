import sys
import json
import re
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QFormLayout, QWidget, QLabel, QLineEdit, QComboBox, 
                             QPushButton, QDateEdit, QCheckBox, QSpinBox, QMessageBox,
                             QScrollArea, QFrame, QToolTip, QFileDialog, QTabWidget,
                             QTextEdit, QSizePolicy, QMenuBar, QMenu, QGraphicsOpacityEffect, QSplitter,
                             QAction)  # Add QAction here
from PyQt5.QtCore import (Qt, QDate, QTimer, QPoint, QPropertyAnimation, 
                          QEasingCurve, QSettings, QAbstractAnimation)
from PyQt5.QtGui import (QFont, QColor, QPalette, QIcon, QPixmap, 
                         QCursor, QDesktopServices, QTextCursor)

# Read config from file
with open('filename_config.json', 'r') as f:
    FILENAME_CONFIG = json.load(f)

class FilenameGenerator(QMainWindow):

    def __init__(self):
        super().__init__()
        
        # Window setup
        self.setWindowTitle("EEG Filename Generator")
        self.setGeometry(100, 100, 1000, 600)
        
        # Set global stylesheet
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
        
        # Central widget and main layout setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Add study label in the upper right
        self.study_label = QLabel()
        self.study_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.study_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #4A90E2;
            margin: 4px;
        """)
        self.layout.addWidget(self.study_label)
        
        # Tab widget setup
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        # Filename Generator Tab
        self.filename_tab = QWidget()
        self.filename_layout = QVBoxLayout(self.filename_tab)
        self.tab_widget.addTab(self.filename_tab, "Perfect Filename")
        
        # Preset combo box
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(FILENAME_CONFIG.keys())
        self.preset_combo.currentTextChanged.connect(self.load_preset)
        self.filename_layout.addWidget(QLabel("Select Preset:"))
        self.filename_layout.addWidget(self.preset_combo)
        
        # Scroll area for input fields
        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet("background-color: white")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_area.setMinimumHeight(400)  # Adjust this value as needed
        self.scroll_content = QWidget()
        self.scroll_area.setWidget(self.scroll_content)
        self.filename_layout.addWidget(self.scroll_area)
        
        self.inputs = {}

        # Result frame (preview box)
        self.result_frame = QFrame()
        self.result_frame.setStyleSheet("""
            QFrame {
                background-color: #E8F5E9;
                border: 2px solid #4CAF50;
                border-radius: 6px;
                padding: 8px;
                margin-top: 5px;
                margin-bottom: 5px;
            }
        """)
        self.result_layout = QHBoxLayout(self.result_frame)
        self.result_label = QLabel()
        self.result_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2E7D32;")
        self.result_layout.addWidget(self.result_label)
        
        # Copy button
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
        
        # Lock filename button
        self.lock_button = QPushButton("Lock Filename")
        self.lock_button.clicked.connect(self.lock_filename)
        self.lock_button.setEnabled(False)  # Initially disabled
        self.lock_button.setStyleSheet("""
            QPushButton:disabled {
                background-color: #A0A0A0;
            }
        """)
        self.filename_layout.addWidget(self.lock_button)
        # Update study label and connect to preset changes
        self.update_study_label()
        self.preset_combo.currentTextChanged.connect(self.update_study_label)

        
        # JSON Sidecar Builder Tab
        self.json_tab = QWidget()
        self.json_layout = QVBoxLayout(self.json_tab)
        self.tab_widget.addTab(self.json_tab, "JSON Sidecar Builder")
        self.tab_widget.setTabEnabled(1, False)  # Disable JSON tab initially
        
        # Add quick tags section
        self.quick_tags_scroll = QScrollArea()
        self.quick_tags_scroll.setWidgetResizable(True)
        self.quick_tags_scroll.setMaximumHeight(200)  # Set maximum height instead of fixed
        self.quick_tags_widget = QWidget()
        self.quick_tags_layout = QVBoxLayout(self.quick_tags_widget)
        self.quick_tags_scroll.setWidget(self.quick_tags_widget)
        self.json_layout.addWidget(self.quick_tags_scroll, 1)  # Set stretch factor to 1

        # Define quick tags
        quick_tags = ["Line Noise", "Movement", "Poor Audio", "Electrode Issues", "Drowsiness", "External Interference", "Removed Headphones", "Moving Around", "Talking", "Crying", "Jaw", "Invalid Data", "Other"]
        
        row_layout = QHBoxLayout()
        for i, tag in enumerate(quick_tags):
            tag_button = QPushButton(tag)
            tag_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            tag_button.setStyleSheet("""
                QPushButton {
                    background-color: #4A90E2;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 5px 10px;
                    margin: 2px;
                }
                QPushButton:hover {
                    background-color: #3A7BC8;
                }
            """)
            tag_button.clicked.connect(lambda _, t=tag: self.add_tag_to_notes(t))
            row_layout.addWidget(tag_button)
            
            # Start a new row after every 4 buttons
            if (i + 1) % 4 == 0 or i == len(quick_tags) - 1:
                self.quick_tags_layout.addLayout(row_layout)
                row_layout = QHBoxLayout()

        # Replace the existing notes_text with two separate text fields
        self.notes_layout = QVBoxLayout()
        
        self.session_notes_label = QLabel("Session Notes:")
        self.session_notes_text = QTextEdit()
        self.session_notes_text.textChanged.connect(self.notes_text_changed)
        
        self.paradigm_notes_label = QLabel("Paradigm Notes:")
        self.paradigm_notes_text = QTextEdit()
        self.paradigm_notes_text.textChanged.connect(self.notes_text_changed)
        
        splitter = QSplitter(Qt.Vertical)
        session_widget = QWidget()
        session_layout = QVBoxLayout(session_widget)
        session_layout.addWidget(self.session_notes_label)
        session_layout.addWidget(self.session_notes_text)
        
        paradigm_widget = QWidget()
        paradigm_layout = QVBoxLayout(paradigm_widget)
        paradigm_layout.addWidget(self.paradigm_notes_label)
        paradigm_layout.addWidget(self.paradigm_notes_text)
        
        splitter.addWidget(session_widget)
        splitter.addWidget(paradigm_widget)
        
        self.notes_layout.addWidget(splitter)
        self.json_layout.addLayout(self.notes_layout, 3)  # Replace the existing notes_text addition

        
        button_layout = QHBoxLayout()
        self.save_json_button = QPushButton("Save JSON Sidecar")
        self.save_json_button.clicked.connect(self.save_json_sidecar)
        button_layout.addWidget(self.save_json_button)
        
        self.change_paradigm_button = QPushButton("Change Paradigm")
        self.change_paradigm_button.clicked.connect(self.change_paradigm)
        button_layout.addWidget(self.change_paradigm_button)
        
        self.json_layout.addLayout(button_layout)
        
        self.indicators = {}  # Add this line to store the indicator labels
        
        # Add Reset Form and Reset Paradigm buttons
        self.reset_buttons_layout = QHBoxLayout()
        self.reset_form_button = QPushButton("Reset Form")
        self.reset_form_button.clicked.connect(self.reset_form)
        self.reset_paradigm_button = QPushButton("Reset Paradigm")
        self.reset_paradigm_button.clicked.connect(self.reset_paradigm)  # Changed from self.reset_paradigm to self.reset_form
        self.reset_buttons_layout.addWidget(self.reset_form_button)
        self.reset_buttons_layout.addWidget(self.reset_paradigm_button)
        self.filename_layout.addLayout(self.reset_buttons_layout)

        # Add debug mode checkbox
        self.debug_mode_checkbox = QCheckBox("Debug Mode")
        self.debug_mode_checkbox.stateChanged.connect(self.toggle_debug_mode)
        self.filename_layout.addWidget(self.debug_mode_checkbox)

        # Add menu bar
        self.create_menu_bar()

        # Initialize output folder as the current working directory
        self.output_folder = os.getcwd()

        # Add save notification light and last saved message label
        save_status_layout = QHBoxLayout()
        self.save_light = QLabel()
        self.save_light.setFixedSize(20, 20)
        self.save_light.setStyleSheet("""
            background-color: #808080;
            border-radius: 10px;
        """)
        save_status_layout.addWidget(self.save_light)
        self.last_saved_label = QLabel("Not saved yet")
        self.last_saved_label.setStyleSheet("font-size: 10px; color: #666;")
        save_status_layout.addWidget(self.last_saved_label)
        save_status_layout.addStretch()
        self.json_layout.addLayout(save_status_layout)

        # Add output folder display at the bottom
        self.create_output_folder_display()

        self.load_preset("BIO")

        # Add these lines in the __init__ method after initializing the JSON tab
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save_json)
        self.auto_save_timer.start(30000)  # Auto-save every 30 seconds


        # Load saved output folder
        self.settings = QSettings("FilenameGeneratorSettings", "EEG Filename Generator")
        self.output_folder = self.settings.value("output_folder", os.getcwd())
        self.update_output_folder_display()

    def add_tag_to_notes(self, tag):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_tag = f"[{timestamp}] {tag}"
        
        self.paradigm_notes_text.setHtml(f"{self.paradigm_notes_text.toHtml()}<p style='margin-top: 10px; margin-bottom: 10px; padding: 5px; background-color: #f0f0f0; border-left: 3px solid #4A90E2; font-family: Arial, sans-serif;'>{formatted_tag}</p>")
        self.paradigm_notes_text.moveCursor(QTextCursor.End)
        self.auto_save_json()

    def update_study_label(self):
        # Get the preview filename from the result label
        filename = self.result_label.text()
        
        # Update the study label with the preview filename
        self.study_label.setText(f"{filename}")

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
            row_layout = QVBoxLayout()  # Changed to QVBoxLayout
            
            # Add error label
            error_label = QLabel()
            error_label.setStyleSheet("color: red; font-size: 12px;")
            error_label.setVisible(False)
            row_layout.addWidget(error_label)
            
            widget_row = QHBoxLayout()
            widget_row.addWidget(widget)
            widget_row.addStretch()  # Add stretch to push widget to the left
            
            if segment.get("editable", True):
                indicator = QLabel("❌")  # Red X
                indicator.setStyleSheet("color: red; font-size: 16px;")
                self.indicators[segment["name"]] = indicator
                widget_row.addWidget(indicator)
            
            row_layout.addLayout(widget_row)
            
            if field_count < fields_per_column:
                left_form.addRow(segment["label"], row_layout)
            else:
                right_form.addRow(segment["label"], row_layout)
            
            self.inputs[segment["name"]] = {"widget": widget, "error_label": error_label}
            field_count += 1
        
        for suffix in preset["optional_suffixes"]:
            widget = QCheckBox(suffix["label"])
            widget.stateChanged.connect(lambda state, name=suffix["name"]: self.update_indicator(name, state))
            
            checkbox_layout = QHBoxLayout()
            checkbox_layout.addWidget(widget)
            checkbox_layout.addStretch()  # Add stretch to push checkbox to the left
            
            if field_count < fields_per_column:
                left_form.addRow("", checkbox_layout)
            else:
                right_form.addRow("", checkbox_layout)
            
            self.inputs[suffix["name"]] = widget
            field_count += 1

        # Adjust the scroll content widget's layout
        self.scroll_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_content.setLayout(columns_layout)

        # Set initial preview template
        self.update_preview(initial=True)

        # Validate all fields after loading
        for segment in preset["segments"]:
            self.validate_field(segment["name"])

        # Add this line at the end of the method
        self.update_json_tab()

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
                # Add this line to trigger validation on focus out
                widget.focusOutEvent = lambda event, name=segment["name"]: self.validate_field(name)
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
        if segment and segment["type"] != "hidden":
            widget = self.inputs[field_name]["widget"]
            error_label = self.inputs[field_name]["error_label"]
            value = self.get_input_value(field_name)
            is_valid = True
            
            # Add this block to check if the dropdown is empty
            if isinstance(widget, QComboBox) and widget.currentText() == "":
                is_valid = False
            elif "validation" in segment:
                is_valid = re.match(segment["validation"], value) is not None
            
            if is_valid:
                if segment["type"] == "combo":
                    widget.setStyleSheet("border: 1px solid green; font-size: 14px;")
                else:
                    widget.setStyleSheet("border: 1px solid green;")
                self.update_indicator(field_name, True)
                error_label.setVisible(False)
            else:
                widget.setStyleSheet("border: 1px solid red;")
                self.update_indicator(field_name, False)
                error_label.setText(segment["error_message"] if "error_message" in segment else "This field is required")
                error_label.setVisible(True)
        self.update_preview()
        self.update_study_label()
        self.update_json_tab()
        self.clear_paradigm_notes()  # Add this line to clear notes when any field is changed

    def update_indicator(self, field_name, is_valid):
        if field_name in self.indicators:
            self.indicators[field_name].setText("✅" if is_valid else "❌")
            self.indicators[field_name].setStyleSheet("color: green;" if is_valid else "color: red;")
        self.update_json_tab()

    def update_preview(self, initial=False):
        filename_parts = []
        preset = FILENAME_CONFIG[self.preset_combo.currentText()]
        all_valid = True
        
        for segment in preset["segments"]:
            if initial:
                value = f"<{segment['name']}>"
            else:
                value = self.get_input_value(segment["name"])
                if "validation" in segment:
                    if not re.match(segment["validation"], value):
                        all_valid = False
            filename_parts.append(value)
        
        filename = ""
        for i, part in enumerate(filename_parts):
            if i > 0 and not preset["segments"][i].get("no_leading_underscore", False):
                filename += "_"
            filename += part
        
        for suffix in preset["optional_suffixes"]:
            if initial or self.inputs[suffix["name"]].isChecked():
                filename += f"_{suffix['name']}"
        
        if all_valid:
            self.copy_button.setEnabled(True)
            self.lock_button.setEnabled(True)
        else:
            self.copy_button.setEnabled(False)
            self.lock_button.setEnabled(False)
        
        self.result_label.setText(filename)


    def generate_filename(self):
        self.update_preview()
        if not any("validation" in segment and not re.match(segment["validation"], self.get_input_value(segment["name"])) for segment in FILENAME_CONFIG[self.preset_combo.currentText()]["segments"] if "validation" in segment):
            self.animate_result_frame()

    def get_input_value(self, name):
        widget = self.inputs[name]["widget"]
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
        animation.setEasingCurve(QEasingCurve.OutBack)
        animation.start()

    def toggle_debug_mode(self, state):
        is_debug = state == Qt.Checked
        self.tab_widget.setTabEnabled(1, is_debug)
        if is_debug:
            self.lock_button.setEnabled(True)
            self.copy_button.setEnabled(True)
        else:
            self.validate_all_fields()

    def validate_all_fields(self):
        preset = FILENAME_CONFIG[self.preset_combo.currentText()]
        for segment in preset["segments"]:
            if segment.get("editable", True):
                self.validate_field(segment["name"])
        
        all_valid = all(self.indicators[field].text() == "✅" for field in self.indicators)
        self.lock_button.setEnabled(all_valid)
        self.copy_button.setEnabled(all_valid)
        self.tab_widget.setTabEnabled(1, all_valid)

    def lock_filename(self):
        if not self.debug_mode_checkbox.isChecked():
            self.generate_filename()
            all_valid = all(self.indicators[field].text() == "✅" for field in self.indicators)
            if all_valid:
                self.tab_widget.setTabEnabled(1, True)
                self.tab_widget.setCurrentIndex(1)
                filename = self.result_label.text()
                self.tab_widget.setTabText(1, f"{filename}_metadata.json")
            else:
                QMessageBox.warning(self, "Validation Error", "Please correct all fields before locking the filename.")
        else:
            self.tab_widget.setCurrentIndex(1)

    def update_json_tab(self):
        if self.tab_widget.isTabEnabled(1):
            self.generate_json_data()
            self.update_notes_from_json()

    def generate_json_data(self):
        filename = self.result_label.text()
        self.json_data = {
            "filename": filename,
            "session_notes": self.session_notes_text.toPlainText(),
            "paradigm_notes": self.paradigm_notes_text.toPlainText()
        }

        session_parts = []
        current_preset = self.preset_combo.currentText()
        
        for segment in FILENAME_CONFIG[current_preset]["segments"]:
            value = self.get_input_value(segment["name"])
            self.json_data[segment["name"]] = value
            
            # Add to session_parts if it's not the file_type
            if segment["name"] != "file_type":
                session_parts.append(value)
        
        # Join session parts with underscores
        self.json_data["session"] = "_".join(session_parts)
        
        for suffix in FILENAME_CONFIG[current_preset]["optional_suffixes"]:
            self.json_data[suffix["name"]] = self.inputs[suffix["name"]].isChecked()

        
        for segment in FILENAME_CONFIG[self.preset_combo.currentText()]["segments"]:
            self.json_data[segment["name"]] = self.get_input_value(segment["name"])
        
        for suffix in FILENAME_CONFIG[self.preset_combo.currentText()]["optional_suffixes"]:
            self.json_data[suffix["name"]] = self.inputs[suffix["name"]].isChecked()

    def update_notes_from_json(self):
        if hasattr(self, 'json_data'):
            if 'session_notes' in self.json_data:
                self.session_notes_text.setPlainText(self.json_data['session_notes'])
            if 'paradigm_notes' in self.json_data:
                self.paradigm_notes_text.setPlainText(self.json_data['paradigm_notes'])

    def auto_save_json(self):
        if self.tab_widget.currentIndex() == 1 and self.output_folder:
            self.save_json_sidecar(auto_save=True)

    def save_json_sidecar(self, auto_save=False):
        if not self.output_folder:
            QMessageBox.warning(self, "No Output Folder", "Please select an output folder first.")
            return

        self.generate_json_data()
        filename = self.json_data["filename"]
        
        file_path = os.path.join(self.output_folder, f"{filename}_metadata.json")
        with open(file_path, 'w') as f:
            json.dump(self.json_data, f, indent=4)
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_saved_label.setText(f"Last saved: {current_time}")
        
        # Flash the save light
        self.flash_save_light()



    def flash_save_light(self):
        self.save_light.setStyleSheet("""
            background-color: #00FF00;
            border-radius: 10px;
        """)
        QTimer.singleShot(500, self.reset_save_light)

    def reset_save_light(self):
        self.save_light.setStyleSheet("""
            background-color: #808080;
            border-radius: 10px;
        """)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", self.output_folder)
        if folder:
            self.output_folder = folder
            self.update_output_folder_display()
            self.auto_save_json()
            # Save the selected folder
            self.settings.setValue("output_folder", self.output_folder)


    def notes_text_changed(self):
        self.auto_save_json()

    def create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')

        # Add "Select Output Folder" action
        select_folder_action = QAction('Select Output Folder', self)
        select_folder_action.triggered.connect(self.select_output_folder)
        file_menu.addAction(select_folder_action)

    def create_output_folder_display(self):
        # Create a widget to hold the output folder display
        output_folder_widget = QWidget()
        output_folder_layout = QHBoxLayout(output_folder_widget)
        output_folder_layout.setContentsMargins(10, 5, 10, 5)

        # Create a label to display the current output folder
        self.output_folder_label = QLabel("No output folder selected")
        self.output_folder_label.setStyleSheet("""
            font-size: 12px;
            color: #666;
            padding: 5px;
            background-color: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 3px;
        """)

        # Create a "Change" button
        change_folder_button = QPushButton("Change")
        change_folder_button.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 5px 10px;
                background-color: #4A90E2;
                color: white;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #3A7BC8;
            }
        """)
        change_folder_button.clicked.connect(self.select_output_folder)

        # Add stretcher to push elements to the right
        output_folder_layout.addStretch()
        output_folder_layout.addWidget(self.output_folder_label)
        output_folder_layout.addWidget(change_folder_button)

        # Add the output folder display to the main layout
        self.layout.addWidget(output_folder_widget)

    def update_output_folder_display(self):
        if self.output_folder:
            display_path = (self.output_folder[:50] + '...') if len(self.output_folder) > 53 else self.output_folder
            self.output_folder_label.setText(f"Output: {display_path}")
            self.output_folder_label.setToolTip(self.output_folder)
        else:
            self.output_folder_label.setText("No output folder selected")
            self.output_folder_label.setToolTip("")

    def reset_form(self):
        current_preset = self.preset_combo.currentText()
        self.load_preset(current_preset)
    
    def reset_paradigm(self):
        current_preset = self.preset_combo.currentText()
        file_type_field = next((segment for segment in FILENAME_CONFIG[current_preset]["segments"] if segment["name"] == "file_type"), None)
        
        if file_type_field:
            file_type_widget = self.inputs["file_type"]["widget"]
            if isinstance(file_type_widget, QComboBox):
                file_type_widget.setCurrentIndex(0)  # Reset to first option
            elif isinstance(file_type_widget, QLineEdit):
                file_type_widget.clear()
            
            self.validate_field("file_type")
            self.update_preview()
            self.update_json_tab()
            self.clear_paradigm_notes()
        else:
            QMessageBox.warning(self, "No Paradigm Field", "No paradigm field found in the current preset.")

    def change_paradigm(self):
        current_preset = self.preset_combo.currentText()
        file_type_field = next((segment for segment in FILENAME_CONFIG[current_preset]["segments"] if segment["name"] == "file_type"), None)
        
        if file_type_field:
            file_type_widget = self.inputs["file_type"]["widget"]
            if isinstance(file_type_widget, QComboBox):
                current_index = file_type_widget.currentIndex()
                next_index = (current_index + 1) % file_type_widget.count()
                file_type_widget.setCurrentIndex(next_index)
            elif isinstance(file_type_widget, QLineEdit):
                file_type_widget.clear()
            
            self.validate_field("file_type")
            self.update_preview()
            self.update_json_tab()
            self.clear_paradigm_notes()
            
            # Switch to the first tab
            self.tab_widget.setCurrentIndex(0)
            
            # Reset paradigm
            self.reset_paradigm()
        else:
            QMessageBox.warning(self, "No File Type Field", "No file type field found in the current preset.")

    def clear_paradigm_notes(self):
        self.paradigm_notes_text.clear()
        if hasattr(self, 'json_data'):
            self.json_data['paradigm_notes'] = ''

    def clear_notes(self):
        self.session_notes_text.clear()
        self.paradigm_notes_text.clear()
        if hasattr(self, 'json_data'):
            self.json_data['session_notes'] = ''
            self.json_data['paradigm_notes'] = ''

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FilenameGenerator()
    window.show()
    sys.exit(app.exec())