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

BTN_BASE = "font-size: {}px; background-color: {}; color: white; border-radius: 5px; font-weight: bold;"
INPUT_STYLE = "font-size: 24px; padding: 10px; border: {}px solid {}; border-radius: 5px;"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ATLAS Module Configuration GUI")
        self.setWindowIcon(QIcon("atlas_logo.png"))
        self.setGeometry(700, 300, 1200, 700)
        
        self.base_directory = "//wsl$/Ubuntu/home/zanko/pf_labs/Interfaccia"
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.page1 = QWidget()
        self.page2 = QWidget()
        self.page3 = QWidget()
        
        self.stacked_widget.addWidget(self.page1)
        self.stacked_widget.addWidget(self.page2)
        self.stacked_widget.addWidget(self.page3)
        
        self.cold_modules = {}
        self.warm_modules = {}
        self.cold_ports = {}
        self.warm_ports = {}
        self.modified_data = {}
        self.serial_number = None
        self.file_saved = None
        self.base_module_path = None
        
        self.setup_page1()
        self.setup_page2()
        self.setup_page3()

    def setup_page1(self):
        layout = QVBoxLayout()
        
        title = QLabel("📡 ATLAS Module Configuration System")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: #2E86AB; margin: 20px;")
        
        self.status_label = QLabel("📁 Enter module serial number")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 24px; color: #FFD700; background-color: rgba(46, 134, 171, 50); padding: 15px; border-radius: 10px; border: 2px solid #2E86AB;")
        
        input_group = QGroupBox("Module Selection")
        input_group.setStyleSheet("font-size: 20px; font-weight: bold;")
        input_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        self.edit_line_path = QLineEdit()
        self.edit_line_path.setPlaceholderText("Enter serial number (e.g., 20UPGM22110267)")
        self.edit_line_path.setMinimumHeight(60)
        self.edit_line_path.setStyleSheet(INPUT_STYLE.format(2, "#2E86AB"))
        
        self.button_browse = QPushButton("Browse")
        self.button_browse.setMinimumHeight(60)
        self.button_browse.setMinimumWidth(120)
        self.button_browse.setStyleSheet(BTN_BASE.format(20, "#6C757D"))
        
        path_layout.addWidget(self.edit_line_path, stretch=4)
        path_layout.addWidget(self.button_browse, stretch=1)
        input_layout.addLayout(path_layout)
        
        self.button_load = QPushButton("🔍 Load Module Data")
        self.button_load.setMinimumHeight(70)
        self.button_load.setStyleSheet(BTN_BASE.format(24, "#2E86AB"))
        input_layout.addWidget(self.button_load)
        
        input_group.setLayout(input_layout)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMinimumHeight(250)
        self.info_text.setStyleSheet("font-size: 16px; background-color: #F8F9FA; border: 2px solid #2E86AB; border-radius: 5px; padding: 10px;")
        self.info_text.setText("ℹ️ Waiting for module data...\n\nThis system will load:\n• Cold configuration files\n• Warm configuration files\n• Port and RX channel information")
        
        self.button_next_1 = QPushButton("Next → Modify Parameters")
        self.button_next_1.setMinimumHeight(70)
        self.button_next_1.setEnabled(False)
        self.button_next_1.setStyleSheet(BTN_BASE.format(24, "#28A745"))
        
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
        self.button_next_1.clicked.connect(lambda: self.switch_page(self.page2))

    def setup_page2(self):
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
        self.button_refresh.setStyleSheet(BTN_BASE.format(16, "#17A2B8") + " padding: 5px 15px;")
        filter_layout.addWidget(self.button_refresh)
        filter_layout.addStretch()
        
        self.param_table = QTableWidget()
        self.param_table.setColumnCount(5)
        self.param_table.setHorizontalHeaderLabels(["Type", "ChipID", "Config Name", "Parameter", "Value"])
        
        header_table = self.param_table.horizontalHeader()
        header_table.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_table.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header_table.setSectionResizeMode(2, QHeaderView.Stretch)
        header_table.setSectionResizeMode(3, QHeaderView.Stretch)
        header_table.setSectionResizeMode(4, QHeaderView.Stretch)
        
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
            QTableWidget::item { padding: 8px; }
        """)
        self.param_table.setSortingEnabled(True)
        
        button_layout = QHBoxLayout()
        self.button_edit = QPushButton("✏️ Edit Selected")
        self.button_edit.setMinimumHeight(60)
        self.button_edit.setStyleSheet(BTN_BASE.format(20, "#007BFF"))
        
        self.button_save = QPushButton("💾 Save All Changes")
        self.button_save.setMinimumHeight(60)
        self.button_save.setStyleSheet(BTN_BASE.format(20, "#FFC107"))
        
        button_layout.addWidget(self.button_edit)
        button_layout.addWidget(self.button_save)
        
        nav_layout = QHBoxLayout()
        self.button_back_2 = QPushButton("← Back")
        self.button_back_2.setMinimumHeight(60)
        self.button_back_2.setStyleSheet(BTN_BASE.format(20, "#6C757D"))
        
        self.button_next_2 = QPushButton("Next → Summary")
        self.button_next_2.setMinimumHeight(60)
        self.button_next_2.setStyleSheet(BTN_BASE.format(20, "#28A745"))
        
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
        self.button_back_2.clicked.connect(lambda: self.switch_page(self.page1))
        self.button_next_2.clicked.connect(self.go_to_summary)
        self.button_refresh.clicked.connect(self.populate_parameter_table)
        self.filter_cold.stateChanged.connect(self.populate_parameter_table)
        self.filter_warm.stateChanged.connect(self.populate_parameter_table)

    def setup_page3(self):
        layout = QVBoxLayout()
        
        title = QLabel("📋 Configuration Summary")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: #28A745; margin: 20px;")
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet("font-size: 18px; background-color: #F8F9FA; border: 2px solid #28A745; border-radius: 10px; padding: 15px;")
        
        nav_layout = QHBoxLayout()
        self.button_back_3 = QPushButton("← Back to Edit")
        self.button_back_3.setMinimumHeight(70)
        self.button_back_3.setStyleSheet(BTN_BASE.format(22, "#6C757D"))
        
        self.button_finish = QPushButton("✓ Finish")
        self.button_finish.setMinimumHeight(70)
        self.button_finish.setStyleSheet(BTN_BASE.format(22, "#28A745"))
        
        nav_layout.addWidget(self.button_back_3)
        nav_layout.addStretch()
        nav_layout.addWidget(self.button_finish)
        
        layout.addWidget(title)
        layout.addWidget(self.summary_text)
        layout.addLayout(nav_layout)
        
        self.page3.setLayout(layout)
        self.page3.setStyleSheet("background-color: white; padding: 20px;")
        
        self.button_back_3.clicked.connect(lambda: self.switch_page(self.page2))
        self.button_finish.clicked.connect(self.finish_and_reset)

    def check_serial_text(self, text):
        style = INPUT_STYLE.format(3 if (os.path.isdir(text) or self.find_folder_by_serial(text)) else 2,
                                   "#28A745" if (os.path.isdir(text) or self.find_folder_by_serial(text)) else "#2E86AB")
        if os.path.isdir(text) or self.find_folder_by_serial(text):
            style += " background-color: #D4EDDA;"
        self.edit_line_path.setStyleSheet(style)
    
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
        base_path = input_text if os.path.isdir(input_text) else self.find_folder_by_serial(input_text)
        
        if not base_path:
            QMessageBox.warning(self, "Error", "Module folder not found for serial: {}\n\nBase directory: {}".format(input_text, self.base_directory))
            return
        
        self.serial_number = os.path.basename(base_path)
        self.base_module_path = base_path
        self.cold_modules.clear()
        self.warm_modules.clear()
        self.cold_ports.clear()
        self.warm_ports.clear()
        self.modified_data.clear()
        
        cold_ok = self.load_config(base_path, "cold")
        warm_ok = self.load_config(base_path, "warm")
        
        if cold_ok and warm_ok:
            all_chips = set(list(self.cold_modules.keys()) + list(self.warm_modules.keys()))
            
            info = "✅ Successfully loaded module: {}\n\n".format(self.serial_number)
            info += "📊 Statistics:\n"
            info += "  • Unique cold configurations: {}\n".format(len(self.cold_modules))
            info += "  • Unique warm configurations: {}\n\n".format(len(self.warm_modules))
            info += "🔌 Front End Configurations:\n\n"
            
            for chipID in sorted(all_chips):
                if chipID in self.cold_modules:
                    config_name = self.cold_modules[chipID].get('config_name', 'N/A')
                    info += "  • ChipID {} (Config: {})\n".format(chipID, config_name)
                    info += "    - Cold configuration loaded ❄️\n"
                    if chipID in self.warm_modules:
                        info += "    - Warm configuration loaded 🔥\n"
                elif chipID in self.warm_modules:
                    config_name = self.warm_modules[chipID].get('config_name', 'N/A')
                    info += "  • ChipID {} (Config: {})\n".format(chipID, config_name)
                    info += "    - Warm configuration loaded 🔥\n"
            
            info += "\n💡 Note: Port connectivity details available in Summary page"
            
            self.info_text.setText(info)
            self.status_label.setText("✅ Module {} loaded successfully".format(self.serial_number))
            self.button_next_1.setEnabled(True)
            
            QMessageBox.information(self, "Success", "Module loaded successfully!\n\nCold modules: {}\nWarm modules: {}".format(len(self.cold_modules), len(self.warm_modules)))
        else:
            QMessageBox.warning(self, "Error", "Failed to load module configurations")

    def load_config(self, base_path, cfg_type):
        config_path = os.path.join(base_path, "L2_" + cfg_type)
        if not os.path.exists(config_path):
            return False
        
        port_files = [f for f in os.listdir(base_path) if f.endswith('.json') and cfg_type in f.lower() and 'YarrPort' in f]
        port_dict = self.cold_ports if cfg_type == "cold" else self.warm_ports
        modules_dict = self.cold_modules if cfg_type == "cold" else self.warm_modules
        
        for port_file in port_files:
            try:
                with open(os.path.join(base_path, port_file), 'r') as f:
                    port_data = json.load(f)
                
                port_name = port_file.replace('.json', '')
                port_dict[port_name] = []
                
                for chip in port_data.get('chips', []):
                    config_file = chip.get('config', '')
                    if not config_file:
                        continue
                    
                    chip_path = os.path.join(base_path, config_file)
                    if not os.path.exists(chip_path):
                        continue
                    
                    with open(chip_path, 'r') as cf:
                        chip_data = json.load(cf)
                    
                    chipID, config_name = None, None
                    for ct in ["ITKPIXV2", "RD53B"]:
                        if ct in chip_data:
                            chipID = chip_data[ct].get("Parameter", {}).get("ChipId")
                            config_name = chip_data[ct].get("Parameter", {}).get("Name")
                            break
                    
                    if chipID is None:
                        continue
                    chipID = str(chipID)
                    
                    port_dict[port_name].append({
                        'chipID': chipID, 'config_name': config_name,
                        'rx': chip.get('rx'), 'tx': chip.get('tx'),
                        'enable': chip.get('enable', 1)
                    })
                    
                    if chipID not in modules_dict:
                        important = ["EnCoreCol0", "EnCoreCol1", "EnCoreCol2", "EnCoreCol3",
                                   "SldoTrimA", "SldoTrimD", "ADCcalPar",
                                   "KSenseInA", "KSenseInD", "KSenseShuntA", "KSenseShuntD"]
                        
                        imp_data = {}
                        for ct in ["ITKPIXV2", "RD53B"]:
                            if ct in chip_data:
                                gc = chip_data[ct].get("GlobalConfig", {})
                                pm = chip_data[ct].get("Parameter", {})
                                for k in important:
                                    if k in gc:
                                        imp_data[k] = gc[k]
                                    elif k in pm:
                                        imp_data[k] = pm[k]
                                break
                        
                        modules_dict[chipID] = {
                            'full_data': chip_data, 'important_data': imp_data,
                            'file_path': chip_path,
                            'config_name': config_name or os.path.basename(chip_path).replace('_L2_{}.json'.format(cfg_type), '')
                        }
            except Exception as e:
                print("Error loading {}: {}".format(port_file, str(e)))
                continue
        
        return len(modules_dict) > 0

    def switch_page(self, page):
        if page == self.page2:
            self.populate_parameter_table()
            self.module_info_label.setText("Module: {}".format(self.serial_number))
        self.stacked_widget.setCurrentWidget(page)
    
    def populate_parameter_table(self):
        self.param_table.setRowCount(0)
        self.param_table.setSortingEnabled(False)
        
        show_cold, show_warm = self.filter_cold.isChecked(), self.filter_warm.isChecked()
        all_chips = set(list(self.cold_modules.keys()) + list(self.warm_modules.keys()))
        
        row = 0
        colors = {
            'cold': {'type_bg': QColor(30, 136, 229), 'item_bg': QColor(255, 220, 200), 'val_bg': QColor(255, 240, 230)},
            'warm': {'type_bg': QColor(255, 107, 53), 'item_bg': QColor(255, 235, 205), 'val_bg': QColor(255, 245, 235)}
        }
        
        for cfg_type in (['cold'] if show_cold else []) + (['warm'] if show_warm else []):
            modules = self.cold_modules if cfg_type == 'cold' else self.warm_modules
            label = "❄️ COLD" if cfg_type == 'cold' else "🔥 WARM"
            clr = colors[cfg_type]
            
            for chipID in sorted(all_chips):
                if chipID not in modules:
                    continue
                    
                module = modules[chipID]
                config_name = module.get('config_name', 'N/A')
                
                for param in sorted(module['important_data'].keys()):
                    self.param_table.insertRow(row)
                    
                    type_item = QTableWidgetItem(label)
                    type_item.setBackground(clr['type_bg'])
                    type_item.setForeground(QColor(255, 255, 255))
                    type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                    self.param_table.setItem(row, 0, type_item)
                    
                    for col, txt, bg in [(1, chipID, clr['item_bg']), (2, config_name, clr['item_bg']), (3, param, clr['item_bg'])]:
                        item = QTableWidgetItem(txt)
                        item.setBackground(bg)
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                        self.param_table.setItem(row, col, item)
                    
                    val_item = QTableWidgetItem(str(module['important_data'][param]))
                    val_item.setBackground(clr['val_bg'])
                    val_item.setForeground(QColor(139, 0, 0))
                    self.param_table.setItem(row, 4, val_item)
                    
                    row += 1
        
        self.param_table.setSortingEnabled(True)
        self.module_info_label.setText("Module: {} | Total entries: {}".format(self.serial_number, self.param_table.rowCount()))

    def edit_parameter(self):
        row = self.param_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "Please select a parameter to edit")
            return
        
        type_txt = self.param_table.item(row, 0).text()
        chipID = self.param_table.item(row, 1).text()
        config_name = self.param_table.item(row, 2).text()
        param = self.param_table.item(row, 3).text()
        curr_val = self.param_table.item(row, 4).text()
        is_cold = "COLD" in type_txt
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Edit {} for Chip {}".format(param, chipID))
        dlg.setMinimumWidth(600)
        dlg.setMinimumHeight(300)
        
        layout = QVBoxLayout()
        
        info = QLabel("❄️ COLD Configuration" if is_cold else "🔥 WARM Configuration")
        info.setStyleSheet("font-size: 22px; font-weight: bold; color: white; background-color: {}; padding: 15px; border-radius: 5px;".format('#1E88E5' if is_cold else '#FF6B35'))
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        det_layout = QVBoxLayout()
        det_layout.setSpacing(10)
        det_style = "font-size: 16px; padding: 5px; background-color: #F8F9FA; border-radius: 3px;"
        
        for txt in ["<b>Parameter:</b> " + param, "<b>ChipID:</b> " + chipID, "<b>Config Name:</b> " + config_name]:
            lbl = QLabel(txt)
            lbl.setStyleSheet(det_style)
            det_layout.addWidget(lbl)
        layout.addLayout(det_layout)
        
        layout.addWidget(QLabel("<b style='font-size: 18px;'>Current Value:</b> <span style='color: {};'>{}</span>".format('#1E88E5' if is_cold else '#FF6B35', curr_val)))
        
        val_input = QLineEdit(curr_val)
        val_input.setStyleSheet("font-size: 18px; padding: 10px; border: 2px solid #2E86AB; border-radius: 5px;")
        val_input.setPlaceholderText("Enter new value")
        layout.addWidget(QLabel("<b>New Value:</b>"))
        layout.addWidget(val_input)
        
        hint = QLabel("ℹ️ Expected type: <i>{}</i>".format(self.get_type_hint(param)))
        hint.setStyleSheet("font-size: 14px; color: #6C757D;")
        layout.addWidget(hint)
        
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.setStyleSheet("font-size: 16px;")
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        dlg.setLayout(layout)
        
        if dlg.exec_() == QDialog.Accepted:
            new_val = val_input.text().strip()
            if not new_val:
                QMessageBox.warning(self, "Error", "Please enter a value")
                return
            
            try:
                conv_val = self.convert_val(param, new_val)
                self.param_table.item(row, 4).setText(str(conv_val))
                
                cfg = "cold" if is_cold else "warm"
                modules = self.cold_modules if is_cold else self.warm_modules
                
                if chipID in modules:
                    modules[chipID]['important_data'][param] = conv_val
                    key = "{}_{}_{}" .format(chipID, param, cfg)
                    self.modified_data[key] = {
                        'chipID': chipID, 'param': param, 'value': conv_val,
                        'type': cfg, 'config_name': config_name
                    }
                    
                    QMessageBox.information(self, "Success", "Parameter updated!\n\nType: {}\nConfig Name: {}\nChipID: {}\nParameter: {}\nOld value: {}\nNew value: {}".format(cfg.upper(), config_name, chipID, param, curr_val, conv_val))
                else:
                    QMessageBox.warning(self, "Error", "Module data not found")
            except ValueError as e:
                QMessageBox.warning(self, "Error", "Invalid value format!\n\n{}\n\nExpected: {}".format(str(e), self.get_type_hint(param)))
            except Exception as e:
                QMessageBox.warning(self, "Error", "Error: {}".format(str(e)))

    def get_type_hint(self, param):
        if param in ["EnCoreCol0", "EnCoreCol1", "EnCoreCol2", "EnCoreCol3", "SldoTrimA", "SldoTrimD"]:
            return "integer"
        elif param == "ADCcalPar":
            return "list (e.g., [1.0, 2.0, 3.0])"
        elif param in ["KSenseInA", "KSenseInD", "KSenseShuntA", "KSenseShuntD"]:
            return "float"
        return "string"

    def convert_val(self, param, val_str):
        if param in ["EnCoreCol0", "EnCoreCol1", "EnCoreCol2", "EnCoreCol3", "SldoTrimA", "SldoTrimD"]:
            return int(val_str)
        elif param == "ADCcalPar":
            return ast.literal_eval(val_str)
        elif param in ["KSenseInA", "KSenseInD", "KSenseShuntA", "KSenseShuntD"]:
            return float(val_str)
        return val_str

    def save_all_changes(self):
        if not self.modified_data:
            QMessageBox.information(self, "Info", "No changes to save")
            return
        
        cold_cnt, warm_cnt = 0, 0
        summary = "The following changes will be saved:\n\n"
        
        for key, mod in self.modified_data.items():
            if mod['type'] == 'cold':
                cold_cnt += 1
                summary += "❄️ COLD - ChipID {}: {} = {}\n".format(mod['chipID'], mod['param'], mod['value'])
            else:
                warm_cnt += 1
                summary += "🔥 WARM - ChipID {}: {} = {}\n".format(mod['chipID'], mod['param'], mod['value'])
        
        summary += "\nTotal: {} cold + {} warm = {} modifications".format(cold_cnt, warm_cnt, len(self.modified_data))
        
        reply = QMessageBox.question(self, "Confirm Save", summary, QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                self.write_files()
                QMessageBox.information(self, "Success", "All changes saved successfully!\n\nFiles saved to:\n{}\n\nCold modifications: {}\nWarm modifications: {}".format(self.file_saved, cold_cnt, warm_cnt))
            except Exception as e:
                QMessageBox.critical(self, "Error", "Failed to save files:\n{}".format(str(e)))

    def write_files(self):
        if not self.base_module_path:
            return
        
        new_path = self.base_module_path + "_modified"
        os.makedirs(new_path, exist_ok=True)
        
        for folder in ["L2_cold", "L2_warm"]:
            os.makedirs(os.path.join(new_path, folder), exist_ok=True)
        
        for cfg_type, modules in [("cold", self.cold_modules), ("warm", self.warm_modules)]:
            cfg_path = os.path.join(new_path, "L2_" + cfg_type)
            
            for chipID, module in modules.items():
                fname = os.path.basename(module['file_path'])
                save_path = os.path.join(cfg_path, fname)
                
                chip_type = "ITKPIXV2" if "ITKPIXV2" in module['full_data'] else "RD53B"
                for param, value in module['important_data'].items():
                    if param in module['full_data'][chip_type]['GlobalConfig']:
                        module['full_data'][chip_type]['GlobalConfig'][param] = value
                    elif param in module['full_data'][chip_type]['Parameter']:
                        module['full_data'][chip_type]['Parameter'][param] = value
                
                with open(save_path, 'w') as f:
                    json.dump(module['full_data'], f, indent=4)
        
        for f in os.listdir(self.base_module_path):
            if f.endswith('.json') and 'YarrPort' in f:
                with open(os.path.join(self.base_module_path, f), 'r') as sf:
                    data = json.load(sf)
                with open(os.path.join(new_path, f), 'w') as df:
                    json.dump(data, df, indent=4)
        
        self.file_saved = new_path

    def go_to_summary(self):
        self.build_summary()
        self.stacked_widget.setCurrentWidget(self.page3)
    
    def build_summary(self):
        summary = "📋 Configuration Summary for Module: {}\n".format(self.serial_number)
        summary += "=" * 80 + "\n\n"
        
        summary += "📊 General Statistics:\n"
        summary += "  • Total cold modules: {}\n".format(len(self.cold_modules))
        summary += "  • Total warm modules: {}\n".format(len(self.warm_modules))
        summary += "  • Total modifications: {}\n\n".format(len(self.modified_data))
        
        summary += "🔌 Connectivity Information (Port Assignments):\n\n"
        
        summary += "  COLD Configuration:\n"
        for port_name, chips in self.cold_ports.items():
            summary += "    {}:\n".format(port_name)
            for chip_info in chips:
                status = "✓ Enabled" if chip_info['enable'] else "✗ Disabled"
                cfg_name = chip_info.get('config_name', 'N/A')
                summary += "      • Config: {} (ChipID {}): RX={}, TX={} [{}]\n".format(cfg_name, chip_info['chipID'], chip_info['rx'], chip_info['tx'], status)
        
        summary += "\n  WARM Configuration:\n"
        for port_name, chips in self.warm_ports.items():
            summary += "    {}:\n".format(port_name)
            for chip_info in chips:
                status = "✓ Enabled" if chip_info['enable'] else "✗ Disabled"
                cfg_name = chip_info.get('config_name', 'N/A')
                summary += "      • Config: {} (ChipID {}): RX={}, TX={} [{}]\n".format(cfg_name, chip_info['chipID'], chip_info['rx'], chip_info['tx'], status)
        
        if self.modified_data:
            summary += "\n" + "=" * 80 + "\n"
            summary += "✏️ Modified Parameters:\n\n"
            for key, mod in self.modified_data.items():
                cfg_name = mod.get('config_name', 'N/A')
                summary += "  • {} - Config: {} (ChipID {}): {} = {}\n".format(mod['type'].upper(), cfg_name, mod['chipID'], mod['param'], mod['value'])
        else:
            summary += "\n" + "=" * 80 + "\n"
            summary += "ℹ️ No parameters were modified\n\n"
        
        summary += "=" * 80 + "\n"
        summary += "📝 All Parameters by Chip:\n\n"
        
        all_chips = set(list(self.cold_modules.keys()) + list(self.warm_modules.keys()))
        
        for chipID in sorted(all_chips):
            summary += "  ChipID {}:\n".format(chipID)
            
            if chipID in self.cold_modules:
                cfg_name = self.cold_modules[chipID].get('config_name', 'N/A')
                summary += "    Config Name: {}\n".format(cfg_name)
                summary += "    Cold Parameters:\n"
                for param, value in sorted(self.cold_modules[chipID]['important_data'].items()):
                    summary += "      • {}: {}\n".format(param, value)
            
            if chipID in self.warm_modules:
                cfg_name = self.warm_modules[chipID].get('config_name', 'N/A')
                if chipID not in self.cold_modules:
                    summary += "    Config Name: {}\n".format(cfg_name)
                summary += "    Warm Parameters:\n"
                for param, value in sorted(self.warm_modules[chipID]['important_data'].items()):
                    summary += "      • {}: {}\n".format(param, value)
            summary += "\n"
        
        summary += "=" * 80 + "\n"
        summary += "💾 Files saved to: {}\n".format(self.file_saved) if self.file_saved else "⚠️ Changes not saved to disk yet\n"
        summary += "\n" + "=" * 80 + "\n"
        summary += "✅ Summary generated successfully\n"
        
        self.summary_text.setText(summary)
    
    def finish_and_reset(self):
        reply = QMessageBox.question(self, "Finish", "Return to start screen?\n\nAll unsaved changes will be lost.", QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.cold_modules.clear()
            self.warm_modules.clear()
            self.cold_ports.clear()
            self.warm_ports.clear()
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