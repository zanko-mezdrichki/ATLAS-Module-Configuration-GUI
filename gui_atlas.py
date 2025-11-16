import sys
import json
import ast
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget,
                             QVBoxLayout, QPushButton, QLineEdit, QHBoxLayout,
                             QMessageBox, QLabel, QStackedWidget, QFileDialog,
                             QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                             QGroupBox, QDialog, QDialogButtonBox)
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt


class StyleConfig:

    BTN_BASE = "font-size: {}px; background-color: {}; color: white; border-radius: 5px; font-weight: bold;"
    INPUT_STYLE = "font-size: 24px; padding: 10px; border: {}px solid {}; border-radius: 5px;"
    
    COLORS = {
        'cold': {
            'type_bg': QColor(30, 136, 229),
            'item_bg': QColor(255, 220, 200),
            'val_bg': QColor(255, 240, 230),
            'header': '#1E88E5'
        },
        'warm': {
            'type_bg': QColor(255, 107, 53),
            'item_bg': QColor(255, 235, 205),
            'val_bg': QColor(255, 245, 235),
            'header': '#FF6B35'
        }
    }
    
    @staticmethod
    def get_button_style(size, color):
        return StyleConfig.BTN_BASE.format(size, color)
    
    @staticmethod
    def get_input_style(border_width, border_color, highlight=False):
        style = StyleConfig.INPUT_STYLE.format(border_width, border_color)
        if highlight:
            style += " background-color: #D4EDDA;"
        return style


class ModuleData:
    
    def __init__(self):
        self.cold_modules = {}
        self.warm_modules = {}
        self.cold_ports = {}
        self.warm_ports = {}
        self.modified_data = {}
        self.serial_number = None
        self.file_saved = None
        self.base_module_path = None
        
    def clear(self):
        self.cold_modules.clear()
        self.warm_modules.clear()
        self.cold_ports.clear()
        self.warm_ports.clear()
        self.modified_data.clear()
        self.serial_number = None
        self.file_saved = None
        self.base_module_path = None
    
    def get_all_chip_ids(self):
        return set(list(self.cold_modules.keys()) + list(self.warm_modules.keys()))
    
    def get_module_by_type(self, config_type):
        return self.cold_modules if config_type == 'cold' else self.warm_modules
    
    def get_ports_by_type(self, config_type):
        return self.cold_ports if config_type == 'cold' else self.warm_ports


class ParameterValidator:
    
    TYPE_HINTS = {
        "EnCoreCol0": "integer",
        "EnCoreCol1": "integer",
        "EnCoreCol2": "integer",
        "EnCoreCol3": "integer",
        "SldoTrimA": "integer",
        "SldoTrimD": "integer",
        "ADCcalPar": "list (e.g., [1.0, 2.0, 3.0])",
        "KSenseInA": "float",
        "KSenseInD": "float",
        "KSenseShuntA": "float",
        "KSenseShuntD": "float"
    }
    
    INTEGER_PARAMS = ["EnCoreCol0", "EnCoreCol1", "EnCoreCol2", "EnCoreCol3", 
                      "SldoTrimA", "SldoTrimD"]
    FLOAT_PARAMS = ["KSenseInA", "KSenseInD", "KSenseShuntA", "KSenseShuntD"]
    LIST_PARAMS = ["ADCcalPar"]
    
    @staticmethod
    def get_type_hint(param):
        return ParameterValidator.TYPE_HINTS.get(param, "string")
    
    @staticmethod
    def convert_value(param, val_str):
        if param in ParameterValidator.INTEGER_PARAMS:
            return int(val_str)
        elif param in ParameterValidator.LIST_PARAMS:
            return ast.literal_eval(val_str)
        elif param in ParameterValidator.FLOAT_PARAMS:
            return float(val_str)
        return val_str


class ConfigLoader:
    
    IMPORTANT_PARAMS = [
        "EnCoreCol0", "EnCoreCol1", "EnCoreCol2", "EnCoreCol3",
        "SldoTrimA", "SldoTrimD", "ADCcalPar",
        "KSenseInA", "KSenseInD", "KSenseShuntA", "KSenseShuntD"
    ]
    
    CHIP_TYPES = ["ITKPIXV2", "RD53B"]
    
    @staticmethod
    def load_config(base_path, cfg_type, module_data):
        config_path = os.path.join(base_path, f"L2_{cfg_type}")
        if not os.path.exists(config_path):
            return False
        
        port_files = [f for f in os.listdir(base_path) 
                     if f.endswith('.json') and cfg_type in f.lower() and 'YarrPort' in f]
        
        port_dict = module_data.get_ports_by_type(cfg_type)
        modules_dict = module_data.get_module_by_type(cfg_type)
        
        for port_file in port_files:
            try:
                ConfigLoader._load_port_file(base_path, port_file, cfg_type, 
                                            port_dict, modules_dict)
            except Exception as e:
                print(f"Error loading {port_file}: {str(e)}")
                continue
        
        return len(modules_dict) > 0
    
    @staticmethod
    def _load_port_file(base_path, port_file, cfg_type, port_dict, modules_dict):
        with open(os.path.join(base_path, port_file), 'r') as f:
            port_data = json.load(f)
        
        port_name = port_file.replace('.json', '')
        port_dict[port_name] = []
        
        for chip in port_data.get('chips', []):
            ConfigLoader._process_chip(base_path, chip, cfg_type, 
                                      port_dict[port_name], modules_dict)
    
    @staticmethod
    def _process_chip(base_path, chip, cfg_type, port_list, modules_dict):
        config_file = chip.get('config', '')
        if not config_file:
            return
        
        chip_path = os.path.join(base_path, config_file)
        if not os.path.exists(chip_path):
            return
        
        with open(chip_path, 'r') as cf:
            chip_data = json.load(cf)
        
        chipID, config_name = ConfigLoader._extract_chip_info(chip_data)
        if chipID is None:
            return
        
        chipID = str(chipID)
        
        port_list.append({
            'chipID': chipID,
            'config_name': config_name,
            'rx': chip.get('rx'),
            'tx': chip.get('tx'),
            'enable': chip.get('enable', 1)
        })
        
        if chipID not in modules_dict:
            modules_dict[chipID] = ConfigLoader._create_module_entry(
                chip_data, chip_path, config_file, cfg_type, config_name
            )
    
    @staticmethod
    def _extract_chip_info(chip_data):
        for chip_type in ConfigLoader.CHIP_TYPES:
            if chip_type in chip_data:
                params = chip_data[chip_type].get("Parameter", {})
                chipID = params.get("ChipId")
                config_name = params.get("Name")
                return chipID, config_name
        return None, None
    
    @staticmethod
    def _create_module_entry(chip_data, chip_path, config_file, cfg_type, config_name):
        imp_data = {}
        
        for chip_type in ConfigLoader.CHIP_TYPES:
            if chip_type in chip_data:
                gc = chip_data[chip_type].get("GlobalConfig", {})
                pm = chip_data[chip_type].get("Parameter", {})
                
                for param in ConfigLoader.IMPORTANT_PARAMS:
                    if param in gc:
                        imp_data[param] = gc[param]
                    elif param in pm:
                        imp_data[param] = pm[param]
                break
        
        return {
            'full_data': chip_data,
            'important_data': imp_data,
            'file_path': chip_path,
            'config_name': config_name or os.path.basename(chip_path).replace(f'_L2_{cfg_type}.json', '')
        }

class FileSaver:
    
    @staticmethod
    def save_changes(module_data):
        if not module_data.base_module_path:
            raise ValueError("Nessun percorso base modulo definito")
        
        new_path = module_data.base_module_path + "_modified"
        os.makedirs(new_path, exist_ok=True)
        
        for folder in ["L2_cold", "L2_warm"]:
            os.makedirs(os.path.join(new_path, folder), exist_ok=True)
        
        FileSaver._save_module_configs(new_path, module_data)
        
        FileSaver._copy_port_files(module_data.base_module_path, new_path)
        
        module_data.file_saved = new_path
        return new_path
    
    @staticmethod
    def _save_module_configs(new_path, module_data):
        for cfg_type in ["cold", "warm"]:
            cfg_path = os.path.join(new_path, f"L2_{cfg_type}")
            modules = module_data.get_module_by_type(cfg_type)
            
            for chipID, module in modules.items():
                FileSaver._save_single_module(cfg_path, module)
    
    @staticmethod
    def _save_single_module(cfg_path, module):
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
    
    @staticmethod
    def _copy_port_files(source_path, dest_path):
        for f in os.listdir(source_path):
            if f.endswith('.json') and 'YarrPort' in f:
                with open(os.path.join(source_path, f), 'r') as sf:
                    data = json.load(sf)
                with open(os.path.join(dest_path, f), 'w') as df:
                    json.dump(data, df, indent=4)


class SummaryBuilder:
    
    @staticmethod
    def build_summary(module_data):
        lines = []
        lines.append(f"📋 Configuration Summary for Module: {module_data.serial_number}")
        lines.append("=" * 80)
        lines.append("")
        
        SummaryBuilder._add_statistics(lines, module_data)
        SummaryBuilder._add_connectivity(lines, module_data)
        SummaryBuilder._add_modifications(lines, module_data)
        SummaryBuilder._add_all_parameters(lines, module_data)
        SummaryBuilder._add_footer(lines, module_data)
        
        return "\n".join(lines)
    
    @staticmethod
    def _add_statistics(lines, module_data):
        lines.append("📊 General Statistics:")
        lines.append(f"  • Total cold modules: {len(module_data.cold_modules)}")
        lines.append(f"  • Total warm modules: {len(module_data.warm_modules)}")
        lines.append(f"  • Total modifications: {len(module_data.modified_data)}")
        lines.append("")
    
    @staticmethod
    def _add_connectivity(lines, module_data):
        lines.append("🔌 Connectivity Information (Port Assignments):")
        lines.append("")
        
        for cfg_type, label in [("cold", "COLD"), ("warm", "WARM")]:
            lines.append(f"  {label} Configuration:")
            ports = module_data.get_ports_by_type(cfg_type)
            
            for port_name, chips in ports.items():
                lines.append(f"    {port_name}:")
                for chip_info in chips:
                    status = "✓ Enabled" if chip_info['enable'] else "✗ Disabled"
                    cfg_name = chip_info.get('config_name', 'N/A')
                    lines.append(f"      • Config: {cfg_name} (ChipID {chip_info['chipID']}): "
                               f"RX={chip_info['rx']}, TX={chip_info['tx']} [{status}]")
            lines.append("")
    
    @staticmethod
    def _add_modifications(lines, module_data):
        lines.append("=" * 80)
        
        if module_data.modified_data:
            lines.append("✏️ Modified Parameters:")
            lines.append("")
            
            for key, mod in module_data.modified_data.items():
                cfg_name = mod.get('config_name', 'N/A')
                lines.append(f"  • {mod['type'].upper()} - Config: {cfg_name} "
                           f"(ChipID {mod['chipID']}): {mod['param']} = {mod['value']}")
        else:
            lines.append("ℹ️ No parameters were modified")
            lines.append("")
    
    @staticmethod
    def _add_all_parameters(lines, module_data):
        lines.append("=" * 80)
        lines.append("📝 All Parameters by Chip:")
        lines.append("")
        
        all_chips = module_data.get_all_chip_ids()
        
        for chipID in sorted(all_chips):
            lines.append(f"  ChipID {chipID}:")
            
            if chipID in module_data.cold_modules:
                cfg_name = module_data.cold_modules[chipID].get('config_name', 'N/A')
                lines.append(f"    Config Name: {cfg_name}")
                lines.append("    Cold Parameters:")
                for param, value in sorted(module_data.cold_modules[chipID]['important_data'].items()):
                    lines.append(f"      • {param}: {value}")
            
            if chipID in module_data.warm_modules:
                cfg_name = module_data.warm_modules[chipID].get('config_name', 'N/A')
                if chipID not in module_data.cold_modules:
                    lines.append(f"    Config Name: {cfg_name}")
                lines.append("    Warm Parameters:")
                for param, value in sorted(module_data.warm_modules[chipID]['important_data'].items()):
                    lines.append(f"      • {param}: {value}")
            lines.append("")
    
    @staticmethod
    def _add_footer(lines, module_data):
        lines.append("=" * 80)
        if module_data.file_saved:
            lines.append(f"💾 Files saved to: {module_data.file_saved}")
        else:
            lines.append("⚠️ Changes not saved to disk yet")
        lines.append("")
        lines.append("=" * 80)
        lines.append("✅ Summary generated successfully")


class EditParameterDialog(QDialog):
    
    def __init__(self, parent, param_info):
        super().__init__(parent)
        self.param_info = param_info
        self.new_value = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle(f"Edit {self.param_info['param']} for Chip {self.param_info['chipID']}")
        self.setMinimumWidth(600)
        self.setMinimumHeight(300)
        
        layout = QVBoxLayout()
        
        is_cold = self.param_info['is_cold']
        header = QLabel("❄️ COLD Configuration" if is_cold else "🔥 WARM Configuration")
        header.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: white; "
            f"background-color: {StyleConfig.COLORS['cold']['header'] if is_cold else StyleConfig.COLORS['warm']['header']}; "
            f"padding: 15px; border-radius: 5px;"
        )
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        self._add_details(layout)
        
        layout.addWidget(QLabel(f"<b style='font-size: 18px;'>Current Value:</b> "
                               f"<span style='color: {StyleConfig.COLORS['cold']['header'] if is_cold else StyleConfig.COLORS['warm']['header']};'>"
                               f"{self.param_info['current_value']}</span>"))
        
        self.value_input = QLineEdit(self.param_info['current_value'])
        self.value_input.setStyleSheet(
            "font-size: 18px; padding: 10px; border: 2px solid #2E86AB; border-radius: 5px;"
        )
        self.value_input.setPlaceholderText("Enter new value")
        layout.addWidget(QLabel("<b>New Value:</b>"))
        layout.addWidget(self.value_input)
        
        hint = QLabel(f"ℹ️ Expected type: <i>{ParameterValidator.get_type_hint(self.param_info['param'])}</i>")
        hint.setStyleSheet("font-size: 14px; color: #6C757D;")
        layout.addWidget(hint)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet("font-size: 16px;")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def _add_details(self, layout):
        details_layout = QVBoxLayout()
        details_layout.setSpacing(10)
        detail_style = "font-size: 16px; padding: 5px; background-color: #F8F9FA; border-radius: 3px;"
        
        for text in [
            f"<b>Parameter:</b> {self.param_info['param']}",
            f"<b>ChipID:</b> {self.param_info['chipID']}",
            f"<b>Config Name:</b> {self.param_info['config_name']}"
        ]:
            label = QLabel(text)
            label.setStyleSheet(detail_style)
            details_layout.addWidget(label)
        
        layout.addLayout(details_layout)
    
    def get_new_value(self):
        val_str = self.value_input.text().strip()
        if not val_str:
            raise ValueError("Please enter a value")
        
        return ParameterValidator.convert_value(self.param_info['param'], val_str)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ATLAS Module Configuration GUI")
        self.setGeometry(700, 300, 1200, 700)
        
        self.base_directory = "//wsl$/Ubuntu/home/zanko/pf_labs/Interfaccia"
        self.module_data = ModuleData()
        self.style_config = StyleConfig()
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.page1 = QWidget()
        self.page2 = QWidget()
        self.page3 = QWidget()
        
        self.stacked_widget.addWidget(self.page1)
        self.stacked_widget.addWidget(self.page2)
        self.stacked_widget.addWidget(self.page3)
        
        self.setup_page1()
        self.setup_page2()
        self.setup_page3()
    
    def connect_signals(self):

        # Page 1
        self.edit_line_path.textChanged.connect(self.check_serial_text)
        self.button_browse.clicked.connect(self.browse_folder)
        self.button_load.clicked.connect(self.load_module_data)
        self.button_next_1.clicked.connect(lambda: self.switch_page(self.page2))
        
        # Page 2
        self.button_edit.clicked.connect(self.edit_parameter)
        self.button_save.clicked.connect(self.save_all_changes)
        self.button_back_2.clicked.connect(lambda: self.switch_page(self.page1))
        self.button_next_2.clicked.connect(self.go_to_summary)
        self.button_refresh.clicked.connect(self.populate_parameter_table)
        
        # Page 3
        self.button_back_3.clicked.connect(lambda: self.switch_page(self.page2))
        self.button_finish.clicked.connect(self.finish_and_reset)

    def setup_page1(self):
        layout = QVBoxLayout()
        
        title = QLabel("📡 ATLAS Module Configuration System")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: #2E86AB; margin: 20px;")
        
        self.status_label = QLabel("📁 Enter module serial number")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            "font-size: 24px; color: #FFD700; background-color: rgba(46, 134, 171, 50); "
            "padding: 15px; border-radius: 10px; border: 2px solid #2E86AB;"
        )
        
        input_group = self.create_input_group()
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMinimumHeight(250)
        self.info_text.setStyleSheet(
            "font-size: 16px; background-color: #F8F9FA; border: 2px solid #2E86AB; "
            "border-radius: 5px; padding: 10px;"
        )
        self.info_text.setText(
            "ℹ️ Waiting for module data...\n\n"
            "This system will load:\n"
            "• Cold configuration files\n"
            "• Warm configuration files\n"
            "• Port and RX channel information"
        )
        
        self.button_next_1 = QPushButton("Next → Modify Parameters")
        self.button_next_1.setMinimumHeight(70)
        self.button_next_1.setEnabled(False)
        self.button_next_1.setStyleSheet(StyleConfig.get_button_style(24, "#28A745"))
        
        layout.addWidget(title)
        layout.addWidget(self.status_label)
        layout.addWidget(input_group)
        layout.addWidget(self.info_text)
        layout.addStretch()
        layout.addWidget(self.button_next_1)
        
        self.page1.setLayout(layout)
        self.page1.setStyleSheet("background-color: white; padding: 20px;")
    
    def create_input_group(self):
        input_group = QGroupBox("Module Selection")
        input_group.setStyleSheet("font-size: 20px; font-weight: bold;")
        input_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        self.edit_line_path = QLineEdit()
        self.edit_line_path.setPlaceholderText("Enter serial number (e.g., 20UPGM22110267)")
        self.edit_line_path.setMinimumHeight(60)
        self.edit_line_path.setStyleSheet(StyleConfig.get_input_style(2, "#2E86AB"))
        
        self.button_browse = QPushButton("Browse")
        self.button_browse.setMinimumHeight(60)
        self.button_browse.setMinimumWidth(120)
        self.button_browse.setStyleSheet(StyleConfig.get_button_style(20, "#6C757D"))
        
        path_layout.addWidget(self.edit_line_path, stretch=4)
        path_layout.addWidget(self.button_browse, stretch=1)
        input_layout.addLayout(path_layout)
        
        self.button_load = QPushButton("🔍 Load Module Data")
        self.button_load.setMinimumHeight(70)
        self.button_load.setStyleSheet(StyleConfig.get_button_style(24, "#2E86AB"))
        input_layout.addWidget(self.button_load)
        
        input_group.setLayout(input_layout)
        return input_group

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
        
        filter_layout = self.create_filter_layout()
        
        self.param_table = self.create_parameter_table()
        
        button_layout = QHBoxLayout()
        self.button_edit = QPushButton("✏️ Edit Selected")
        self.button_edit.setMinimumHeight(60)
        self.button_edit.setStyleSheet(StyleConfig.get_button_style(20, "#007BFF"))
        
        self.button_save = QPushButton("💾 Save All Changes")
        self.button_save.setMinimumHeight(60)
        self.button_save.setStyleSheet(StyleConfig.get_button_style(20, "#FFC107"))
        
        button_layout.addWidget(self.button_edit)
        button_layout.addWidget(self.button_save)
        
        nav_layout = QHBoxLayout()
        self.button_back_2 = QPushButton("← Back")
        self.button_back_2.setMinimumHeight(60)
        self.button_back_2.setStyleSheet(StyleConfig.get_button_style(20, "#6C757D"))
        
        self.button_next_2 = QPushButton("Next → Summary")
        self.button_next_2.setMinimumHeight(60)
        self.button_next_2.setStyleSheet(StyleConfig.get_button_style(20, "#28A745"))
        
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
    
    def create_filter_layout(self):
        filter_layout = QHBoxLayout()
        
        legend_label = QLabel("🎨 Legend: ")
        legend_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        filter_layout.addWidget(legend_label)
        
        cold_legend = QLabel("■ COLD (Left Column)")
        cold_legend.setStyleSheet(
            "font-size: 16px; color: white; background-color: #1E88E5; "
            "padding: 5px 10px; border-radius: 3px; font-weight: bold;"
        )
        filter_layout.addWidget(cold_legend)
        
        warm_legend = QLabel("■ WARM (Right Column)")
        warm_legend.setStyleSheet(
            "font-size: 16px; color: white; background-color: #FF6B35; "
            "padding: 5px 10px; border-radius: 3px; font-weight: bold;"
        )
        filter_layout.addWidget(warm_legend)
        filter_layout.addSpacing(30)
        
        info_label = QLabel("ℹ️ Click on Cold or Warm value to edit")
        info_label.setStyleSheet("font-size: 16px; color: #495057; font-style: italic;")
        filter_layout.addWidget(info_label)
        
        self.button_refresh = QPushButton("🔄 Refresh Table")
        self.button_refresh.setMinimumHeight(40)
        self.button_refresh.setStyleSheet(StyleConfig.get_button_style(16, "#17A2B8") + " padding: 5px 15px;")
        filter_layout.addWidget(self.button_refresh)
        filter_layout.addStretch()
        
        return filter_layout
    
    def create_parameter_table(self):
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["ChipID", "Config Name", "Parameter", 
                                         "❄️ Cold Value", "🔥 Warm Value", "Status"])
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
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
        table.setSortingEnabled(True)
        
        return table

    def setup_page3(self):
        layout = QVBoxLayout()
        
        title = QLabel("📋 Configuration Summary")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: #28A745; margin: 20px;")
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet(
            "font-size: 18px; background-color: #F8F9FA; border: 2px solid #28A745; "
            "border-radius: 10px; padding: 15px;"
        )
        
        nav_layout = QHBoxLayout()
        self.button_back_3 = QPushButton("← Back to Edit")
        self.button_back_3.setMinimumHeight(70)
        self.button_back_3.setStyleSheet(StyleConfig.get_button_style(22, "#6C757D"))
        
        self.button_finish = QPushButton("✓ Finish")
        self.button_finish.setMinimumHeight(70)
        self.button_finish.setStyleSheet(StyleConfig.get_button_style(22, "#28A745"))
        
        nav_layout.addWidget(self.button_back_3)
        nav_layout.addStretch()
        nav_layout.addWidget(self.button_finish)
        
        layout.addWidget(title)
        layout.addWidget(self.summary_text)
        layout.addLayout(nav_layout)
        
        self.page3.setLayout(layout)
        self.page3.setStyleSheet("background-color: white; padding: 20px;")

    def check_serial_text(self, text):
        is_valid = os.path.isdir(text) or self.find_folder_by_serial(text)
        style = StyleConfig.get_input_style(
            3 if is_valid else 2,
            "#28A745" if is_valid else "#2E86AB",
            highlight=is_valid
        )
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
        self.module_data.clear()
        
        input_text = self.edit_line_path.text().strip() 
        base_path = input_text if os.path.isdir(input_text) else self.find_folder_by_serial(input_text)
        
        if not base_path:
            QMessageBox.warning(
                self, "Error",
                f"Module folder not found for serial: {input_text}\n\n"
                f"Base directory: {self.base_directory}"
            )
            return
        
        self.module_data.serial_number = os.path.basename(base_path)
        self.module_data.base_module_path = base_path 
        
        cold_ok = ConfigLoader.load_config(base_path, "cold", self.module_data)
        warm_ok = ConfigLoader.load_config(base_path, "warm", self.module_data)
        
        if cold_ok and warm_ok:
            self.show_load_success()
        else:
            QMessageBox.warning(self, "Error", "Failed to load module configurations")
    
    def show_load_success(self):
        all_chips = self.module_data.get_all_chip_ids()
        
        info_lines = [
            f"✅ Successfully loaded module: {self.module_data.serial_number}\n",
            "📊 Statistics:",
            f"  • Unique cold configurations: {len(self.module_data.cold_modules)}",
            f"  • Unique warm configurations: {len(self.module_data.warm_modules)}\n",
            "🔌 Front End Configurations:\n"
        ]
        
        for chipID in sorted(all_chips):
            if chipID in self.module_data.cold_modules:
                config_name = self.module_data.cold_modules[chipID].get('config_name', 'N/A')
                info_lines.append(f"  • ChipID {chipID} (Config: {config_name})")
                info_lines.append("    - Cold configuration loaded ❄️")
                if chipID in self.module_data.warm_modules:
                    info_lines.append("    - Warm configuration loaded 🔥")
            elif chipID in self.module_data.warm_modules:
                config_name = self.module_data.warm_modules[chipID].get('config_name', 'N/A')
                info_lines.append(f"  • ChipID {chipID} (Config: {config_name})")
                info_lines.append("    - Warm configuration loaded 🔥")
        
        info_lines.append("\n💡 Note: Port connectivity details available in Summary page")
        
        self.info_text.setText("\n".join(info_lines))
        self.status_label.setText(f"✅ Module {self.module_data.serial_number} loaded successfully")
        self.button_next_1.setEnabled(True)
        
        QMessageBox.information(
            self, "Success",
            f"Module loaded successfully!\n\n"
            f"Cold modules: {len(self.module_data.cold_modules)}\n"
            f"Warm modules: {len(self.module_data.warm_modules)}"
        )

    def switch_page(self, page):
        if page == self.page2:
            self.populate_parameter_table()
            self.module_info_label.setText(f"Module: {self.module_data.serial_number}")
        self.stacked_widget.setCurrentWidget(page)
    
    def populate_parameter_table(self):
        self.param_table.setRowCount(0)
        self.param_table.setSortingEnabled(False)
        
        all_chips = self.module_data.get_all_chip_ids()
        
        all_params = set()
        for chipID in all_chips:
            if chipID in self.module_data.cold_modules:
                all_params.update(self.module_data.cold_modules[chipID]['important_data'].keys())
            if chipID in self.module_data.warm_modules:
                all_params.update(self.module_data.warm_modules[chipID]['important_data'].keys())
        
        row = 0
        for chipID in sorted(all_chips):
            cold_module = self.module_data.cold_modules.get(chipID)
            warm_module = self.module_data.warm_modules.get(chipID)
            
            config_name = 'N/A'
            if cold_module:
                config_name = cold_module.get('config_name', 'N/A')
            elif warm_module:
                config_name = warm_module.get('config_name', 'N/A')
            
            chip_params = set()
            if cold_module:
                chip_params.update(cold_module['important_data'].keys())
            if warm_module:
                chip_params.update(warm_module['important_data'].keys())
            
            for param in sorted(chip_params):
                self.add_combined_table_row(row, chipID, config_name, param, 
                                           cold_module, warm_module)
                row += 1
        
        self.param_table.setSortingEnabled(True)
        self.module_info_label.setText(
            f"Module: {self.module_data.serial_number} | Total parameters: {self.param_table.rowCount()}"
        )
    
    def add_combined_table_row(self, row, chipID, config_name, param, cold_module, warm_module):
        self.param_table.insertRow(row)
        
        chip_item = QTableWidgetItem(chipID)
        chip_item.setFlags(chip_item.flags() & ~Qt.ItemIsEditable)
        chip_item.setBackground(QColor(240, 240, 240))
        self.param_table.setItem(row, 0, chip_item)
        
        config_item = QTableWidgetItem(config_name)
        config_item.setFlags(config_item.flags() & ~Qt.ItemIsEditable)
        config_item.setBackground(QColor(240, 240, 240))
        self.param_table.setItem(row, 1, config_item)
        
        param_item = QTableWidgetItem(param)
        param_item.setFlags(param_item.flags() & ~Qt.ItemIsEditable)
        param_item.setBackground(QColor(240, 240, 240))
        self.param_table.setItem(row, 2, param_item)
        
        if cold_module and param in cold_module['important_data']:
            cold_value = str(cold_module['important_data'][param])
            cold_item = QTableWidgetItem(cold_value)
            cold_item.setBackground(StyleConfig.COLORS['cold']['val_bg'])
            cold_item.setForeground(QColor(0, 100, 200))
            cold_item.setFlags(cold_item.flags() & ~Qt.ItemIsEditable)
        else:
            cold_item = QTableWidgetItem("N/A")
            cold_item.setBackground(QColor(220, 220, 220))
            cold_item.setForeground(QColor(150, 150, 150))
            cold_item.setFlags(cold_item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
        self.param_table.setItem(row, 3, cold_item)
        
        if warm_module and param in warm_module['important_data']:
            warm_value = str(warm_module['important_data'][param])
            warm_item = QTableWidgetItem(warm_value)
            warm_item.setBackground(StyleConfig.COLORS['warm']['val_bg'])
            warm_item.setForeground(QColor(200, 50, 0))
            warm_item.setFlags(warm_item.flags() & ~Qt.ItemIsEditable)
        else:
            warm_item = QTableWidgetItem("N/A")
            warm_item.setBackground(QColor(220, 220, 220))
            warm_item.setForeground(QColor(150, 150, 150))
            warm_item.setFlags(warm_item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
        self.param_table.setItem(row, 4, warm_item)
        
        status_text = ""
        if f"{chipID}_{param}_cold" in self.module_data.modified_data:
            status_text += "❄️"
        if f"{chipID}_{param}_warm" in self.module_data.modified_data:
            status_text += "🔥"
        
        status_item = QTableWidgetItem(status_text if status_text else "—")
        status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
        status_item.setBackground(QColor(255, 255, 200) if status_text else QColor(255, 255, 255))
        status_item.setTextAlignment(Qt.AlignCenter)
        self.param_table.setItem(row, 5, status_item)

    def edit_parameter(self):
        row = self.param_table.currentRow()
        col = self.param_table.currentColumn()
        
        if row < 0:
            QMessageBox.warning(self, "Warning", "Please select a parameter to edit")
            return
        
        if col not in [3, 4]:
            QMessageBox.warning(self, "Warning", "Please click on a Cold or Warm value cell to edit")
            return
        
        is_cold = (col == 3)
        cfg_type = "cold" if is_cold else "warm"
        
        cell_item = self.param_table.item(row, col)
        if cell_item.text() == "N/A":
            QMessageBox.warning(
                self, "Warning",
                f"This parameter does not have a {cfg_type.upper()} configuration"
            )
            return
        
        param_info = self.extract_parameter_info_from_combined_row(row, is_cold)
        
        dialog = EditParameterDialog(self, param_info)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                new_value = dialog.get_new_value()
                self.apply_parameter_change_combined(row, col, param_info, new_value)
            except ValueError as e:
                QMessageBox.warning(
                    self, "Error",
                    f"Invalid value format!\n\n{str(e)}\n\n"
                    f"Expected: {ParameterValidator.get_type_hint(param_info['param'])}"
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error: {str(e)}")
    
    def extract_parameter_info_from_combined_row(self, row, is_cold):
        chipID = self.param_table.item(row, 0).text()
        config_name = self.param_table.item(row, 1).text()
        param = self.param_table.item(row, 2).text()
        
        col = 3 if is_cold else 4
        current_value = self.param_table.item(row, col).text()
        
        return {
            'chipID': chipID,
            'config_name': config_name,
            'param': param,
            'current_value': current_value,
            'is_cold': is_cold
        }
    
    def apply_parameter_change_combined(self, row, col, param_info, new_value):
        self.param_table.item(row, col).setText(str(new_value))
        
        cfg_type = "cold" if param_info['is_cold'] else "warm"
        modules = self.module_data.get_module_by_type(cfg_type)
        chipID = param_info['chipID']
        
        if chipID in modules:
            modules[chipID]['important_data'][param_info['param']] = new_value
            
            key = f"{chipID}_{param_info['param']}_{cfg_type}"
            self.module_data.modified_data[key] = {
                'chipID': chipID,
                'param': param_info['param'],
                'value': new_value,
                'type': cfg_type,
                'config_name': param_info['config_name']
            }
            
            status_text = ""
            if f"{chipID}_{param_info['param']}_cold" in self.module_data.modified_data:
                status_text += "❄️"
            if f"{chipID}_{param_info['param']}_warm" in self.module_data.modified_data:
                status_text += "🔥"
            
            status_item = self.param_table.item(row, 5)
            status_item.setText(status_text if status_text else "—")
            status_item.setBackground(QColor(255, 255, 200) if status_text else QColor(255, 255, 255))
            
            QMessageBox.information(
                self, "Success",
                f"Parameter updated!\n\n"
                f"Type: {cfg_type.upper()}\n"
                f"Config Name: {param_info['config_name']}\n"
                f"ChipID: {chipID}\n"
                f"Parameter: {param_info['param']}\n"
                f"Old value: {param_info['current_value']}\n"
                f"New value: {new_value}"
            )
        else:
            QMessageBox.warning(self, "Error", "Module data not found")

    def save_all_changes(self):
        if not self.module_data.modified_data:
            QMessageBox.information(self, "Info", "No changes to save")
            return
        
        summary = self.build_save_summary()
        
        reply = QMessageBox.question(
            self, "Confirm Save", summary,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                saved_path = FileSaver.save_changes(self.module_data)
                cold_cnt, warm_cnt = self.count_modifications()
                
                QMessageBox.information(
                    self, "Success",
                    f"All changes saved successfully!\n\n"
                    f"Files saved to:\n{saved_path}\n\n"
                    f"Cold modifications: {cold_cnt}\n"
                    f"Warm modifications: {warm_cnt}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save files:\n{str(e)}")
    
    def build_save_summary(self):
        cold_cnt, warm_cnt = self.count_modifications()
        
        lines = ["The following changes will be saved:\n"]
        
        for key, mod in self.module_data.modified_data.items():
            if mod['type'] == 'cold':
                lines.append(f"❄️ COLD - ChipID {mod['chipID']}: {mod['param']} = {mod['value']}")
            else:
                lines.append(f"🔥 WARM - ChipID {mod['chipID']}: {mod['param']} = {mod['value']}")
        
        lines.append(f"\nTotal: {cold_cnt} cold + {warm_cnt} warm = {len(self.module_data.modified_data)} modifications")
        
        return "\n".join(lines)
    
    def count_modifications(self):
        cold_cnt = sum(1 for mod in self.module_data.modified_data.values() if mod['type'] == 'cold')
        warm_cnt = sum(1 for mod in self.module_data.modified_data.values() if mod['type'] == 'warm')
        return cold_cnt, warm_cnt

    def go_to_summary(self):
        summary_text = SummaryBuilder.build_summary(self.module_data)
        self.summary_text.setText(summary_text)
        self.stacked_widget.setCurrentWidget(self.page3)
    
    def finish_and_reset(self):
        reply = QMessageBox.question(
            self, "Finish",
            "Return to start screen?\n\nAll unsaved changes will be lost.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.reset_application()
    
    def reset_application(self):
        self.module_data.clear()
        
        self.edit_line_path.clear()
        self.info_text.setText(
            "ℹ️ Waiting for module data...\n\n"
            "This system will load:\n"
            "• Cold configuration files\n"
            "• Warm configuration files\n"
            "• Port and RX channel information"
        )
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