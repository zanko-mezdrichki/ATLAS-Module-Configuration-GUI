# 🧩 ATLAS Module Configuration GUI

**ATLAS Module Configuration GUI** is a **Python/PyQt5 application** designed to manage, visualize, and edit configuration parameters of ATLAS detector modules.  
It supports both *cold* and *warm* module configurations, allowing users to safely modify parameters and export updated files.

Project carried out with a university classmate and supervised by Professor Carla Sbarra. 

---

## 🚀 Features

- **Module Loading:** Load module data by entering a serial number or browsing folders. Automatically reads JSON configuration files for cold and warm modules.  
- **Interactive Table:** Displays different parameters in a color-coded table.  
- **Parameter Editing:** Edit parameters directly in the GUI.  
- **Filtering & Sorting:** Filter by cold/warm modules and sort parameters for efficient navigation.  
- **Summary & Export:** Generate a detailed summary of the activities that have been done (edits, saves).  
- **Safe Export:** Original files are preserved; only modified parameters are overwritten in a copy of the folder.

---

## ⚙️ Installation

1) **Clone** the repository
```bash
git clone https://github.com/Zazza2003/ATLAS-Module-Configuration-GUI/
```
2) **Navigate** into the project folder
```bash
cd ATLAS-Module-Configuration-GUI
```

3) **Install** dependencies
```bash
pip install PyQt5
```
## 🕹️ Usage

1)**Run the application**:
```bash
python gui_atlas.py
```
2)**Load a module**: Enter the serial number or browse to the module folder. 2 examples are provided. 

3)**Modify parameters**: Navigate to the parameter table, select a parameter, and edit its value with type guidance.

4)**Save changes**: Click “Save All Changes” to export modifications to a new folder.

5)**View summary**: Use the summary page to review all loaded and modified data before finishing.

## 🤖 Technologies Used
-**Python 3.8.10**

-**PyQt5** for GUI

-**JSON** for configuration data

-**os, shutil** for file and folder management
# LICENSE
This project is licensed under the [MIT License](LICENSE).





