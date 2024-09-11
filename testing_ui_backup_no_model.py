import sys
import json
import re
import os
import shutil
import pandas as pd 
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QFormLayout, QWidget, QLabel, QLineEdit, QComboBox, 
                             QPushButton, QDateEdit, QCheckBox, QSpinBox, QMessageBox,
                             QScrollArea, QFrame, QToolTip, QFileDialog, QTabWidget,
                             QTextEdit, QSizePolicy, QMenuBar, QMenu, QGraphicsOpacityEffect, QSplitter,
                             QAction) 
from PyQt5.QtCore import (Qt, pyqtSignal, QDate, QTimer, QPoint, QPropertyAnimation, 
                          QEasingCurve, QSettings, QAbstractAnimation)
from PyQt5.QtGui import (QFont, QColor, QPalette, QIcon, QPixmap, 
                         QCursor, QDesktopServices, QTextCursor)



# Read config from file
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'filename_config.json'), 'r') as f:
    CONFIG_DICT = json.load(f)
    
    
class SessionInfoForm(QWidget):  # Inherit from QWidget instead of QMainWindow
    
    lock_session_info_signal = pyqtSignal()  # Signal to emit when lock button is clicked


    def __init__(self):
        
        super().__init__()

        self.indicators = {}  # Store indicator labels

        # Layout setup
        self.layout = QVBoxLayout(self)  

        # Preset combo box
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(CONFIG_DICT.keys())
        self.preset_combo.currentTextChanged.connect(self.load_preset)
        self.layout.addWidget(QLabel("Select Study Preset:"))
        self.layout.addWidget(self.preset_combo)

        # Scroll area for input fields
        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet("background-color: white")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_area.setMinimumHeight(400) 
        self.scroll_content = QWidget()
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

        self.inputs = {}



   

        # Lock filename button
        self.lock_button = QPushButton("Lock Filename")
        self.lock_button.clicked.connect(self.lock_session_info_signal.emit)
        self.lock_button.setEnabled(False)  # Initially set to disabled
        self.lock_button.setStyleSheet("""
            QPushButton:disabled {
                background-color: #A0A0A0;
            }
        """)
        self.layout.addWidget(self.lock_button)
        
        
        
        # Load first preset
        self.reset_form()

        
        
        
        
        
    def load_preset(self, preset_name):
        self.clear_form()
        preset = CONFIG_DICT[preset_name]
        
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
        preset = CONFIG_DICT[self.preset_combo.currentText()]
        segment = next((s for s in preset["segments"] if s["name"] == field_name), None)
        if segment and segment["type"] != "hidden":
            widget = self.inputs[field_name]["widget"]
            error_label = self.inputs[field_name]["error_label"]
            value = self.get_input_value(field_name)
                       
            is_valid = re.match(segment["validation"], value) is not None
            
            if is_valid:
                if segment["type"] == "combo":
                    widget.setStyleSheet("border: 1px solid green; font-size: 14px;")
                else:
                    widget.setStyleSheet("border: 1px solid green;")
                widget.setStyleSheet("border: 1px solid green;")
                    
                self.update_indicator(field_name, True)
                error_label.setVisible(False)
            else:
                widget.setStyleSheet("border: 1px solid red;")
                self.update_indicator(field_name, False)
                error_label.setText(segment["error_message"] if "error_message" in segment else "This field is required")
                error_label.setVisible(True)
        self.update_preview()

        
        
    def update_indicator(self, field_name, is_valid):
        if field_name in self.indicators:
            self.indicators[field_name].setText("✅" if is_valid else "❌")
            self.indicators[field_name].setStyleSheet("color: green;" if is_valid else "color: red;")

    def update_preview(self, initial=False):
        filename_parts = []
        preset = CONFIG_DICT[self.preset_combo.currentText()]
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
            self.lock_button.setEnabled(True)
        else:
            self.lock_button.setEnabled(False)
        

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




    def reset_form(self):
        current_preset = self.preset_combo.currentText()
        self.load_preset(current_preset)
    


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
            QPushButton:disabled {
                background-color: #B0B0B0;  
                color: #7F7F7F;      
            }
            QCheckBox {
                font-size: 14px;
                color: #1A3A54;
            }
        """)
        
        self.setWindowTitle("Main Application")
        self.setGeometry(100, 100, 800, 600)
        
        # Create a QTabWidget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # Add the first tab (assuming it's already defined in the original code)
        self.session_info_tab = SessionInfoForm()
        self.tab_widget.addTab(self.session_info_tab, "Session Information")
        
        self.session_info_tab.lock_session_info_signal.connect(self.lock_session_info)

        # Replace the second tab with the new one
        self.file_tab = FileInputForm()
        self.tab_widget.addTab(self.file_tab, "File Upload")
        self.tab_widget.setTabEnabled(1, False)  # Disable second tab initially



    def validate_all_fields(self):
        preset = CONFIG_DICT[self.preset_combo.currentText()]
        for segment in preset["segments"]:
            if segment.get("editable", True):
                self.validate_field(segment["name"])
        
        all_valid = all(self.session_info_tab.indicators[field].text() == "✅" for field in self.session_info_tab.indicators)
        self.lock_button.setEnabled(all_valid)
        self.tab_widget.setTabEnabled(1, all_valid)

    def lock_session_info(self):
        all_valid = all(self.session_info_tab.indicators[field].text() == "✅" for field in self.session_info_tab.indicators)
        if all_valid:
            self.tab_widget.setTabEnabled(1, True)
            self.tab_widget.setCurrentIndex(1)
        else:
            QMessageBox.warning(self, "Validation Error", "Please correct all fields before locking the filename.")





class FileInputForm(QWidget):
    def __init__(self):
        super().__init__()

        # Main layout
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
        
        # List to hold all sections
        self.sections = []

        # Add initial section
        self.addSection()  # Initialize with one section

    def uploadTXT(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select a file",
            "",
            "Text Files (*.txt;*.rtf);;All Files (*)",
            options=options
        )

        if filename:
            self.txt_label.setText(filename)
            self.checkEnableAddButton()

    def addSection(self):
        index = len(self.sections)
        # Create UI components for a new section dynamically
        paradigm_combo = QComboBox()
        paradigm_combo.addItems(["Paradigm 1", "Paradigm 2", "Paradigm 3"])  # Add your paradigms here
        
        raw_button = QPushButton("Upload .RAW file")
        raw_label = QLabel("No file selected")
        
        mff_button = QPushButton("Upload .MFF folder")
        mff_label = QLabel("No folder selected")
        
        # Connect buttons to their respective handlers
        raw_button.clicked.connect(lambda _, label=raw_label: self.uploadRAW(label))
        mff_button.clicked.connect(lambda _, label=mff_label: self.uploadMFF(label))

        # Form layout for the section
        form_layout = QFormLayout()
        form_layout.addRow(QLabel(f"Paradigm {index + 1}:"), paradigm_combo)
        form_layout.addRow(raw_button, raw_label)
        form_layout.addRow(mff_button, mff_label)

        # Create a QWidget for the section and set the layout
        section_widget = QWidget()
        section_widget.setLayout(form_layout)

        # Add the section widget to the scroll layout
        self.sections.append({
            "paradigm_combo": paradigm_combo,
            "raw_label": raw_label,
            "mff_label": mff_label,
            "widget": section_widget
        })
        self.scroll_layout.addWidget(section_widget)

        # Add a divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        self.scroll_layout.addWidget(divider)

        self.checkEnableAddButton()

    def uploadRAW(self, raw_label):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Select .RAW file", "", "RAW Files (*.raw);;All Files (*)", options=options)
        if filename:
            raw_label.setText(filename)
        self.checkEnableAddButton()  # Notify parent to check enable status

    def uploadMFF(self, mff_label):
        options = QFileDialog.Options()
        folder = QFileDialog.getExistingDirectory(self, "Select .MFF folder", "", options=options)
        if folder:
            mff_label.setText(folder)
        self.checkEnableAddButton()  # Notify parent to check enable status

    def checkEnableAddButton(self):
        # Check if the main .txt file has been selected
        if self.txt_label.text() == "No file selected":
            self.add_button.setEnabled(False)
            return

        # Get the latest section
        latest_section = self.sections[-1]
        
        # Check if the latest section's paradigm is selected
        if latest_section["paradigm_combo"].currentIndex() == -1:
            self.add_button.setEnabled(False)
            return
        
        # Check if a .RAW file has been selected in the latest section
        if latest_section["raw_label"].text() == "No file selected":
            self.add_button.setEnabled(False)
            return
        
        # Check if a .MFF folder has been selected in the latest section
        if latest_section["mff_label"].text() == "No folder selected":
            self.add_button.setEnabled(False)
            return
        
        # If all checks pass, enable the add_button
        self.add_button.setEnabled(True)




class DataModel:
    
    def __init__(self):

        # Load global variables from JSON file
        with open(self.CONFIG_PATH, 'r') as file:
            config = json.load(file)

        self.EEG_PARADIGMS = config['EEG_PARADIGMS']
        self.STUDY_NAMES = config['STUDY_NAMES']
        self.EEG_LOCATIONS = config['EEG_LOCATIONS']
        self.DEID_EEG_BACKUP_DIRECTORY = config['DEID_EEG_BACKUP_DIRECTORY']
        self.FULLNAME_EEG_BACKUP_DIRECTORY = config['FULLNAME_EEG_BACKUP_DIRECTORY']
        self.DEID_LOG_FILEPATH = config['DEID_LOG_FILEPATH']
        self.FILE_TYPE_TO_COLUMN = config['FILE_TYPE_TO_COLUMN']

        self.session_data = {
            'study': None,
            'visit_number': None,
            'subject_id': None,
            'subject_initials': None,
            'date': None,
            'location': None,
            'net_serial_number': None,
            'speakers': None,
            'babycap': None,
            'other_notes': None
        }
        self.eeg_data = [] 
        
        
        self.deid_log = pd.DataFrame()
        
        self.load_deid_log(self.DEID_LOG_FILEPATH)
        
        
        self.deid = None

    def display_message_box(self, message):
        msg_box = QMessageBox()
        msg_box.setText(message)
        msg_box.exec_()
        
    def clear_data(self):
        self.__init__()
        self.display_message_box("Data cleared")

    def load_deid_log(self, file_path):
        if os.path.exists(file_path):
            #df = pd.read_excel(file_path)
            self.deid_log = pd.read_csv(file_path)
        else:
            raise FileNotFoundError(f"The file {file_path} does not exist.")        
  
  
    def set_session_data(self, data_dict):
        self.session_data = data_dict

  
    def add_eeg_data(self, data_dict):
        self.eeg_data.append(data_dict)

    
    def get_deid_from_log(self):
        
        # idk 
        df = self.deid_log.copy()
        
        # Find first empty row (ignoring first column)
        empty_rows = df.loc[:, df.columns[1:]].isna().all(axis=1)
        empty_row_index = empty_rows.idxmax() if empty_rows.any() else len(df)
        
        # get deid
        deid = df.at[empty_row_index, df.columns[0]]

        # set deid 
        self.deid = deid
        
        return deid, empty_row_index


    def save_to_csv(self, file_path):
   
        
        # idk
        df = self.deid_log.copy()
        
        
        _, empty_row_index = self.get_deid_from_log()
        
        
        # Manually assign values to the DataFrame columns from data_dict
        if empty_row_index < len(df):
            # Fill out the identified empty row
            df.at[empty_row_index, 'Study'] = self.session_data['study']
            df.at[empty_row_index, 'Subject ID'] = self.session_data['subject_id']
            df.at[empty_row_index, 'Visit Num'] = self.session_data['visit_number']
            df.at[empty_row_index, 'Visit Date'] = self.session_data['date']
            df.at[empty_row_index, 'Initials'] = self.session_data['subject_initials']
            df.at[empty_row_index, 'Location'] = self.session_data['location']
            df.at[empty_row_index, 'Net Serial Number'] = self.session_data['net_serial_number']
            df.at[empty_row_index, 'Notes'] = self.session_data['other_notes']        
        else:
            raise Exception("No empty rows available in the CSV")
                
                
        for eeg_file_dict in self.eeg_data:
            cur_file_type = eeg_file_dict['File type']
            column_name = self.FILE_TYPE_TO_COLUMN.get(cur_file_type, None)
            
            if column_name:
                if pd.isna(df.at[empty_row_index, column_name]):
                    df.at[empty_row_index, column_name] = 1
                else:
                    df.at[empty_row_index, column_name] += 1
                

        
        # Update deid log
        df.to_csv(file_path, index=False)
        
        
                     
    def save_deid_files(self, destination_folder):
        file_type_counter = {}

        # Loop through all files
        for row in self.eeg_data:
            src_path = row['RAW file path']
            if src_path:
                file_type = row['File type']
                
                # Initialize or update the counter for this file type
                if file_type not in file_type_counter:
                    file_type_counter[file_type] = 1
                else:
                    file_type_counter[file_type] += 1
                
                # Create base file name with optional counter
                counter = file_type_counter[file_type] if file_type_counter[file_type] > 1 else ""
                base_name = f"{self.deid:04}_{file_type}{counter}"

                # Add additional notes if needed
                if self.session_data['babycap']:
                    base_name += "_babycap"
                if self.session_data['speakers'] and file_type != 'rest':
                    base_name += "_speakers"


                # Create final file path
                dst_path = os.path.join(destination_folder, base_name + os.path.splitext(src_path)[1])

                # Make copy at destination folder
                shutil.copy2(src_path, dst_path)        
                
        self.display_message_box("DEID files are copied")

        
        
    def copy_and_rename_files(self, destination_folder):
        file_type_counter = {}
        
        
        dat = self.session_data

        # Loop through all files
        for row in self.eeg_data:
            src_path = row['RAW file path']
            if src_path:
                file_type = row['File type']
                
                # Initialize or update the counter for this file type
                if file_type not in file_type_counter:
                    file_type_counter[file_type] = 1
                else:
                    file_type_counter[file_type] += 1
                
                # Create base file name with optional counter
                counter = file_type_counter[file_type] if file_type_counter[file_type] > 1 else ""
                base_name = f"{dat['study']}_{dat['visit_number']}_{file_type}{counter}_{dat['subject_id']}_{dat['subject_initials']}_{dat['date']}"

                # Add additional notes if needed
                if dat['babycap']:
                    base_name += "_babycap"
                if dat['speakers'] and file_type != 'rest':
                    base_name += "_speakers"

                # Create final file path
                dst_path = os.path.join(destination_folder, base_name + os.path.splitext(src_path)[1])

                # Make copy at destination folder
                shutil.copy2(src_path, dst_path)
                
        self.display_message_box("Non-DEID files are copied")





if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
