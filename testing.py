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


    
    
class SessionInfoForm(QWidget):  # Inherit from QWidget instead of QMainWindow
    
    confirm_session_info_signal = pyqtSignal()  # Signal to emit when lock button is clicked

    def __init__(self, data_model=None, parent=None):
        super().__init__(parent)

        # Init data model 
        self.data_model = data_model

        # Inputs and indicator labels
        self.inputs = {}
        self.indicators = {}  

        # Layout setup
        self.layout = QVBoxLayout(self)  

        # Preset combo box
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(self.data_model.CONFIG_DICT.keys())
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

        # Lock filename button
        self.confirm_session_button = QPushButton("Confirm Session Information")
        self.confirm_session_button.clicked.connect(self.confirm_session_info_signal.emit)
        self.confirm_session_button.setEnabled(False)  # not enabled until fields are validated
        self.confirm_session_button.setStyleSheet("""
            QPushButton:disabled {
                background-color: #A0A0A0;
            }
        """)
        self.layout.addWidget(self.confirm_session_button)
        
        # Load first preset
        self.reset_form()
        

    def get_current_study(self):
        """Get current study preset from combobox text. Could alternatively get from data model?"""
        return self.preset_combo.currentText()

        
    def reset_form(self):
        """Reset to default form and current study """        
        self.preset_combo.setCurrentIndex(0)
        self.load_preset(self.get_current_study())
        self.update_session_info() # should be blank
        
        
    def update_session_info(self):
        """Update data model with currently entered session information"""
        cur_session_info = self.data_model.session_info 
        for key in cur_session_info:
            value = self.get_input_value(key)
            self.data_model.session_info[key] = value
        print(self.data_model.session_info)
        
        
    def load_preset(self, preset):
        """Load UI elements of preset from configuration dict"""
        self.clear_form()
        
        # Load preset from data model
        preset = self.data_model.CONFIG_DICT[preset]

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

        total_fields = len(preset)
        fields_per_column = (total_fields + 1) // 2  # Round up division
        field_count = 0

        for field_name, field in preset.items():
            if field["type"] == "hidden":
                continue  # Skip hidden fields

            widget = self.create_widget(field)
            row_layout = QVBoxLayout()  # Changed to QVBoxLayout

            # Add error label
            error_label = QLabel()
            error_label.setStyleSheet("color: red; font-size: 12px;")
            error_label.setVisible(False)
            row_layout.addWidget(error_label)

            widget_row = QHBoxLayout()
            widget_row.addWidget(widget)
            widget_row.addStretch()  # Add stretch to push widget to the left

            if field.get("editable", True):
                indicator = QLabel("❌")  # Red X
                indicator.setStyleSheet("color: red; font-size: 16px;")
                self.indicators[field_name] = indicator
                widget_row.addWidget(indicator)

            row_layout.addLayout(widget_row)

            if field_count < fields_per_column:
                left_form.addRow(field["label"], row_layout)
            else:
                right_form.addRow(field["label"], row_layout)

            self.inputs[field_name] = {"widget": widget, "error_label": error_label}
            field_count += 1

        # Adjust the scroll content widget's layout
        self.scroll_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_content.setLayout(columns_layout)

        # Set initial preview template
        self.update_preview(initial=True)

        # Validate all fields after loading
        for field_name, field in preset.items():
            if field["type"] != "hidden":
                self.validate_field(field_name)


    def create_widget(self, field):
        """Create widget configuration document"""
        if field["type"] == "text":
            widget = QLineEdit()
            widget.setMinimumHeight(30)
            if "default" in field:
                widget.setText(field["default"])
            if "editable" in field and not field["editable"]:
                widget.setReadOnly(True)
                widget.setStyleSheet("font-size: 14px; background-color: #F0F0F0;")  # Grey out non-editable fields
            else:
                widget.textChanged.connect(lambda text, name=field["name"]: self.validate_field(name))
                widget.setStyleSheet("font-size: 14px;")
        elif field["type"] == "combo":
            widget = QComboBox()
            widget.setMinimumHeight(30)
            widget.addItems(field["options"])
            if field.get("editable", True):
                widget.currentTextChanged.connect(lambda text, name=field["name"]: self.validate_field(name))
                widget.focusOutEvent = lambda event, name=field["name"]: self.validate_field(name)
            else:
                widget.setEnabled(False)
            widget.setStyleSheet("font-size: 14px;")
        elif field["type"] == "date":
            widget = QDateEdit()
            widget.setMinimumHeight(30)
            widget.setCalendarPopup(True)
            widget.setDate(QDate.currentDate())
            if field.get("editable", True):
                widget.dateChanged.connect(lambda date, name=field["name"]: self.validate_field(name))
            else:
                widget.setReadOnly(True)
            widget.setStyleSheet("font-size: 14px;")
        elif field["type"] == "spinbox":
            widget = QSpinBox()
            widget.setMinimumHeight(30)
            widget.setMinimum(0)
            widget.setMaximum(99999)
            if field.get("editable", True):
                widget.valueChanged.connect(lambda value, name=field["name"]: self.validate_field(name))
            else:
                widget.setReadOnly(True)
            widget.setStyleSheet("font-size: 14px;")
        elif field["type"] == "hidden":
            widget = QLineEdit()
            widget.setVisible(False)
        return widget
    
    
    def clear_form(self):
        """Clear and reset all form elements, clear input and indicators. Only used by load_preset so could be hidden?"""
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
        """Validate field using regex from configuration dict, then update UI"""
        preset = self.data_model.CONFIG_DICT[self.get_current_study()]
        field = preset.get(field_name, None)
        if field and field["type"] != "hidden":
            widget = self.inputs[field_name]["widget"]
            error_label = self.inputs[field_name]["error_label"]
            value = self.get_input_value(field_name)

            is_valid = re.match(field["validation"], value) is not None

            if is_valid:
                widget.setStyleSheet("border: 1px solid green;")
                self.update_indicator(field_name, True)
                error_label.setVisible(False)
            else:
                widget.setStyleSheet("border: 1px solid red;")
                self.update_indicator(field_name, False)
                error_label.setText(field.get("error_message", "This field is required"))
                error_label.setVisible(True)
        self.update_preview()
        

    def update_indicator(self, field_name, is_valid):
        """Update form to reflect indicators"""
        if field_name in self.indicators:
            self.indicators[field_name].setText("✅" if is_valid else "❌")
            self.indicators[field_name].setStyleSheet("color: green;" if is_valid else "color: red;")


    def get_input_value(self, name):
        """Get value from given element"""
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
    
        



    # ALL OF THIS I AM UNSURE ABOUT 

    def update_preview(self, initial=False):
        filename_parts = []
        preset = self.data_model.CONFIG_DICT[self.get_current_study()]
        all_valid = True

        for field_name, field in preset.items():
            if field["type"] == "hidden":
                continue  # Skip hidden fields
            if initial:
                value = f"<{field_name}>"
            else:
                value = self.get_input_value(field_name)
                if "validation" in field:
                    if not re.match(field["validation"], value):
                        all_valid = False
            filename_parts.append(value)

        filename = "_".join(filename_parts)

        if all_valid:
            self.confirm_session_button.setEnabled(True)
        else:
            self.confirm_session_button.setEnabled(False)
        print(filename)





        
        
        
   

        
    

    





class FileInputForm(QWidget):
    
    confirm_file_info_signal = pyqtSignal()
    
    def __init__(self, data_model=None, parent=None):
        super().__init__(parent)

        # Set data model
        self.data_model = data_model
        
        # List to hold all sections
        self.sections = []

        # Main layout
        self.layout = QVBoxLayout(self)

        # Text file input
        self.notes_button = QPushButton("Upload Notes (.txt) file")
        self.notes_button.clicked.connect(self.upload_notes_file)
        self.notes_label = QLabel("No file selected")
        self.layout.addWidget(self.notes_button)
        self.layout.addWidget(self.notes_label)
        
        # Container for sections
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)
        
        # Add paradigm button
        self.add_button = QPushButton("Add Additional Paradigms")
        self.add_button.clicked.connect(self.add_section)
        self.add_button.setEnabled(False)
        self.layout.addWidget(self.add_button)
        
        # Add confirm session info button
        self.confirm_file_button = QPushButton("Confirm File Info")
        self.confirm_file_button.clicked.connect(self.confirm_file_info_signal)
        self.confirm_file_button.setEnabled(False)
        self.layout.addWidget(self.confirm_file_button)
        
        # Add initial section
        self.add_section()  # Initialize with one section


    def add_section(self):
        """Add section for EEG paradigm. Contains paradigm combobox and buttons for MFF and RAW file selection"""
        # Layout 
        form_layout = QFormLayout()

        # Paradigm selection combo box
        paradigm_combo = QComboBox()
        paradigm_combo.addItems(self.data_model.get_current_paradigms())
        paradigm_combo.currentIndexChanged.connect(self.check_form_completion)
        form_layout.addRow(QLabel(f"Paradigm {len(self.sections) + 1}:"), paradigm_combo)

        # RAW file button
        raw_button = QPushButton("Upload .RAW file")
        raw_label = QLabel("No file selected")
        raw_button.clicked.connect(lambda _, label=raw_label: self.upload_raw(label))
        form_layout.addRow(raw_button, raw_label)

        # MFF file button
        mff_button = QPushButton("Upload .MFF folder")
        mff_label = QLabel("No folder selected")
        mff_button.clicked.connect(lambda _, label=mff_label: self.upload_mff(label))
        form_layout.addRow(mff_button, mff_label)

        # Sections for each paradigm using QWidgets
        section_widget = QWidget()
        section_widget.setLayout(form_layout)
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

        # Make sure buttons are updated 
        self.check_form_completion()


    def upload_raw(self, raw_label):
        """File dialog for selecting RAW file"""
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Select .RAW file", "", "RAW Files (*.raw);;All Files (*)", options=options)
        if filename:
            raw_label.setText(filename)
        self.check_form_completion()  # Update buttons 


    def upload_mff(self, mff_label):
        """File dialog for selecting MFF file"""
        options = QFileDialog.Options()
        folder = QFileDialog.getExistingDirectory(self, "Select .MFF folder", "", options=options)
        if folder:
            mff_label.setText(folder)
        self.check_form_completion()  # Update buttons


    def check_form_completion(self):
        """Enable or disable buttons depending on if file selection is complete for each section."""
        # Check if notes present
        if self.notes_label.text() == "No file selected":
            self.add_button.setEnabled(False)
            self.confirm_file_button.setEnabled(False)
            return
        # Check if all sections are complete (selected paradigm + loaded raw + loaded mff)
        all_sections_complete = all(
            section["paradigm_combo"].currentIndex() != 0 and
            section["raw_label"].text() != "No file selected" and
            section["mff_label"].text() != "No folder selected"
            for section in self.sections
        )
        self.add_button.setEnabled(all_sections_complete)
        self.confirm_file_button.setEnabled(all_sections_complete)
        
        
    def upload_notes_file(self):
        """Open file dialog for user to select a notes file"""
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select a file",
            "",
            "Text Files (*.txt;*.rtf);;All Files (*)",
            options=options
        )
        if filename:
            self.notes_label.setText(filename)
            self.check_form_completion()
        
        
    def clear_files(self):
        """Clear all elements in form""" 
        for section in self.sections:
            section["widget"].deleteLater()
        self.sections = []
        self.add_section() # add initial section   
        self.add_button.setEnabled(False) # reset buttons 
        self.confirm_file_button.setEnabled(False)

                    

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize data model
        self.data_model = DataModel()
        
        # Set stylesheet
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
        

        # Create the menu
        self.init_menu()
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # Init session info tab
        self.session_info_tab = SessionInfoForm(self.data_model)
        self.tab_widget.addTab(self.session_info_tab, "Session Information")
        
        self.session_info_tab.confirm_session_info_signal.connect(self.confirm_session_info)

        # Init file upload tab  
        self.file_upload_tab = FileInputForm(self.data_model)
        self.tab_widget.addTab(self.file_upload_tab, "File Upload")
        self.tab_widget.setTabEnabled(1, False)  # Disable second tab initially
        self.tab_widget.setCurrentIndex(0)
        
        self.file_upload_tab.confirm_file_info_signal.connect(self.confirm_file_info)


    def init_menu(self):
        """Create menu bar with reset form and select output items"""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        # Select output folder
        select_output_action = QAction("Select Output Folder", self)
        select_output_action.triggered.connect(self.select_output_folder)
        file_menu.addAction(select_output_action)

        # Reset form
        reset_action = QAction("Reset Form", self)
        reset_action.triggered.connect(self.reset_form)
        file_menu.addAction(reset_action)


    def select_output_folder(self):
        """Store output folder in data_model when menu item is selected"""
        folder = QFileDialog.getExistingDirectory(self, "Select File Output Folder")
        if folder:
            self.data_model.file_output_folder = folder


    def reset_form(self):
        """Reset all fields and data model"""
        # Reset the session info tab and file tab
        self.session_info_tab.reset_form()
        self.file_upload_tab.clear_files()

        # Disable the second tab
        self.tab_widget.setTabEnabled(1, False)
        self.tab_widget.setCurrentIndex(0)
        
        # Clear data amodel
        self.data_model.clear_data()


    def confirm_session_info(self):
        """When session confirm button is clicked: double check validity, update model, and swap to second tab"""
        all_valid = all(self.session_info_tab.indicators[field].text() == "✅" for field in self.session_info_tab.indicators)
        if all_valid:
            # Update data model with session information
            self.session_info_tab.update_session_info()
            # Swap to second tab            
            self.file_upload_tab.clear_files()
            self.tab_widget.setTabEnabled(1, True)
            self.tab_widget.setCurrentIndex(1)
        else:
            QMessageBox.warning(self, "Validation Error", "Check that the fields are valid. This should never happen, if you see this something is really wrong lol")
            
            
    def confirm_file_info(self):
        """When file confirm button is pressed: double check validity, then process files"""        
        all_valid = all(
            section["paradigm_combo"].currentIndex() != 0 and
            section["raw_label"].text() != "No file selected" and
            section["mff_label"].text() != "No folder selected"
            for section in self.file_upload_tab.sections
        ) and self.file_upload_tab.notes_label != "No file selected"
        if all_valid:
            print("confirm")

            # get deid
            # add deid entry
            
            # copy file
            # copy other file
            
            # rest data  
        
        else:
            QMessageBox.warning(self, "Validation Error", "Check that the fields are valid. This should never happen, if you see this something is really really wrong lol")






class DataModel:
    
    # DEID_EEG_BACKUP_DIRECTORY = config['DEID_EEG_BACKUP_DIRECTORY']
    # FULLNAME_EEG_BACKUP_DIRECTORY = config['FULLNAME_EEG_BACKUP_DIRECTORY']
    # DEID_LOG_FILEPATH = config['DEID_LOG_FILEPATH']
    # FILE_TYPE_TO_COLUMN = config['FILE_TYPE_TO_COLUMN']
    
    def __init__(self):

        # Configuration dictionary containing presets
        config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'filename_config.json') 
        with open(config_file_path, 'r') as f:
            self.CONFIG_DICT = json.load(f)

        # Output folder to save renamed files
        self.file_output_folder = 'D:/eeg_backup/'

        # Notes file path         
        self.notes_file = ""
        
        # Session information  
        self.session_info = {
            'study': None,
            'visit_number': None,
            'subject_id': None,
            'subject_initials': None,
            'date': None,
            'location': None,
            'net_serial_number': None,
            'audio_source': None,
            'cap_type': None,
            'other_notes': None
        }

        # List of dictionaries containing EEG file paradigm and file paths
        self.eeg_file_list = []
        
        # Init deid log
        self.deid_log = pd.DataFrame()
        #self.load_deid_log(self.DEID_LOG_FILEPATH)
        
        # DeID for current session
        self.deid = None
        
        
    def get_current_paradigms(self):
        """Get list of paradigms for current study preset"""
        current_study = self.session_info['study']
        return self.CONFIG_DICT[current_study]['paradigm']['options']
        

    def clear_data(self):
        """Reset data model"""
        self.__init__()
        
        
    def load_deid_log(self, file_path):
        """Read deid log into pandas table"""
        if os.path.exists(file_path):
            #df = pd.read_excel(file_path)
            self.deid_log = pd.read_csv(file_path)
        else:
            raise FileNotFoundError(f"The file {file_path} does not exist.")        
  

  
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
                
        QMessageBox.information(self, "title", "DEID files are copied")

        
        
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
                
        QMessageBox.information(self, "title", "Non-DEID files are copied")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
