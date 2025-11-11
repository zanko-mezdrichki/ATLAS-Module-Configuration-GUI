import sys
import json
import ast
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget,
                             QVBoxLayout, QPushButton, QLineEdit, QHBoxLayout,
                             QMessageBox, QLabel, QStackedWidget, QFileDialog,
                             QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                             QGroupBox, QCheckBox, QDialog, QDialogButtonBox)
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ATLAS Module Configuration GUI")
        self.setWindowIcon(QIcon("atlas_logo.png"))
        self.setGeometry(700, 300, 1200, 700)
        
        # Directory base(needs to be changed)
        self.base_directory = "//wsl$/Ubuntu/home/zanko/pf_labs/Interfaccia"
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.page1 = QWidget()  # Loading
        self.page2 = QWidget()  # Manipolation
        self.page3 = QWidget()  # Summary
        
        self.stacked_widget.addWidget(self.page1)
        self.stacked_widget.addWidget(self.page2)
        self.stacked_widget.addWidget(self.page3)
        
        self.modules_data_cold = {}
        self.modules_data_warm = {}
        self.port_info_cold = {}
        self.port_info_warm = {}
        self.modified_data = {}
        self.serial_number = None
        self.file_saved = None
        
        self.initUI_1()
        self.initUI_2()
        self.initUI_3()

    def initUI_1(self):
        layout = QVBoxLayout()
        
        title = QLabel("📡 ATLAS Module Configuration System")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: #2E86AB; margin: 20px;")
        
        self.status_label = QLabel("📁 Enter module serial number")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            font-size: 24px;
            color: #FFD700;
            background-color: rgba(46, 134, 171, 50);
            padding: 15px;
            border-radius: 10px;
            border: 2px solid #2E86AB;
        """)
        
        input_group = QGroupBox("Module Selection")
        input_group.setStyleSheet("font-size: 20px; font-weight: bold;")
        input_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        self.edit_line_path = QLineEdit()
        self.edit_line_path.setPlaceholderText("Enter serial number (e.g., 20UPGM22110267)")
        self.edit_line_path.setMinimumHeight(60)
        self.edit_line_path.setStyleSheet("""
            font-size: 24px;
            padding: 10px;
            border: 2px solid #2E86AB;
            border-radius: 5px;
        """)
        
        self.button_browse = QPushButton("Browse")
        self.button_browse.setMinimumHeight(60)
        self.button_browse.setMinimumWidth(120)
        self.button_browse.setStyleSheet("""
            font-size: 20px;
            background-color: #6C757D;
            color: white;
            border-radius: 5px;
            font-weight: bold;
        """)
        
        path_layout.addWidget(self.edit_line_path, stretch=4)
        path_layout.addWidget(self.button_browse, stretch=1)
        input_layout.addLayout(path_layout)
        
        self.button_load = QPushButton("🔍 Load Module Data")
        self.button_load.setMinimumHeight(70)
        self.button_load.setStyleSheet("""
            font-size: 24px;
            background-color: #2E86AB;
            color: white;
            border-radius: 5px;
            font-weight: bold;
        """)
        input_layout.addWidget(self.button_load)
        
        input_group.setLayout(input_layout)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMinimumHeight(250)
        self.info_text.setStyleSheet("""
            font-size: 16px;
            background-color: #F8F9FA;
            border: 2px solid #2E86AB;
            border-radius: 5px;
            padding: 10px;
        """)
        self.info_text.setText("ℹ️ Waiting for module data...\n\nThis system will load:\n• Cold configuration files\n• Warm configuration files\n• Port and RX channel information")
        
        self.button_next_1 = QPushButton("Next → Modify Parameters")
        self.button_next_1.setMinimumHeight(70)
        self.button_next_1.setEnabled(False)
        self.button_next_1.setStyleSheet("""
            font-size: 24px;
            background-color: #28A745;
            color: white;
            border-radius: 5px;
            font-weight: bold;
        """)
        
        layout.addWidget(title)
        layout.addWidget(self.status_label)
        layout.addWidget(input_group)
        layout.addWidget(self.info_text)
        layout.addStretch()
        layout.addWidget(self.button_next_1)
        
        self.page1.setLayout(layout)
        self.page1.setStyleSheet("background-color: white; padding: 20px;")
        
        self.edit_line_path.textChanged.connect(self.check_serial_text)
        self.button_browse.clicked.connect(self.browse_folder)
        self.button_load.clicked.connect(self.load_module_data)
        self.button_next_1.clicked.connect(self.go_to_page2)

    def initUI_2(self):
        layout = QVBoxLayout()
        
        header = QHBoxLayout()
        title = QLabel("⚙️ Module Parameters Configuration")
        title.setStyleSheet("font-size: 30px; font-weight: bold; color: #2E86AB;")
        header.addWidget(title)
        header.addStretch()
        
        self.module_info_label = QLabel("")
        self.module_info_label.setStyleSheet("font-size: 18px; color: #495057;")
        header.addWidget(self.module_info_label)
        
        filter_layout = QHBoxLayout()

        legend_label = QLabel("🎨 Legend: ")
        legend_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        filter_layout.addWidget(legend_label)
        
        cold_legend = QLabel("■ COLD")
        cold_legend.setStyleSheet("font-size: 16px; color: white; background-color: #1E88E5; padding: 5px 10px; border-radius: 3px; font-weight: bold;")
        filter_layout.addWidget(cold_legend)
        
        warm_legend = QLabel("■ WARM")
        warm_legend.setStyleSheet("font-size: 16px; color: white; background-color: #FF6B35; padding: 5px 10px; border-radius: 3px; font-weight: bold;")
        filter_layout.addWidget(warm_legend)
        
        filter_layout.addSpacing(30)
        
        filter_label = QLabel("🔍 Show:")
        filter_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        filter_layout.addWidget(filter_label)
        
        self.filter_cold = QCheckBox("Cold")
        self.filter_cold.setChecked(True)
        self.filter_cold.setStyleSheet("font-size: 16px;")
        filter_layout.addWidget(self.filter_cold)
        
        self.filter_warm = QCheckBox("Warm")
        self.filter_warm.setChecked(True)
        self.filter_warm.setStyleSheet("font-size: 16px;")
        filter_layout.addWidget(self.filter_warm)
        
        self.button_refresh = QPushButton("🔄 Refresh Table")
        self.button_refresh.setMinimumHeight(40)
        self.button_refresh.setStyleSheet("""
            font-size: 16px;
            background-color: #17A2B8;
            color: white;
            border-radius: 5px;
            font-weight: bold;
            padding: 5px 15px;
        """)
        filter_layout.addWidget(self.button_refresh)
        
        filter_layout.addStretch()
        
        self.param_table = QTableWidget()
        self.param_table.setColumnCount(5)
        self.param_table.setHorizontalHeaderLabels([
            "Type", "ChipID", "Config Name", "Parameter", "Value"
        ])
        
        header_table = self.param_table.horizontalHeader()
        header_table.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Type
        header_table.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # ChipID
        header_table.setSectionResizeMode(2, QHeaderView.Stretch)  # Config Name
        header_table.setSectionResizeMode(3, QHeaderView.Stretch)  # Parameter
        header_table.setSectionResizeMode(4, QHeaderView.Stretch)  # Value
        
        self.param_table.setAlternatingRowColors(True)
        self.param_table.setStyleSheet("""
            QTableWidget {
                font-size: 15px;
                gridline-color: #CED4DA;
                border: 2px solid #2E86AB;
                selection-background-color: #FFC107;
                selection-color: black;
            }
            QHeaderView::section {
                background-color: #2E86AB;
                color: white;
                font-weight: bold;
                font-size: 16px;
                padding: 10px;
                border: 1px solid #1A5F7A;
            }
            QTableWidget::item {
                padding: 8px;
            }
        """)
        
        self.param_table.setSortingEnabled(True)
        
        button_layout = QHBoxLayout()
        
        self.button_edit = QPushButton("✏️ Edit Selected")
        self.button_edit.setMinimumHeight(60)
        self.button_edit.setStyleSheet("""
            font-size: 20px;
            background-color: #007BFF;
            color: white;
            border-radius: 5px;
            font-weight: bold;
        """)
        
        self.button_save = QPushButton("💾 Save All Changes")
        self.button_save.setMinimumHeight(60)
        self.button_save.setStyleSheet("""
            font-size: 20px;
            background-color: #FFC107;
            color: white;
            border-radius: 5px;
            font-weight: bold;
        """)
        
        button_layout.addWidget(self.button_edit)
        button_layout.addWidget(self.button_save)
        
        nav_layout = QHBoxLayout()
        self.button_back_2 = QPushButton("← Back")
        self.button_back_2.setMinimumHeight(60)
        self.button_back_2.setStyleSheet("""
            font-size: 20px;
            background-color: #6C757D;
            color: white;
            border-radius: 5px;
            font-weight: bold;
        """)
        
        self.button_next_2 = QPushButton("Next → Summary")
        self.button_next_2.setMinimumHeight(60)
        self.button_next_2.setStyleSheet("""
            font-size: 20px;
            background-color: #28A745;
            color: white;
            border-radius: 5px;
            font-weight: bold;
        """)
        
        nav_layout.addWidget(self.button_back_2)
        nav_layout.addStretch()
        nav_layout.addWidget(self.button_next_2)
        
        layout.addLayout(header)
        layout.addLayout(filter_layout)
        layout.addWidget(self.param_table)
        layout.addLayout(button_layout)
        layout.addLayout(nav_layout)
        
        self.page2.setLayout(layout)
        self.page2.setStyleSheet("background-color: white; padding: 20px;")
        
        self.button_edit.clicked.connect(self.edit_parameter)
        self.button_save.clicked.connect(self.save_all_changes)
        self.button_back_2.clicked.connect(self.go_to_page1)
        self.button_next_2.clicked.connect(self.go_to_page3)
        self.button_refresh.clicked.connect(self.populate_parameter_table)
        self.filter_cold.stateChanged.connect(self.populate_parameter_table)
        self.filter_warm.stateChanged.connect(self.populate_parameter_table)

    def initUI_3(self):
        layout = QVBoxLayout()
        
        title = QLabel("📋 Configuration Summary")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: #28A745; margin: 20px;")
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet("""
            font-size: 18px;
            background-color: #F8F9FA;
            border: 2px solid #28A745;
            border-radius: 10px;
            padding: 15px;
        """)
        
        nav_layout = QHBoxLayout()
        self.button_back_3 = QPushButton("← Back to Edit")
        self.button_back_3.setMinimumHeight(70)
        self.button_back_3.setStyleSheet("""
            font-size: 22px;
            background-color: #6C757D;
            color: white;
            border-radius: 5px;
            font-weight: bold;
        """)
        
        self.button_finish = QPushButton("✓ Finish")
        self.button_finish.setMinimumHeight(70)
        self.button_finish.setStyleSheet("""
            font-size: 22px;
            background-color: #28A745;
            color: white;
            border-radius: 5px;
            font-weight: bold;
        """)
        
        nav_layout.addWidget(self.button_back_3)
        nav_layout.addStretch()
        nav_layout.addWidget(self.button_finish)
        
        layout.addWidget(title)
        layout.addWidget(self.summary_text)
        layout.addLayout(nav_layout)
        
        self.page3.setLayout(layout)
        self.page3.setStyleSheet("background-color: white; padding: 20px;")
        
        self.button_back_3.clicked.connect(self.go_to_page2)
        self.button_finish.clicked.connect(self.finish_and_reset)

    def check_serial_text(self, text):
        if os.path.isdir(text):
            self.edit_line_path.setStyleSheet("""
                font-size: 24px;
                padding: 10px;
                border: 3px solid #28A745;
                border-radius: 5px;
                background-color: #D4EDDA;
            """)
        elif self.find_folder_by_serial(text):
            self.edit_line_path.setStyleSheet("""
                font-size: 24px;
                padding: 10px;
                border: 3px solid #28A745;
                border-radius: 5px;
                background-color: #D4EDDA;
            """)
        else:
            self.edit_line_path.setStyleSheet("""
                font-size: 24px;
                padding: 10px;
                border: 2px solid #2E86AB;
                border-radius: 5px;
            """)
    
    def find_folder_by_serial(self, serial):
        if not os.path.isdir(self.base_directory):
            return None
        
        for item in os.listdir(self.base_directory):
            item_path = os.path.join(self.base_directory, item)
            if os.path.isdir(item_path) and serial in item:
                return item_path
        return None
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Module Folder", self.base_directory)
        if folder:
            self.edit_line_path.setText(folder)
    
    def load_module_data(self):
        input_text = self.edit_line_path.text().strip()
        
        if os.path.isdir(input_text):
            base_path = input_text
        else:
            base_path = self.find_folder_by_serial(input_text)
            if not base_path:
                QMessageBox.warning(self, "Error",
                    f"Module folder not found for serial: {input_text}\n\n"
                    f"Base directory: {self.base_directory}")
                return
        
        self.serial_number = os.path.basename(base_path)
        
        self.modules_data_cold.clear()
        self.modules_data_warm.clear()
        self.port_info_cold.clear()
        self.port_info_warm.clear()
        self.modified_data.clear()
        
        cold_loaded = self.load_configuration(base_path, "cold")
        warm_loaded = self.load_configuration(base_path, "warm")
        
        if cold_loaded and warm_loaded:
            info = f"✅ Successfully loaded module: {self.serial_number}\n\n"
            info += f"📊 Statistics:\n"
            info += f"  • Unique cold configurations: {len(self.modules_data_cold)}\n"
            info += f"  • Unique warm configurations: {len(self.modules_data_warm)}\n\n"
            info += f"🔌 Front End Configurations:\n\n"
            
            all_chipIDs = set(list(self.modules_data_cold.keys()) + list(self.modules_data_warm.keys()))
            
            for chipID in sorted(all_chipIDs):
                if chipID in self.modules_data_cold:
                    config_name = self.modules_data_cold[chipID].get('config_name', 'N/A')
                    info += f"  • ChipID {chipID} (Config: {config_name})\n"
                    info += f"    - Cold configuration loaded ❄️\n"
                    if chipID in self.modules_data_warm:
                        info += f"    - Warm configuration loaded 🔥\n"
                elif chipID in self.modules_data_warm:
                    config_name = self.modules_data_warm[chipID].get('config_name', 'N/A')
                    info += f"  • ChipID {chipID} (Config: {config_name})\n"
                    info += f"    - Warm configuration loaded 🔥\n"
            
            info += f"\n💡 Note: Port connectivity details available in Summary page"
            
            self.info_text.setText(info)
            self.status_label.setText(f"✅ Module {self.serial_number} loaded successfully")
            self.button_next_1.setEnabled(True)
            
            QMessageBox.information(self, "Success",
                f"Module loaded successfully!\n\n"
                f"Cold modules: {len(self.modules_data_cold)}\n"
                f"Warm modules: {len(self.modules_data_warm)}")
        else:
            QMessageBox.warning(self, "Error", "Failed to load module configurations")

    def load_configuration(self, base_path, config_type):
        config_folder = f"L2_{config_type}"
        config_path = os.path.join(base_path, config_folder)
        
        if not os.path.exists(config_path):
            return False
        
        port_files = [f for f in os.listdir(base_path)
                     if f.endswith('.json') and config_type in f.lower() and 'YarrPort' in f]
        
        port_dict = self.port_info_cold if config_type == "cold" else self.port_info_warm
        modules_dict = self.modules_data_cold if config_type == "cold" else self.modules_data_warm
        
        for port_file in port_files:
            port_file_path = os.path.join(base_path, port_file)
            
            try:
                with open(port_file_path, 'r') as f:
                    port_data = json.load(f)
                
                port_name = port_file.replace('.json', '')
                port_dict[port_name] = []
                
                for chip in port_data.get('chips', []):
                    config_file = chip.get('config', '')
                    if not config_file:
                        continue
                    
                    chip_config_path = os.path.join(base_path, config_file)
                    if not os.path.exists(chip_config_path):
                        continue
                    
                    with open(chip_config_path, 'r') as cf:
                        chip_data = json.load(cf)
                    
                    chipID = None
                    config_name = None
                    for chip_type in ["ITKPIXV2", "RD53B"]:
                        if chip_type in chip_data:
                            chipID = chip_data[chip_type].get("Parameter", {}).get("ChipId")
                            config_name = chip_data[chip_type].get("Parameter", {}).get("Name")
                            break
                    
                    if chipID is None:
                        continue
                    
                    chipID = str(chipID)
                    
                    port_dict[port_name].append({
                        'chipID': chipID,
                        'config_name': config_name,
                        'rx': chip.get('rx'),
                        'tx': chip.get('tx'),
                        'enable': chip.get('enable', 1)
                    })
                    
                    if chipID not in modules_dict:
                        important_keys = [
                            "EnCoreCol0", "EnCoreCol1", "EnCoreCol2", "EnCoreCol3",
                            "SldoTrimA", "SldoTrimD", "ADCcalPar",
                            "KSenseInA", "KSenseInD", "KSenseShuntA", "KSenseShuntD"
                        ]
                        
                        important_data = {}
                        for chip_type in ["ITKPIXV2", "RD53B"]:
                            if chip_type in chip_data:
                                global_config = chip_data[chip_type].get("GlobalConfig", {})
                                parameter = chip_data[chip_type].get("Parameter", {})
                                
                                for k in important_keys:
                                    if k in global_config:
                                        important_data[k] = global_config[k]
                                    elif k in parameter:
                                        important_data[k] = parameter[k]
                                break
                        
                        modules_dict[chipID] = {
                            'full_data': chip_data,
                            'important_data': important_data,
                            'file_path': chip_config_path,
                            'config_name': config_name or os.path.basename(chip_config_path).replace(f'_L2_{config_type}.json', '')
                        }
                
            except Exception as e:
                print(f"Error loading {port_file}: {str(e)}")
                continue
        
        return len(modules_dict) > 0

    def go_to_page2(self):
        self.populate_parameter_table()
        self.module_info_label.setText(f"Module: {self.serial_number}")
        self.stacked_widget.setCurrentWidget(self.page2)
    
    def populate_parameter_table(self):
        self.param_table.setRowCount(0)
        self.param_table.setSortingEnabled(False)
        
        show_cold = self.filter_cold.isChecked()
        show_warm = self.filter_warm.isChecked()
        
        all_params = set()
        for module in self.modules_data_cold.values():
            all_params.update(module['important_data'].keys())
        for module in self.modules_data_warm.values():
            all_params.update(module['important_data'].keys())
        
        all_chipIDs = set(list(self.modules_data_cold.keys()) + list(self.modules_data_warm.keys()))
        
        row = 0
        
        if show_cold:
            for chipID in sorted(all_chipIDs):
                if chipID in self.modules_data_cold:
                    module = self.modules_data_cold[chipID]
                    config_name = module.get('config_name', 'N/A')
                    
                    for param in sorted(module['important_data'].keys()):
                        value = str(module['important_data'][param])
                        
                        self.param_table.insertRow(row)
                        
                        type_item = QTableWidgetItem("❄️ COLD")
                        type_item.setBackground(QColor(30, 136, 229))  # Blu
                        type_item.setForeground(QColor(255, 255, 255))
                        type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                        self.param_table.setItem(row, 0, type_item)
                        
                        chip_item = QTableWidgetItem(chipID)
                        chip_item.setBackground(QColor(255, 220, 200))
                        chip_item.setFlags(chip_item.flags() & ~Qt.ItemIsEditable)
                        self.param_table.setItem(row, 1, chip_item)
                        
                        name_item = QTableWidgetItem(config_name)
                        name_item.setBackground(QColor(255, 220, 200))
                        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                        self.param_table.setItem(row, 2, name_item)
                        
                        param_item = QTableWidgetItem(param)
                        param_item.setBackground(QColor(255, 220, 200))  # Arancione chiaro
                        param_item.setFlags(param_item.flags() & ~Qt.ItemIsEditable)
                        self.param_table.setItem(row, 3, param_item)
                        
                        value_item = QTableWidgetItem(value)
                        value_item.setBackground(QColor(255, 240, 230))
                        value_item.setForeground(QColor(139, 0, 0))
                        self.param_table.setItem(row, 4, value_item)
                        
                        row += 1
        
        if show_warm:
            for chipID in sorted(all_chipIDs):
                if chipID in self.modules_data_warm:
                    module = self.modules_data_warm[chipID]
                    config_name = module.get('config_name', 'N/A')
                    
                    for param in sorted(module['important_data'].keys()):
                        value = str(module['important_data'][param])
                        
                        self.param_table.insertRow(row)
                        
                        type_item = QTableWidgetItem("🔥 WARM")
                        type_item.setBackground(QColor(255, 107, 53))
                        type_item.setForeground(QColor(255, 255, 255))
                        type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                        self.param_table.setItem(row, 0, type_item)
                        
                        chip_item = QTableWidgetItem(chipID)
                        chip_item.setBackground(QColor(255, 235, 205))
                        chip_item.setFlags(chip_item.flags() & ~Qt.ItemIsEditable)
                        self.param_table.setItem(row, 1, chip_item)
                        
                        name_item = QTableWidgetItem(config_name)
                        name_item.setBackground(QColor(255, 235, 205))
                        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                        self.param_table.setItem(row, 2, name_item)
                        
                        param_item = QTableWidgetItem(param)
                        param_item.setBackground(QColor(255, 235, 205))  # Pesca chiaro
                        param_item.setFlags(param_item.flags() & ~Qt.ItemIsEditable)
                        self.param_table.setItem(row, 3, param_item)
                        
                        value_item = QTableWidgetItem(value)
                        value_item.setBackground(QColor(255, 245, 235))
                        value_item.setForeground(QColor(139, 0, 0))
                        self.param_table.setItem(row, 4, value_item)
                        
                        row += 1
        
        self.param_table.setSortingEnabled(True)
        total_rows = self.param_table.rowCount()
        self.module_info_label.setText(f"Module: {self.serial_number} | Total entries: {total_rows}")

    def edit_parameter(self):
        current_row = self.param_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a parameter to edit")
            return
        
        type_text = self.param_table.item(current_row, 0).text()
        chipID = self.param_table.item(current_row, 1).text()
        config_name = self.param_table.item(current_row, 2).text()
        param = self.param_table.item(current_row, 3).text()
        current_value = self.param_table.item(current_row, 4).text()
        
        is_cold = "COLD" in type_text
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit {param} for Chip {chipID}")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(300)
        
        layout = QVBoxLayout()
        
        info_widget = QLabel(f"{'❄️ COLD' if is_cold else '🔥 WARM'} Configuration")
        info_widget.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: white;
            background-color: {'#1E88E5' if is_cold else '#FF6B35'};
            padding: 15px;
            border-radius: 5px;
        """)
        info_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_widget)
        
        details_layout = QVBoxLayout()
        details_layout.setSpacing(10)
        
        detail_style = "font-size: 16px; padding: 5px; background-color: #F8F9FA; border-radius: 3px;"
        
        param_label = QLabel(f"<b>Parameter:</b> {param}")
        param_label.setStyleSheet(detail_style)
        details_layout.addWidget(param_label)
        
        chip_label = QLabel(f"<b>ChipID:</b> {chipID}")
        chip_label.setStyleSheet(detail_style)
        details_layout.addWidget(chip_label)
        
        name_label = QLabel(f"<b>Config Name:</b> {config_name}")
        name_label.setStyleSheet(detail_style)
        details_layout.addWidget(name_label)
        
        layout.addLayout(details_layout)
        
        layout.addWidget(QLabel(f"<b style='font-size: 18px;'>Current Value:</b> <span style='color: {'#1E88E5' if is_cold else '#FF6B35'};'>{current_value}</span>"))
        
        value_input = QLineEdit(current_value)
        value_input.setStyleSheet("""
            font-size: 18px;
            padding: 10px;
            border: 2px solid #2E86AB;
            border-radius: 5px;
        """)
        value_input.setPlaceholderText("Enter new value")
        layout.addWidget(QLabel("<b>New Value:</b>"))
        layout.addWidget(value_input)
        
        type_hint = self.get_parameter_type_hint(param)
        hint_label = QLabel(f"ℹ️ Expected type: <i>{type_hint}</i>")
        hint_label.setStyleSheet("font-size: 14px; color: #6C757D;")
        layout.addWidget(hint_label)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet("font-size: 16px;")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            new_value = value_input.text().strip()
            
            if not new_value:
                QMessageBox.warning(self, "Error", "Please enter a value")
                return
            
            try:
                converted_value = self.convert_value(param, new_value)
                
                self.param_table.item(current_row, 4).setText(str(converted_value))
                
                if is_cold and chipID in self.modules_data_cold:
                    self.modules_data_cold[chipID]['important_data'][param] = converted_value
                    data_type = "cold"
                elif not is_cold and chipID in self.modules_data_warm:
                    self.modules_data_warm[chipID]['important_data'][param] = converted_value
                    data_type = "warm"
                else:
                    QMessageBox.warning(self, "Error", "Module data not found")
                    return
                
                key = f"{chipID}_{param}_{data_type}"
                self.modified_data[key] = {
                    'chipID': chipID,
                    'param': param,
                    'value': converted_value,
                    'type': data_type,
                    'config_name': config_name
                }
                
                QMessageBox.information(self, "Success",
                    f"Parameter updated!\n\n"
                    f"Type: {data_type.upper()}\n"
                    f"Config Name: {config_name}\n"
                    f"ChipID: {chipID}\n"
                    f"Parameter: {param}\n"
                    f"Old value: {current_value}\n"
                    f"New value: {converted_value}")
                
            except ValueError as e:
                QMessageBox.warning(self, "Error", f"Invalid value format!\n\n{str(e)}\n\nExpected: {type_hint}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error: {str(e)}")

    def get_parameter_type_hint(self, param):
        if param in ["EnCoreCol0", "EnCoreCol1", "EnCoreCol2", "EnCoreCol3",
                     "SldoTrimA", "SldoTrimD"]:
            return "integer"
        elif param == "ADCcalPar":
            return "list (e.g., [1.0, 2.0, 3.0])"
        elif param in ["KSenseInA", "KSenseInD", "KSenseShuntA", "KSenseShuntD"]:
            return "float"
        else:
            return "string"

    def convert_value(self, param, value_str):
        if param in ["EnCoreCol0", "EnCoreCol1", "EnCoreCol2", "EnCoreCol3",
                     "SldoTrimA", "SldoTrimD"]:
            return int(value_str)
        elif param == "ADCcalPar":
            return ast.literal_eval(value_str)
        elif param in ["KSenseInA", "KSenseInD", "KSenseShuntA", "KSenseShuntD"]:
            return float(value_str)
        return value_str

    def save_all_changes(self):
        if not self.modified_data:
            QMessageBox.information(self, "Info", "No changes to save")
            return
        
        summary = "The following changes will be saved:\n\n"
        cold_count = 0
        warm_count = 0
        
        for key, mod in self.modified_data.items():
            if mod['type'] == 'cold':
                cold_count += 1
                summary += f"❄️ COLD - ChipID {mod['chipID']}: {mod['param']} = {mod['value']}\n"
            else:
                warm_count += 1
                summary += f"🔥 WARM - ChipID {mod['chipID']}: {mod['param']} = {mod['value']}\n"
        
        summary += f"\nTotal: {cold_count} cold + {warm_count} warm = {len(self.modified_data)} modifications"
        
        reply = QMessageBox.question(self, "Confirm Save",
            summary,
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                self.save_to_files()
                QMessageBox.information(self, "Success",
                    f"All changes saved successfully!\n\n"
                    f"Files saved to:\n{self.file_saved}\n\n"
                    f"Cold modifications: {cold_count}\n"
                    f"Warm modifications: {warm_count}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save files:\n{str(e)}")

    def save_to_files(self):
        base_path = self.find_folder_by_serial(self.serial_number)
        if not base_path:
            return
        
        new_path = base_path + "_modified"
        os.makedirs(new_path, exist_ok=True)
        
        cold_path = os.path.join(new_path, "L2_cold")
        warm_path = os.path.join(new_path, "L2_warm")
        os.makedirs(cold_path, exist_ok=True)
        os.makedirs(warm_path, exist_ok=True)
        
        for chipID, module in self.modules_data_cold.items():
            filename = os.path.basename(module['file_path'])
            save_path = os.path.join(cold_path, filename)
            
            chip_type = "ITKPIXV2" if "ITKPIXV2" in module['full_data'] else "RD53B"
            for param, value in module['important_data'].items():
                if param in module['full_data'][chip_type]['GlobalConfig']:
                    module['full_data'][chip_type]['GlobalConfig'][param] = value
                elif param in module['full_data'][chip_type]['Parameter']:
                    module['full_data'][chip_type]['Parameter'][param] = value
            
            with open(save_path, 'w') as f:
                json.dump(module['full_data'], f, indent=4)
        
        for chipID, module in self.modules_data_warm.items():
            filename = os.path.basename(module['file_path'])
            save_path = os.path.join(warm_path, filename)
            
            chip_type = "ITKPIXV2" if "ITKPIXV2" in module['full_data'] else "RD53B"
            for param, value in module['important_data'].items():
                if param in module['full_data'][chip_type]['GlobalConfig']:
                    module['full_data'][chip_type]['GlobalConfig'][param] = value
                elif param in module['full_data'][chip_type]['Parameter']:
                    module['full_data'][chip_type]['Parameter'][param] = value
            
            with open(save_path, 'w') as f:
                json.dump(module['full_data'], f, indent=4)
        
        original_files = os.listdir(base_path)
        for f in original_files:
            if f.endswith('.json') and 'YarrPort' in f:
                src = os.path.join(base_path, f)
                dst = os.path.join(new_path, f)
                with open(src, 'r') as sf:
                    data = json.load(sf)
                with open(dst, 'w') as df:
                    json.dump(data, df, indent=4)
        
        self.file_saved = new_path

    def go_to_page1(self):
        self.stacked_widget.setCurrentWidget(self.page1)
    
    def go_to_page3(self):
        self.generate_summary()
        self.stacked_widget.setCurrentWidget(self.page3)
    
    def generate_summary(self):
        summary = f"📋 Configuration Summary for Module: {self.serial_number}\n"
        summary += "=" * 80 + "\n\n"
        
        summary += "📊 General Statistics:\n"
        summary += f"  • Total cold modules: {len(self.modules_data_cold)}\n"
        summary += f"  • Total warm modules: {len(self.modules_data_warm)}\n"
        summary += f"  • Total modifications: {len(self.modified_data)}\n\n"
        
        summary += "🔌 Connectivity Information (Port Assignments):\n\n"
        
        summary += "  COLD Configuration:\n"
        for port_name, chips in self.port_info_cold.items():
            summary += f"    {port_name}:\n"
            for chip_info in chips:
                status = "✓ Enabled" if chip_info['enable'] else "✗ Disabled"
                config_name = chip_info.get('config_name', 'N/A')
                summary += f"      • Config: {config_name} (ChipID {chip_info['chipID']}): RX={chip_info['rx']}, TX={chip_info['tx']} [{status}]\n"
        
        summary += "\n  WARM Configuration:\n"
        for port_name, chips in self.port_info_warm.items():
            summary += f"    {port_name}:\n"
            for chip_info in chips:
                status = "✓ Enabled" if chip_info['enable'] else "✗ Disabled"
                config_name = chip_info.get('config_name', 'N/A')
                summary += f"      • Config: {config_name} (ChipID {chip_info['chipID']}): RX={chip_info['rx']}, TX={chip_info['tx']} [{status}]\n"
        
        if self.modified_data:
            summary += "\n" + "=" * 80 + "\n"
            summary += "✏️ Modified Parameters:\n\n"
            
            for key, mod in self.modified_data.items():
                config_name = mod.get('config_name', 'N/A')
                summary += f"  • {mod['type'].upper()} - Config: {config_name} (ChipID {mod['chipID']}): {mod['param']} = {mod['value']}\n"
        else:
            summary += "\n" + "=" * 80 + "\n"
            summary += "ℹ️ No parameters were modified\n\n"
        
        summary += "=" * 80 + "\n"
        summary += "📝 All Parameters by Chip:\n\n"
        
        all_chipIDs = set(list(self.modules_data_cold.keys()) + list(self.modules_data_warm.keys()))
        
        for chipID in sorted(all_chipIDs):
            summary += f"  ChipID {chipID}:\n"
            
            if chipID in self.modules_data_cold:
                config_name = self.modules_data_cold[chipID].get('config_name', 'N/A')
                summary += f"    Config Name: {config_name}\n"
                summary += f"    Cold Parameters:\n"
                for param, value in sorted(self.modules_data_cold[chipID]['important_data'].items()):
                    summary += f"      • {param}: {value}\n"
            
            if chipID in self.modules_data_warm:
                config_name = self.modules_data_warm[chipID].get('config_name', 'N/A')
                if chipID not in self.modules_data_cold:
                    summary += f"    Config Name: {config_name}\n"
                summary += f"    Warm Parameters:\n"
                for param, value in sorted(self.modules_data_warm[chipID]['important_data'].items()):
                    summary += f"      • {param}: {value}\n"
            
            summary += "\n"
        
        summary += "=" * 80 + "\n"
        if self.file_saved:
            summary += f"💾 Files saved to: {self.file_saved}\n"
        else:
            summary += f"⚠️ Changes not saved to disk yet\n"
        
        summary += "\n" + "=" * 80 + "\n"
        summary += "✅ Summary generated successfully\n"
        
        self.summary_text.setText(summary)
    
    def finish_and_reset(self):
        reply = QMessageBox.question(self, "Finish",
            "Return to start screen?\n\nAll unsaved changes will be lost.",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.modules_data_cold.clear()
            self.modules_data_warm.clear()
            self.port_info_cold.clear()
            self.port_info_warm.clear()
            self.modified_data.clear()
            self.serial_number = None
            self.file_saved = None
            
            self.edit_line_path.clear()
            self.info_text.setText("ℹ️ Waiting for module data...\n\nThis system will load:\n• Cold configuration files\n• Warm configuration files\n• Port and RX channel information")
            self.status_label.setText("📁 Enter module serial number")
            self.button_next_1.setEnabled(False)
            self.param_table.setRowCount(0)
            
            self.stacked_widget.setCurrentWidget(self.page1)
            
            QMessageBox.information(self, "Reset", "Application reset successfully")

def main():
    app = QApplication(sys.argv)
    
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
        
if __name__ == "__main__":
    main()
