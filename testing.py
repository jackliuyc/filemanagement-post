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

# The FileSection class and MainWindow class remain unchanged

# Read config from file
with open('filename_config.json', 'r') as f:
    FILENAME_CONFIG = json.load(f)
    
    
class SessionInfoForm(QMainWindow):
      
#class FilenameGenerator(QMainWindow):

    def __init__(self):
        super().__init__()
        
        # Window setup
        self.setWindowTitle("EEG Filename Generator")
        self.setGeometry(100, 100, 1000, 600)
        
        
        
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        
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
        
        self.setWindowTitle("Main Application")
        self.setGeometry(100, 100, 800, 600)
        
        # Create a QTabWidget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Add the first tab (assuming it's already defined in the original code)
        self.first_tab = SessionInfoForm()
        self.tabs.addTab(self.first_tab, "First Tab Title")

        # Replace the second tab with the new one
        self.second_tab = FileInputForm()
        self.tabs.addTab(self.second_tab, "File Input Form")




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

class FileInputForm(QWidget):
    def __init__(self):
        super().__init__()

        # Your provided MainWindow code here, adapted as a QWidget
        self.layout = QVBoxLayout(self)

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
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
