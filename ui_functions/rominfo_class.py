from core_files.ImageEditor import *
from core_files.IniHandler import *
from PyQt5 import QtWidgets


class RomInfo:
    name = ""
    palette_table_address = 0x0
    original_ow_table_pointer = 0x0
    original_ow_pointers_address = 0x0
    ow_table_pointer = 0x0
    palette_table_pointer_address = []
    original_num_of_ows = 0x0
    original_num_of_palettes = 0x0
    original_palette_table_address = 0x0
    ow_fix_address = 0x0
    free_space = 0x0
    path = ''
    rom_base = ''
    rom_successfully_loaded = 0

    Profiler = ProfileManager("")

    def __init__(self):

        self.set_name()

        if check_if_name_exists(self.name) == 1:
            self.rom_successfully_loaded = 1

            self.set_info(get_name_line_index(self.name))
            self.Profiler = ProfileManager(self.name)

            # Initialize the OW Table Info
            change_core_info(self.ow_table_pointer, self.original_ow_table_pointer,
                             self.original_num_of_ows, self.original_ow_pointers_address, self.free_space, self.path)

            # Initialize the palette table info
            change_image_editor_info(self.palette_table_pointer_address, self.original_num_of_palettes,
                                     self.original_palette_table_address, self.free_space)

            self.ow_fix()

    def set_name(self):
        name_raw = get_word(0xAC)
        rom_name = capitalized_hex(name_raw)[2:]  # Removes the 0x
        self.name = hex_to_text(rom_name)

        # Checks if Rom uses JPAN's Engine
        if pointer_to_address(0x160EE0) == 0x1A2000:
            self.name = "JPAN"


    def set_info(self, start_pos):
        self.ow_table_pointer = get_line_offset(start_pos + 2)
        self.original_ow_table_pointer = get_line_offset(start_pos + 3)
        self.original_ow_pointers_address = get_line_offset(start_pos + 4)
        self.original_num_of_ows = get_line_offset(start_pos + 5, 1)

        self.palette_table_pointer_address = get_palette_pointers(start_pos + 7)
        self.palette_table_address = pointer_to_address(self.palette_table_pointer_address[0])
        self.original_palette_table_address = get_line_offset(start_pos + 8)
        self.original_num_of_palettes = get_line_offset(start_pos + 9, 1)

        self.ow_fix_address = get_line_offset(start_pos + 11)

        self.free_space = get_line_offset(start_pos + 13)
        self.rom_base = get_line_string(start_pos + 14).split(" = ")[1]

        self.path = 'Files/' + self.name + "/"

    def ow_fix(self):
        # Makes sure more OWs can be added
        if self.ow_fix_address != 0:
            rom.seek(self.ow_fix_address)
            rom.write_byte(0xff)

    def load_profile_data(self, profile):
        self.set_info(get_name_line_index(profile))
        self.Profiler = ProfileManager(self.name)

        # Initialize the OW Table Info
        change_core_info(self.ow_table_pointer, self.original_ow_table_pointer,
                         self.original_num_of_ows, self.original_ow_pointers_address, self.free_space, self.path)

        # Initialize the palette table info
        change_image_editor_info(self.palette_table_pointer_address, self.original_num_of_palettes,
                                 self.original_palette_table_address, self.free_space)
