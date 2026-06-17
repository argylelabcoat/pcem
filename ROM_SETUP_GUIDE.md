# PCem ROM Setup Tool - User Guide

## Overview

`rom_setup.py` is a menu-driven Python script that helps you organize and copy ROM files for PCem emulator systems and expansion cards. It parses the `README.md` file to understand which ROM files each system and card requires, then helps you select what you need and copy the files from a source directory.

## Prerequisites

- Python 3.6+
- Properly organized ROM directory (`../../PCem-ROMs` relative to the script location)
- The ROM files must be in the same directory structure as listed in the README

## Directory Structure

The script expects the following structure:

```
pcem/
├── rom_setup.py
├── roms/                    (destination - created automatically)
└── ../
    └── PCem-ROMs/           (source ROM files)
        ├── ibmpc/
        ├── ibmxt/
        ├── tandy/
        └── ... (other ROM directories)
```

## Usage

### Basic Usage

1. **Navigate to the PCem directory:**
   ```bash
   cd /path/to/pcem
   ```

2. **Run the script:**
   ```bash
   python3 rom_setup.py
   ```

### Menu Options

The main menu provides the following options:

1. **Select Systems (CPU-based)** - Choose systems organized by CPU type:
   - 8088 based systems
   - 8086 based systems
   - 286 based systems
   - 386 based systems
   - 486 based systems
   - Pentium based systems
   - Super Socket 7 based systems
   - Socket 8 and Slot 1 based systems

2. **Select Graphics Cards** - Choose graphics cards by type:
   - Basic cards (MDA, CGA, Hercules, etc.)
   - Unaccelerated SVGA cards
   - 2D Accelerated SVGA cards
   - 3D Accelerated SVGA cards
   - 3D only cards

3. **Select Sound Cards** - Choose audio devices:
   - PC speaker
   - Sound Blaster variants
   - AdLib
   - Gravis Ultrasound
   - And others

4. **Select HDD Controllers** - Choose storage controllers:
   - MFM controllers
   - ESDI controllers
   - IDE controllers
   - SCSI controllers

5. **Select Misc Cards** - Choose miscellaneous hardware

6. **Review Selection** - View all selected ROM files and their status
   - ✓ = ROM file exists in source directory
   - ⚠ = ROM file not found (will be skipped)

7. **Copy Selected ROMs** - Copy all selected ROM files to the destination directory

8. **Clear Selection** - Remove all selections and start over

9. **Exit** - Quit the program

### Workflow Example

1. Start the script
2. Select **Option 1** to choose systems
3. Choose **8088 based** systems
4. Select **IBM PC** and **IBM XT** (you'll be prompted to enter numbers)
5. Back to main menu, select **Option 2** for graphics cards
6. Choose **Basic cards** and select relevant cards
7. Select **Option 6** to review your selections
8. Select **Option 7** to copy the ROMs
9. The script will copy all selected files to `roms/` subdirectory

## ROM File Checking

Before copying, the script checks if each ROM file exists in the source directory. During review:
- **✓** indicates the ROM file was found and will be copied
- **⚠** indicates the ROM file was not found and will be skipped

## Output

ROM files are organized in the destination directory maintaining their subdirectory structure:

```
roms/
├── ibmpc/
│   ├── pc102782.bin
│   ├── basicc11.f6
│   └── ...
├── ibmxt/
│   ├── 5000027.u19
│   └── ...
└── ...
```

## Troubleshooting

### "ROM source directory not found"

This warning appears if the script can't find `../../PCem-ROMs`. Ensure:
- The ROM files directory exists at the correct path
- The directory is named exactly `PCem-ROMs`
- You're running the script from the correct location

### "ROM file not found" during copy

This means the ROM file is listed in README but not found in the source directory. This is common for:
- Files you haven't acquired yet
- Files with incorrect naming/organization in the source directory

Check the README for the exact expected file path.

### Permission Denied

Make sure the script is executable:
```bash
chmod +x rom_setup.py
```

And that you have write permissions to the `roms/` directory.

## Tips

- You can select multiple items by entering comma-separated numbers (e.g., `1,3,5`)
- The script automatically creates subdirectories needed in the destination
- You can run the script multiple times to add more ROMs
- Existing ROM files won't be overwritten; copying will skip them if they exist

## Notes

- ROM files must be organized in the source directory exactly as specified in the README
- The script only copies; it doesn't delete or modify existing files
- File permissions are preserved during copying

## Command-Line Usage Tips

To save the session log:
```bash
python3 rom_setup.py | tee rom_setup.log
```

To run in non-interactive mode (future enhancement), you could pipe selections:
```bash
echo -e "1\n1\n1\n7\n0" | python3 rom_setup.py
```
