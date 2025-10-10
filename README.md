# 🧩 ATLAS Module Configuration GUI

**ATLAS Module Configuration GUI** is a **Python/PyQt5 application** designed to manage, visualize, and edit configuration parameters of ATLAS detector modules.  
It supports both *cold* and *warm* module configurations, allowing users to safely modify parameters and export updated files while preserving the original directory structure.

---

## 🚀 Features

- **Module Loading:** Load module data by entering a serial number or browsing folders. Automatically reads JSON configuration files for cold and warm modules.  
- **Interactive Table:** Displays chip-level parameters in a color-coded table for easy distinction between cold (blue) and warm (orange) modules.  
- **Parameter Editing:** Edit parameters directly in the GUI with type validation (integer, float, or list) and immediate feedback.  
- **Filtering & Sorting:** Filter by cold/warm modules and sort parameters for efficient navigation.  
- **Summary & Export:** Generate a detailed summary of module configurations and save all modifications to a new folder.  
- **Safe Export:** Original files are preserved; only modified parameters are overwritten in a copy of the folder.

---

## ⚙️ Installation

Clone the repository and install dependencies:

1) **Clone** the repository
```bash
git clone https://github.com/your-username/atlas-module-gui.git
```
2) **Navigate** into the project folder
```bash
cd atlas-module-gui
```

3) **Install** dependencies
```bash
pip install PyQt5
```
# Usage

1)**Run the application**:
```bash
python main.py
```
2)**Load a module**: Enter the serial number or browse to the module folder.

3)**Modify parameters**: Navigate to the parameter table, select a parameter, and edit its value with type guidance.

4)**Save changes**: Click “Save All Changes” to export modifications to a new folder.

5)**View summary**: Use the summary page to review all loaded and modified data before finishing.

# File Structure
```plaintext
atlas-module-gui/
│
├── main.py  
├── README.md 
└── LICENSE
```
# Technologies Used
-**PyQt5** for GUI

-**JSON** for configuration data

-**os, shutil** for file and folder management
# LICENSE
This project is licensed under the [MIT License](LICENSE).





