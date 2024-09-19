import sys
import json
import re
import os
import shutil
import pandas as pd
from datetime import datetime

from openpyxl import load_workbook


from PyQt5.QtCore import pyqtSignal, QDate
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QFormLayout, QWidget, 
    QLabel, QLineEdit, QComboBox, QPushButton, QDateEdit, QSpinBox, 
    QMessageBox, QScrollArea, QFrame, QFileDialog, QTabWidget, 
    QSizePolicy, QAction
)

    
class SessionInfoForm(QWidget):  
    
    # signal to main window when session info is confirmed 
    confirm_session_info_signal = pyqtSignal()  

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

        # Validate all fields after loading  
        self.validate_all_fields()


    def create_widget(self, field):
        """Create widget and connect relevant signals to validate_all_fields."""
        if field["type"] == "text":
            widget = QLineEdit()
            widget.setMinimumHeight(30)
            if "default" in field:
                widget.setText(field["default"])
            if "editable" in field and not field["editable"]:
                widget.setReadOnly(True)
            else:
                widget.textChanged.connect(self.validate_all_fields)  # Connect to validate_all_fields
        elif field["type"] == "combo":
            widget = QComboBox()
            widget.setMinimumHeight(30)
            widget.addItems(field["options"])
            if field.get("editable", True):
                widget.currentTextChanged.connect(self.validate_all_fields)  # Connect to validate_all_fields
            else:
                widget.setEnabled(False)
        elif field["type"] == "date":
            widget = QDateEdit()
            widget.setMinimumHeight(30)
            widget.setCalendarPopup(True)
            widget.setDate(QDate.currentDate())
            if field.get("editable", True):
                widget.dateChanged.connect(self.validate_all_fields)  # Connect to validate_all_fields
            else:
                widget.setReadOnly(True)
        elif field["type"] == "spinbox":
            widget = QSpinBox()
            widget.setMinimumHeight(30)
            widget.setMinimum(0)
            widget.setMaximum(99999)
            if field.get("editable", True):
                widget.valueChanged.connect(self.validate_all_fields)  # Connect to validate_all_fields
            else:
                widget.setReadOnly(True)
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
    

    def validate_all_fields(self):
        """Validate all fields and update the overall UI state based on validation results."""
        preset = self.data_model.CONFIG_DICT[self.get_current_study()]
        all_valid = True

        # Loop over all fields in the preset
        for field_name, field in preset.items():
            if field["type"] == "hidden":
                continue  # Skip hidden fields

            # Get the current value of the field
            value = self.get_input_value(field_name)

            # Get info from config dict for validation
            widget = self.inputs[field_name]["widget"]
            error_label = self.inputs[field_name]["error_label"]

            # Check if the field's value matches the regex validation
            if "validation" in field:
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
                    all_valid = False  # Mark form as invalid if any field is invalid

        # Enable or disable the confirm button based on the overall validation result
        self.confirm_session_button.setEnabled(all_valid)

        
    




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
        paradigm_combo.addItems(self.data_model.get_list_of_current_paradigms())
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
        self.check_form_completion()  # Check validity and update buttons 


    def upload_mff(self, mff_label):
        """File dialog for selecting MFF file"""
        options = QFileDialog.Options()
        folder = QFileDialog.getExistingDirectory(self, "Select .MFF folder", "", options=options)
        if folder:
            mff_label.setText(folder)
        self.check_form_completion()  # Check validity and update buttons 


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
            self.data_model.notes_file = filename
            self.notes_label.setText(filename)
            self.check_form_completion()
        
        
    def clear_files(self):
        """Clear all elements in form"""
        # Remove all widgets and dividers from the scroll layout
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Clear and re-init first section
        self.sections = []
        self.add_section()
        
        # Reset buttons
        self.add_button.setEnabled(False)
        self.confirm_file_button.setEnabled(False)


    def update_file_info(self):
        """Update data_model user input fields."""
        # Clear the existing eeg_file_info
        self.data_model.eeg_file_info = []

        # Loop over each section 
        for section in self.sections:
            
            # Dictionary of file info
            paradigm = section['paradigm_combo'].currentText()
            raw_file = section['raw_label'].text()
            mff_folder = section['mff_label'].text()
            file_info = {
                'paradigm': paradigm,
                'raw_file': raw_file if raw_file != "No file selected" else None,
                'mff_folder': mff_folder if mff_folder != "No folder selected" else None
            }
            self.data_model.eeg_file_info.append(file_info)
                    







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
                font-size: 16px;
                color: #1A3A54;
            }
            QComboBox, QLineEdit, QDateEdit, QSpinBox {
                font-size: 16px;
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
                font-size: 16px;
                color: #1A3A54;
            }
            QTabBar::tab {
                font-size: 16px;
                min-width: 180;  
                padding: 5px; 
                border: 1px solid #D1D9E6;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                border-bottom-color: #FFFFFF;
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
        
        # Slot for session info confirm signal
        self.session_info_tab.confirm_session_info_signal.connect(self.confirm_session_info)

        # Init file upload tab  
        self.file_upload_tab = FileInputForm(self.data_model)
        self.tab_widget.addTab(self.file_upload_tab, "File Upload")
        self.tab_widget.setTabEnabled(0, True) # Enable first tab
        self.tab_widget.setTabEnabled(1, False)  # Disable second tab initially
        self.tab_widget.setCurrentIndex(0)
        
        # Slot for file info confirm signal 
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
        """Select new output folder for files"""
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
        
        # Swap to first tab
        self.tab_widget.setTabEnabled(0, True)
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
            # Disable first tab (have to reset whole session)
            self.tab_widget.setTabEnabled(0, False)
        else:
            QMessageBox.warning(self, "Validation Error", "Check that the fields are valid. If you see this something is really really wrong.")
            
            
    def confirm_file_info(self):
        """When file confirm button is pressed: double check validity, then process files"""        
        
        # Check all file fields filled out 
        all_valid = all(
            section["paradigm_combo"].currentIndex() != 0 and
            section["raw_label"].text() != "No file selected" and
            section["mff_label"].text() != "No folder selected"
            for section in self.file_upload_tab.sections
        ) and self.file_upload_tab.notes_label != "No file selected"
        
        if all_valid:
            
            # Update data model with file info
            self.file_upload_tab.update_file_info()

            # update deid log/get deid    
            self.data_model.save_session_to_deid_log()
            QMessageBox.information(self, 'title', f'your deid is: {self.data_model.deid}\nsaved to csv\ndo not touch anything')
            
            # copy corrected files
            self.data_model.copy_and_rename_files()   
            QMessageBox.information(self, 'title', 'copied corrected files\ndo not touch anything')
         
            # copy deid files
            self.data_model.save_deid_files()
            QMessageBox.information(self, 'title', 'copied deid files\ndo not touch anything')

            # create sidecar files
            #self.data_model.save_sidecar_files()

            # reset data
            self.reset_form()
            if datetime.now().microsecond % 100 < 10:
                ascii_art = r"""form is reset here is a lucky 10% cat
                 /\_/\  
                ( o.o ) 
                > ^ <
                """
                QMessageBox.information(self, 'title', ascii_art)
            else:
                QMessageBox.information(self, 'title', 'form is reset')
        
        else:
            QMessageBox.warning(self, "Validation Error", "Check that the fields are valid. If you see this something is really really wrong.")






class DataModel:
    
    PARADIGM_TO_DEID_COLUMN_NAME = {
        "rest": "Resting", 
        "resteyesclosed" : "Resting",
        "chirp": "Chirp", 
        "chirplong": "Chirp", 
        "ssct": "Steady State", 
        "rleeg": "Reversal Learning", 
        "talk": "TalkListen", 
        "listen": "TalkListen", 
        "vdaudio": "Visual Discrimination", 
        "vdnoaudio": "Visual Discrimination", 
        "slstructured": "SL Passive", 
        "slrandom": "SL Passive", 
        "slactive": "SL Active", 
        "habituation": "Habituation",
        "bblong": "BB Long", 
        "tactilechirp": "Tactile Chirp", 
        "tactilehab": "Tactile Habituation", 
        "oddball": "Oddball", 
        "other": "Other"
    }

    DEID_LOG_FILEPATH = 'C:/Users/liu7tv/OneDrive - cchmc/deid_logs_testing/DeidentifyPatientNum_NEW.xlsx'  
    
    def __init__(self):

        # Configuration dictionary containing presets
        config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'filename_config.json') 
        with open(config_file_path, 'r') as f:
            self.CONFIG_DICT = json.load(f)

        # Output folder to save renamed files
        self.file_output_folder = 'D:/zz_WORKING_DIRECTORY/'
        #self.file_output_folder = 'C:/Users/liu7tv/Desktop/upload_test_files/output'

        # Notes file path         
        self.notes_file = None
        
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
        self.eeg_file_info = []
        
        # Init deid log
        self.deid_log = pd.DataFrame()
        self.load_deid_log(self.DEID_LOG_FILEPATH)
        
        # DeID for current session
        self.deid = None
        
    
    def clear_data(self):
        """Reset data model"""
        self.__init__()    
    
    
    def get_list_of_current_paradigms(self):
        """Get list of paradigms for current study preset"""
        current_study = self.session_info['study']
        return self.CONFIG_DICT[current_study]['paradigm']['options']
        
    
    def load_deid_log(self, file_path):
        """Read deid log into pandas dataframe, ignoring rows without available deids"""
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Deid log {file_path} does not exist!")        

        # load deid log into data model 
        self.deid_log = pd.read_excel(file_path, engine='openpyxl')
        
        # Filter out rows where first column is NaN (no deid available)
        first_column = self.deid_log.columns[0]
        self.deid_log = self.deid_log[self.deid_log[first_column].notna()]
        self.deid_log.reset_index(drop=True, inplace=True)

  


    def save_session_to_deid_log(self):
        """Get deid and update deid log with current session information"""
        
        # back up deid log before editing
        self.back_up_deid_log()
       
        # get deid log and determine first empty row
        df = self.deid_log.copy()
        empty_row_index = self.get_empty_row_index_from_deid_log()
        
        # check if there's rows available    
        if empty_row_index >= len(df):
            raise Exception("No empty rows available in the CSV")
        
        # set deid from log
        self.deid = self.get_deid(empty_row_index)
        
        print(self.session_info['date'])
        
        # Update DataFrame with session info
        cur_session_data = {
            'Study': self.session_info['study'],
            'Subject ID': self.session_info['subject_id'],
            'Visit Num': self.session_info['visit_number'],
            'Visit Date': self.session_info['date'],
            'Initials': self.session_info['subject_initials'],
            'Location': self.session_info['location'],
            'Net Serial Number': self.session_info['net_serial_number'],
            'Notes': self.session_info['other_notes']
        }
        for key, value in cur_session_data.items():
            df.at[empty_row_index, key] = value   
        
        # Add paradigms
        for eeg_file_dict in self.eeg_file_info:
            cur_paradigm = eeg_file_dict['paradigm']
            column_name = self.PARADIGM_TO_DEID_COLUMN_NAME.get(cur_paradigm, None)
            if column_name:
                if pd.isna(df.at[empty_row_index, column_name]):
                    df.at[empty_row_index, column_name] = 1
                else:
                    df.at[empty_row_index, column_name] += 1  
                        
        # Update work book (only at specified row)
        wb = load_workbook(self.DEID_LOG_FILEPATH)
        sheet = wb.active
        for col_idx, col_name in enumerate(df.columns, start=1):
            sheet.cell(row=empty_row_index + 2, column=col_idx, value=df.at[empty_row_index, col_name])
            
        # Save the workbook with the updated row
        wb.save(self.DEID_LOG_FILEPATH)


    def back_up_deid_log(self):
        """back up current version of deid log (will overwrite files in current day)"""
        backup_folder = os.path.join(os.path.dirname(self.DEID_LOG_FILEPATH), 'backup')
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder)        
        name, extension = os.path.splitext(os.path.basename(self.DEID_LOG_FILEPATH))
        date_str = datetime.now().strftime("%m-%d-%Y")
        new_file_name = f"{name}_{date_str}{extension}"
        backup_filepath = os.path.join(backup_folder, new_file_name)
        shutil.copy2(self.DEID_LOG_FILEPATH, backup_filepath)

        
    def get_empty_row_index_from_deid_log(self):
        """Find the index of the first completely empty row (ignoring the first column)"""
        empty_rows = self.deid_log.loc[:, self.deid_log.columns[1:]].isna().all(axis=1)
        if not empty_rows.any():
            raise ValueError("No available rows in deid log, run out of deids.")
        return empty_rows.idxmax()


    def get_deid(self, row):
        """Get deid from deid log, given a row index"""
        return self.deid_log.at[row, self.deid_log.columns[0]]





                     
    def copy_and_rename_files(self):
        paradigm_counter = {}
        
        destination_folder = self.file_output_folder 
        
        dat = self.session_info

        # Loop through all files
        for cur_file_info in self.eeg_file_info:
            src_path_raw = cur_file_info['raw_file']
            src_path_mff = cur_file_info['mff_folder']
            
            # get extensions
            raw_file_ext = os.path.splitext(src_path_raw)[1]
            mff_file_ext = os.path.splitext(src_path_mff)[1]

            if src_path_raw and src_path_mff:
                paradigm = cur_file_info['paradigm']
                
                # Initialize or update the counter for this file type
                if paradigm not in paradigm_counter:
                    paradigm_counter[paradigm] = 1
                else:
                    paradigm_counter[paradigm] += 1
                
                # Create base file name with optional counter
                counter = paradigm_counter[paradigm] if paradigm_counter[paradigm] > 1 else ""
                base_name = f"{dat['study']}_{dat['visit_number']}_{paradigm}{counter}_{dat['subject_id']}_{dat['subject_initials']}_{dat['date']}"

                # Add additional modifiers if needed
                if self.session_info['cap_type'] == 'babycap':
                    base_name += "_babycap"
                if self.session_info['audio_source'] == 'speakers' and paradigm != 'rest':
                    base_name += "_speakers"
                    
                # Sub directory path for saving files in correct folder 
                final_directory_path = os.path.join(destination_folder, "back_up", dat['study'], dat['subject_id'] + " " + dat['subject_initials'], dat['visit_number'])
                os.makedirs(final_directory_path, exist_ok=True)  # Create directories if they do not exist
                
                # Create final file path
                dst_path_raw = os.path.join(final_directory_path, base_name + raw_file_ext)
                dst_path_mff = os.path.join(final_directory_path, base_name + mff_file_ext)
                
                # Check if file already exists
                if os.path.exists(dst_path_raw):
                    raise FileExistsError(f"File '{dst_path_raw}' already exists (this should never happen you can panic)")
                
                # Check if file already exists
                if os.path.exists(dst_path_mff):
                    raise FileExistsError(f"File '{dst_path_mff}' already exists (this should never happen you can panic)")
                
                
                # Make copy at destination folder
                shutil.copy2(src_path_raw, dst_path_raw)
                shutil.copytree(src_path_mff, dst_path_mff)


        # save notes file
        new_notes_file_name = f"{dat['study']}_{dat['visit_number']}_{dat['subject_id']}_{dat['subject_initials']}_{dat['date']}" + os.path.splitext(self.notes_file)[1]
        shutil.copy2(self.notes_file, os.path.join(final_directory_path, new_notes_file_name))   
        
    def save_deid_files(self):
        
        destination_folder = self.file_output_folder 

        paradigm_counter = {}

        # Loop through all files
        for cur_file_info in self.eeg_file_info:
            src_path = cur_file_info['raw_file']
            
            raw_file_ext = os.path.splitext(src_path)[1]
            if src_path:
                paradigm = cur_file_info['paradigm']
                
                # Initialize or update the counter for this file type
                if paradigm not in paradigm_counter:
                    paradigm_counter[paradigm] = 1
                else:
                    paradigm_counter[paradigm] += 1
                
                # Create base file name with optional counter
                counter = paradigm_counter[paradigm] if paradigm_counter[paradigm] > 1 else ""
                base_name = f"{self.deid}_{paradigm}{counter}"

                # Add additional notes if needed
                if self.session_info['cap_type'] == 'babycap':
                    base_name += "_babycap"
                if self.session_info['audio_source'] == 'speakers' and paradigm != 'rest':
                    base_name += "_speakers"

                
                
                
                # Sub directory path for saving files in correct folder 
                final_directory_path = os.path.join(destination_folder, "deidentified")
                os.makedirs(final_directory_path, exist_ok=True)  # Create directories if they do not exist
                
                # Create final file path
                dst_path_deid = os.path.join(final_directory_path, base_name + raw_file_ext)
                

                # Make copy at destination folder
                shutil.copy2(src_path, dst_path_deid)   
                
        
        # save notes file
        new_notes_file_name = f"{self.deid}_notes" + os.path.splitext(self.notes_file)[1]
        shutil.copy2(self.notes_file, os.path.join(final_directory_path, new_notes_file_name))   
        
        
        
    def save_sidecar_files(self):
        """Save session and file info in json sidecar file"""
                
        paradigm_counter = {}
        destination_folder = self.file_output_folder 
        dat = self.session_info 
        
        # Loop through all files
        for cur_file_info in self.eeg_file_info:
            final_sidecar_dict = self.session_info | cur_file_info
            paradigm = final_sidecar_dict['paradigm']
            
            # Initialize or update the counter for this file type
            if paradigm not in paradigm_counter:
                paradigm_counter[paradigm] = 1
            else:
                paradigm_counter[paradigm] += 1
            
            # Create base file name with optional counter
            counter = paradigm_counter[paradigm] if paradigm_counter[paradigm] > 1 else ""
            base_name = f"{dat['study']}_{dat['visit_number']}_{paradigm}{counter}_{dat['subject_id']}_{dat['subject_initials']}_{dat['date']}"

            # Add additional modifiers if needed
            if self.session_info['cap_type'] == 'babycap':
                base_name += "_babycap"
            if self.session_info['audio_source'] == 'speakers' and paradigm != 'rest':
                base_name += "_speakers"
                
            # Sub directory path for saving files in correct folder 
            final_directory_path = os.path.join(destination_folder, dat['study'], dat['subject_id'] + " " + dat['subject_initials'], dat['visit_number'])
            os.makedirs(final_directory_path, exist_ok=True)

            # Save json file            
            dst_path_sidecar = os.path.join(final_directory_path, base_name + ".json")
            with open(dst_path_sidecar, "w") as outfile:
                json.dump(final_sidecar_dict, outfile, indent=4)
        
      
      
      
      
      
    def safe_file_copy(src_path, dst_folder, file_name):
        """Create destination dir if it doesn't exist --> save file, error out if file already exists"""
        
        # Create directory path if it doesn't exist
        os.makedirs(dst_folder, exist_ok=True)
        
        # Create the full destination path
        dst_path = os.path.join(dst_folder, file_name)
        
        # Check if the file already exists
        if os.path.exists(dst_path):
            raise FileExistsError(f"File '{dst_path}' already exists")
        
        # Copy the file
        shutil.copy2(src_path, dst_path)
    
    
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
