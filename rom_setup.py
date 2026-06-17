#!/usr/bin/env python3
"""
PCem ROM Setup Tool - Menu-driven ROM organizer for PCem systems and expansion cards
Parses README.md to extract ROM requirements and copies files from source ROM directory
"""

import os
import shutil
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class PCemROMOrganizer:
    def __init__(self, rom_source: Path, rom_dest: Optional[Path] = None):
        self.script_dir = Path(__file__).parent
        self.readme_path = self.script_dir / "README.md"
        self.rom_source = Path(rom_source).expanduser().resolve()
        self.rom_dest = Path(rom_dest).expanduser().resolve() if rom_dest else self.script_dir / "roms"

        self.systems = {}  # cpu_type -> [(name, roms), ...]
        self.graphics_cards = {}  # card_type -> [(name, roms), ...]
        self.sound_cards = []  # [(name, roms), ...]
        self.hdd_controllers = []  # [(name, roms), ...]
        self.misc_cards = []  # [(name, roms), ...]

    def parse_readme(self):
        """Parse README.md to extract all systems and cards with their ROM requirements"""
        if not self.readme_path.exists():
            print(f"Error: README.md not found at {self.readme_path}")
            return False

        with open(self.readme_path, 'r') as f:
            content = f.read()

        # Parse Systems sections
        self._parse_systems_section(content)

        # Parse Graphics Cards sections
        self._parse_graphics_section(content)

        # Parse Sound Cards
        self._parse_sound_section(content)

        # Parse HDD Controllers
        self._parse_hdd_section(content)

        # Parse Misc Cards
        self._parse_misc_section(content)

        return True

    def _parse_systems_section(self, content):
        """Extract system definitions from README"""
        # Find all system CPU sections
        cpu_types = ['8088 based', '8086 based', '286 based', '386 based', '486 based',
                     'Pentium based', 'Super Socket 7 based', 'Socket 8 based', 'Slot 1 based']

        for cpu_type in cpu_types:
            section_pattern = f"### {cpu_type}.*?(?=###|## Graphics|$)"
            match = re.search(section_pattern, content, re.DOTALL)
            if match:
                self.systems[cpu_type] = self._extract_rom_entries(match.group())

    def _parse_graphics_section(self, content):
        """Extract graphics card definitions from README"""
        card_types = ['Basic cards', 'Unaccelerated (S)VGA cards', '2D Accelerated SVGA cards',
                      '3D Accelerated SVGA cards', '3D only cards']

        for card_type in card_types:
            section_pattern = f"### {re.escape(card_type)}.*?(?=###|## Sound|$)"
            match = re.search(section_pattern, content, re.DOTALL)
            if match:
                self.graphics_cards[card_type] = self._extract_rom_entries(match.group())

    def _parse_sound_section(self, content):
        """Extract sound card definitions from README"""
        section_pattern = r"## Sound Cards.*?(?=## HDD|$)"
        match = re.search(section_pattern, content, re.DOTALL)
        if match:
            self.sound_cards = self._extract_rom_entries(match.group())

    def _parse_hdd_section(self, content):
        """Extract HDD controller definitions from README"""
        section_pattern = r"## HDD Controller Cards.*?(?=## Misc|$)"
        match = re.search(section_pattern, content, re.DOTALL)
        if match:
            self.hdd_controllers = self._extract_rom_entries(match.group())

    def _parse_misc_section(self, content):
        """Extract misc card definitions from README"""
        section_pattern = r"## Misc Cards.*?(?=#### Additional|$)"
        match = re.search(section_pattern, content, re.DOTALL)
        if match:
            self.misc_cards = self._extract_rom_entries(match.group())

    def _extract_rom_entries(self, section_text: str) -> List[Tuple[str, List[str]]]:
        """Extract individual ROM entries from a markdown table section"""
        entries = []
        lines = section_text.split('\n')

        # Find the table header and data rows
        table_start = None
        for i, line in enumerate(lines):
            if '|' in line and 'ROM' in line:  # Header line
                table_start = i
                break

        if table_start is None:
            return entries

        # Parse table rows
        for i in range(table_start + 2, len(lines)):  # Skip header and separator
            line = lines[i].strip()

            # Stop at next section
            if line.startswith('###') or line.startswith('##') or not line.startswith('|'):
                break

            # Parse table row
            cells = [cell.strip() for cell in line.split('|')]
            cells = [cell for cell in cells if cell]  # Remove empty cells

            if len(cells) >= 2:
                # Usually: Year | Name/Description | ROM files
                # For some: Int. | Hardware | Notes | ROM files
                name_cell = None
                roms_cell = None

                # Find cells that look like names (contain HTML bold tags or device names)
                for j, cell in enumerate(cells):
                    if '<b>' in cell or (j > 0 and ('/' in cells[-1] or '.bin' in cells[-1])):
                        name_cell = j
                        roms_cell = len(cells) - 1
                        break

                if name_cell is not None and roms_cell is not None:
                    name_text = cells[name_cell]
                    roms_text = cells[roms_cell]

                    name = self._clean_name(name_text)
                    roms = self._extract_rom_files(roms_text)

                    if name and roms:
                        entries.append((name, roms))

        return entries

    def _extract_rom_files(self, text: str) -> List[str]:
        """Extract ROM file paths from text"""
        if not text:
            return []

        # Handle HTML breaks and special characters
        text = text.replace('<br/>', '\n')
        text = text.replace('&nbsp;', ' ')

        files = []

        # Pattern: path/to/file or path/to/file.ext
        # This pattern captures directory paths with filenames
        patterns = [
            r'([a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\. ]+)',  # paths with slashes
            r'([a-zA-Z0-9_\-]+\.[a-zA-Z0-9]{3})',  # files with extensions
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                file_path = match.group(1).strip()
                # Filter out false matches
                if file_path and file_path not in files:
                    if any(x in file_path for x in ['.', '/']):
                        # Additional cleanup
                        if not any(skip in file_path for skip in ['(', ')', '<', '>', 'or', 'and']):
                            files.append(file_path)

        # Split on newlines and clean up
        final_files = []
        for f in files:
            for line in f.split('\n'):
                line = line.strip()
                if line and '/' in line:
                    final_files.append(line)

        return list(dict.fromkeys(final_files))  # Remove duplicates while preserving order

    def _clean_name(self, text: str) -> str:
        """Clean up system/card name from table cell"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove special characters and extra whitespace
        text = text.strip()
        # Remove common annotations
        text = re.sub(r'\[\d+\]', '', text)
        return text

    def show_menu(self) -> bool:
        """Show main menu and handle user input"""
        while True:
            print("\n" + "="*60)
            print("PCem ROM Setup Tool")
            print("="*60)
            print(f"ROMs selected: {len(set(self.selected_roms))}")
            print("-"*60)
            print("1. Select Systems (CPU-based)")
            print("2. Select Graphics Cards")
            print("3. Select Sound Cards")
            print("4. Select HDD Controllers")
            print("5. Select Misc Cards")
            print("6. Review Selection")
            print("7. Copy Selected ROMs")
            print("8. Clear Selection")
            print("0. Exit")
            print("\nChoice: ", end='')

            choice = input().strip()

            if choice == '1':
                self.select_systems()
            elif choice == '2':
                self.select_graphics()
            elif choice == '3':
                self.select_sound()
            elif choice == '4':
                self.select_hdd()
            elif choice == '5':
                self.select_misc()
            elif choice == '6':
                self.review_selection()
            elif choice == '7':
                return True
            elif choice == '8':
                self.selected_roms = []
                print("Selection cleared")
            elif choice == '0':
                return False
            else:
                print("Invalid choice. Try again.")

    def select_systems(self):
        """Menu to select systems by CPU type"""
        if not self.systems:
            print("No systems found in README")
            return

        while True:
            print("\n" + "-"*60)
            print("Select CPU Type:")
            print("-"*60)

            cpu_types = list(self.systems.keys())
            for i, cpu_type in enumerate(cpu_types, 1):
                count = len(self.systems[cpu_type])
                print(f"{i}. {cpu_type} ({count} systems)")
            print("0. Back to main menu")
            print("\nChoice: ", end='')

            choice = input().strip()
            if choice == '0':
                break

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(cpu_types):
                    self.select_from_list(self.systems[cpu_types[idx]], cpu_types[idx])
                else:
                    print("Invalid choice")
            except ValueError:
                print("Invalid input")

    def select_graphics(self):
        """Menu to select graphics cards by type"""
        if not self.graphics_cards:
            print("No graphics cards found in README")
            return

        while True:
            print("\n" + "-"*60)
            print("Select Graphics Card Type:")
            print("-"*60)

            card_types = list(self.graphics_cards.keys())
            for i, card_type in enumerate(card_types, 1):
                count = len(self.graphics_cards[card_type])
                print(f"{i}. {card_type} ({count} cards)")
            print("0. Back to main menu")
            print("\nChoice: ", end='')

            choice = input().strip()
            if choice == '0':
                break

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(card_types):
                    self.select_from_list(self.graphics_cards[card_types[idx]], card_types[idx])
                else:
                    print("Invalid choice")
            except ValueError:
                print("Invalid input")

    def select_sound(self):
        """Menu to select sound cards"""
        if not self.sound_cards:
            print("No sound cards found in README")
            return

        self.select_from_list(self.sound_cards, "Sound Cards")

    def select_hdd(self):
        """Menu to select HDD controllers"""
        if not self.hdd_controllers:
            print("No HDD controllers found in README")
            return

        self.select_from_list(self.hdd_controllers, "HDD Controllers")

    def select_misc(self):
        """Menu to select misc cards"""
        if not self.misc_cards:
            print("No misc cards found in README")
            return

        self.select_from_list(self.misc_cards, "Misc Cards")

    def select_from_list(self, items: List[Tuple[str, List[str]]], category: str):
        """Generic selection menu for any category"""
        if not items:
            print(f"No items in {category}")
            return

        print(f"\n{'-'*60}")
        print(f"Select {category}:")
        print(f"{'-'*60}")

        for i, (name, roms) in enumerate(items, 1):
            print(f"{i}. {name}")
        print("0. Back")
        print("\nChoice (multiple choices allowed, comma-separated): ", end='')

        choice = input().strip()
        if choice == '0':
            return

        try:
            choices = [int(c.strip())-1 for c in choice.split(',')]
            for idx in choices:
                if 0 <= idx < len(items):
                    name, roms = items[idx]
                    self.selected_roms.extend(roms)
                    print(f"✓ Added {name}")
                else:
                    print(f"Invalid choice: {idx+1}")
        except ValueError:
            print("Invalid input format")

    def review_selection(self):
        """Display all selected ROMs"""
        if not self.selected_roms:
            print("\nNo ROMs selected yet")
            return

        unique_roms = sorted(set(self.selected_roms))
        print(f"\n{'='*60}")
        print(f"Selected ROMs ({len(unique_roms)} files)")
        print(f"{'='*60}")

        for rom in unique_roms:
            src = self.rom_source / rom
            status = "✓" if src.exists() else "⚠"
            print(f"{status} {rom}")

        print(f"{'='*60}\n")

    def copy_roms(self) -> bool:
        """Copy selected ROMs from source to destination"""
        if not hasattr(self, 'selected_roms') or not self.selected_roms:
            print("No ROMs selected")
            return False

        print(f"\n{'='*60}")
        print(f"Copying {len(set(self.selected_roms))} ROM files...")
        print(f"{'='*60}")

        # Create destination directory if it doesn't exist
        self.rom_dest.mkdir(exist_ok=True)

        copied = 0
        missing = 0

        for rom_file in set(self.selected_roms):
            src = self.rom_source / rom_file
            dst = self.rom_dest / rom_file

            # Create destination subdirectory
            dst.parent.mkdir(parents=True, exist_ok=True)

            if src.exists():
                try:
                    shutil.copy2(src, dst)
                    print(f"✓ {rom_file}")
                    copied += 1
                except Exception as e:
                    print(f"✗ {rom_file} - Error: {e}")
                    missing += 1
            else:
                print(f"⚠ {rom_file} - Not found in {self.rom_source}")
                missing += 1

        print(f"\n{'='*60}")
        print(f"Summary: {copied} copied, {missing} missing")
        print(f"ROMs installed to: {self.rom_dest}")
        print(f"{'='*60}\n")

        return True

    def run(self):
        """Main entry point"""
        print("="*60)
        print("PCem ROM Setup Tool")
        print("="*60)
        print(f"\nROM Source:      {self.rom_source}")
        print(f"ROM Destination: {self.rom_dest}")
        print("="*60)

        print("\nInitializing ROM organizer...")

        # Verify ROM source directory exists
        if not self.rom_source.exists():
            print(f"\n❌ Error: ROM source directory not found: {self.rom_source}")
            print("Make sure the path exists and is correct.")
            return

        if not self.rom_source.is_dir():
            print(f"\n❌ Error: ROM source is not a directory: {self.rom_source}")
            return

        # Parse README
        if not self.parse_readme():
            return

        print(f"Found {sum(len(v) for v in self.systems.values())} systems")
        print(f"Found {sum(len(v) for v in self.graphics_cards.values())} graphics cards")
        print(f"Found {len(self.sound_cards)} sound cards")
        print(f"Found {len(self.hdd_controllers)} HDD controllers")
        print(f"Found {len(self.misc_cards)} misc cards\n")

        # Initialize selected ROMs
        self.selected_roms = []

        # Show main menu
        if self.show_menu():
            self.copy_roms()


def main():
    parser = argparse.ArgumentParser(
        description='PCem ROM Setup Tool - Menu-driven ROM organizer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 rom_setup.py /path/to/PCem-ROMs
  python3 rom_setup.py ~/Downloads/PCem-ROMs -d ~/pcem/roms
  python3 rom_setup.py ../../PCem-ROMs
        """
    )

    parser.add_argument(
        'rom_source',
        help='Path to source ROM directory (e.g., ../../PCem-ROMs or ~/Downloads/PCem-ROMs)'
    )

    parser.add_argument(
        '-d', '--destination',
        help='Path to destination ROM directory (default: ./roms in script directory)',
        default=None
    )

    args = parser.parse_args()

    # Create organizer with provided paths
    organizer = PCemROMOrganizer(args.rom_source, args.destination)
    organizer.run()


if __name__ == "__main__":
    main()
