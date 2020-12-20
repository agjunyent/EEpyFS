# pylint: disable=line-too-long

import base64
import copy
import os
from ast import literal_eval
from glob import glob
from pathlib import Path

import yaml
import cv2
import PySimpleGUI as sg

from ship import Ship
from gui_user_profile import GUIUserProfile
from user_profile import UserProfile

MAX_HIGH_SLOTS = 8
MAX_MID_SLOTS = 5
MAX_DRONE_SLOTS = 5
MAX_LOW_SLOTS = 8
MAX_RIG_SLOTS = 3

COLORS = {}
COLORS["story"] = [38, 91, 54]
COLORS["pirate"] = [93, 236, 178]
COLORS["deadspace"] = [200, 70, 0]

sg.user_settings_filename("settings/settings.json")

class GUI():
    def __init__(self, ships_data, high_slots_data, mid_slots_data, drone_slots_data, low_slots_data, combat_rigs_data, engineer_rigs_data):
        profile_name = sg.user_settings()["last_loaded_profile"]
        self.profile_data = UserProfile()
        self.profile_data.load(profile_name)

        self.ships_data = copy.deepcopy(ships_data)
        self.ship_factions = []
        self.ship_types = {} #["Frigates", "Destroyers", "Cruisers", "Battlecruisers", "Battleships"]
        self.ship_names = {}
        for ship_faction in ships_data:
            self.ship_factions.append(ship_faction)
            self.ship_types[ship_faction] = []
            self.ship_names[ship_faction] = {}
            for ship_type in ships_data[ship_faction]:
                self.ship_types[ship_faction].append(ship_type)
                self.ship_names[ship_faction][ship_type] = []
                for ship_name in ships_data[ship_faction][ship_type]:
                    self.ship_names[ship_faction][ship_type].append(ship_name)

        self.current_ship_faction = None
        self.current_ship_type = None

        self.high_slots_data = high_slots_data
        self.mid_slots_data = mid_slots_data
        self.drone_slots_data = drone_slots_data
        self.low_slots_data = low_slots_data
        self.combat_rigs_data = combat_rigs_data
        self.engineer_rigs_data = engineer_rigs_data

        self.menu_def = [['&File', ['E&xit']],
                         ['F&itting', ['&New::fitting', '!&Save::fitting']],
                         ['&Profile', ['&New::profile', '---', '&Edit::profile', '!&Save::profile', '&Load::profile']],
                         ]

        high_slots_layout = [self.make_slot("slot-high-" + str(x), image_filename="icons/high-slot.png") for x in range(MAX_HIGH_SLOTS)]
        mid_slots_layout = [[self.make_slot("slot-mid-" + str(x), image_filename="icons/mid-slot.png")] for x in range(MAX_MID_SLOTS)]
        drone_slots_layout = [[self.make_slot("slot-drone-" + str(x), image_filename="icons/drone-slot.png")] for x in range(MAX_DRONE_SLOTS)]
        low_slots_layout = [self.make_slot("slot-low-" + str(x), image_filename="icons/low-slot.png") for x in range(MAX_LOW_SLOTS)]

        combat_rigs_layout = [[self.make_slot("slot-combat-" + str(x), image_filename="icons/combat-slot.png")] for x in range(MAX_RIG_SLOTS)]
        engineer_rigs_layout = [[self.make_slot("slot-engineer-" + str(x), image_filename="icons/engineer-slot.png")] for x in range(MAX_RIG_SLOTS)]

        turrets_damage_layout = [[sg.Text("")], [sg.Text("Turrets: ")], [sg.Text("0 dps", key="turrets-dps", size=(14, 1))]]
        missiles_damage_layout = [[sg.Text("")], [sg.Text("Missiles: ")], [sg.Text("0 dps", key="launchers-dps", size=(14, 1))]]
        drones_damage_layout = [[sg.Text("0 Km", key="drones-range", size=(14, 1))], [sg.Text("Drones: ")], [sg.Text("0 dps", key="drones-dps", size=(14, 1))]]

        damage_layout = [sg.Frame('', [
            [sg.Text("Damage: ")] + [sg.Text("0 dps", key="dps", size=(14, 1))],
            [sg.Frame('', [[sg.Col(turrets_damage_layout)], [sg.Sizer(160, 1)]])] +
            [sg.Frame('', [[sg.Col(missiles_damage_layout)], [sg.Sizer(160, 1)]])] +
            [sg.Frame('', [[sg.Col(drones_damage_layout)], [sg.Sizer(160, 1)]])],
        ])]

        shield_layout = self.make_defense("shield")
        armor_layout = self.make_defense("armor")
        hull_layout = self.make_defense("hull")

        defense_layout = [sg.Frame('', [
            [sg.Text("Defense:", size=(9, 1))] + [sg.Text("", key="defense-VAL", size=(10, 1))],
            [sg.Frame('', [[sg.Col(shield_layout)], [sg.Sizer(160, 1)]])] +
            [sg.Frame('', [[sg.Col(armor_layout)], [sg.Sizer(160, 1)]])] +
            [sg.Frame('', [[sg.Col(hull_layout)], [sg.Sizer(160, 1)]])],
        ])]

        capacitor_layout = [sg.Frame('', [
            [sg.Text("Capacitor Capacity:", size=(24, 1))] + [sg.Text("0 GJ", key="capacitor-VAL", size=(10, 1), justification="r")],
            [sg.Text("Capacitor Recharge Time:", size=(24, 1))] + [sg.Text("0 s", key="capacitor-recharge-VAL", size=(10, 1), justification="r")],
            [sg.Text("Capacitor Recharge Rate:", size=(24, 1))] + [sg.Text("0 GJ/s", key="capacitor-rate-VAL", size=(10, 1), justification="r")],
        ])]

        powergrid_layout = [sg.Frame('', [
            [sg.Text("Powergrid:", size=(18, 1))] + [sg.Text("0 MW", key="powergrid-VAL", size=(16, 1), justification="r")],
            [sg.ProgressBar(100, orientation='h', size=(25, 5), key="powergrid-PROG", bar_color=("orange", "grey"))]
        ])]

        navigation_layout = [sg.Frame('', [
            [sg.Text("Flight velocity:", size=(20, 1))] + [sg.Text("0 m/s", key="navigation-flight-velocity", size=(14, 1), justification="r")],
            [sg.Text("Mass:", size=(20, 1))] + [sg.Text("0 Kg", key="navigation-mass", size=(14, 1), justification="r")],
            [sg.Text("Inertia modifier:", size=(20, 1))] + [sg.Text("0", key="navigation-inertia-modifier", size=(14, 1), justification="r")],
            [sg.Text("Warp speed:", size=(20, 1))] + [sg.Text("0 AU/s", key="navigation-warp-speed", size=(14, 1), justification="r")],
        ])]

        treedata = sg.TreeData()
        treedata_items_layout = [sg.Tree(data=treedata,
                                   headings=[''],
                                   visible_column_map=[''],
                                   auto_size_columns=True,
                                   row_height=26,
                                   num_rows=30,
                                   col0_width=30,
                                   key='tree',
                                   change_submits=False,
                                   show_expanded=False,
                                   enable_events=True)]

        treedata_ships = self.make_ship_treedata(self.ship_names)
        treedata_fittings_layout = [sg.Tree(data=treedata_ships,
                                            headings=[''],
                                            visible_column_map=[''],
                                            auto_size_columns=True,
                                            row_height=26,
                                            num_rows=30,
                                            col0_width=30,
                                            key='tree-fittings',
                                            change_submits=False,
                                            show_expanded=False,
                                            enable_events=True)]

        treedata_tabs = [[sg.Tab('Fittings', [treedata_fittings_layout], key="tab-fittings"),
                          sg.Tab('Items', [treedata_items_layout], key="tab-items")]]

        layout = [[sg.Menu(self.menu_def, key="menu")],
                  [sg.TabGroup(treedata_tabs, enable_events=True, key="tabs")] +
                  [sg.Frame('', [
                      high_slots_layout,
                      [
                          sg.Col(combat_rigs_layout + [[sg.HorizontalSeparator()]] + engineer_rigs_layout),
                          self.make_ship("ships/blank.png"),
                          sg.Col(mid_slots_layout + [[sg.HorizontalSeparator()]] + drone_slots_layout, pad=(0, 0))
                      ],
                      low_slots_layout], key='fit', element_justification='c'),
                   sg.Frame('', [
                       damage_layout,
                       defense_layout,
                       capacitor_layout,
                       powergrid_layout,
                       navigation_layout
                   ]),
                  ],
                 ]

        self.current_fitting_name = None
        self.current_ship_data = None
        self.current_ship_name = None
        self.current_ship = None
        self.selected_slot = None
        self.tooltip = None
        self.selected_tree_row = None
        self.selected_tree_row_position = None

        self.gui_user_profile = GUIUserProfile()

        self.window = sg.Window('EEpyFS. Eve Echoes python Fitting Simulator', layout)
        self.window.Finalize()

        self.window["tree"].bind('<Double-Button-1>', '-double-click')
        self.window["tree-fittings"].bind('<Double-Button-1>', '-double-click')
        # self.window["tree"].bind('<Button-3>', '-right-click')
        self.window["tree"].Widget.bind('<Button-3>', self.onTreeRightClick)
        self.window["tree"].bind('<Leave>', '-leave')

        self.add_hover_events()

        # self.window.Maximize()

    def add_hover_events(self):
        for slot_num in range(MAX_HIGH_SLOTS):
            # self.window["slot-high-" + str(slot_num)].bind('<Enter>', '-hover-enter')
            self.window["slot-high-" + str(slot_num)].bind('<Leave>', '-hover-leave')
            self.window["slot-high-" + str(slot_num)].bind('<Button-3>', '-right')
        for slot_num in range(MAX_MID_SLOTS):
            self.window["slot-mid-" + str(slot_num)].bind('<Button-3>', '-right')
        #     self.window["slot-mid-" + str(slot_num)].bind('<Enter>', '-hover-enter')
        #     self.window["slot-mid-" + str(slot_num)].bind('<Leave>', '-hover-leave')
        for slot_num in range(MAX_LOW_SLOTS):
            self.window["slot-low-" + str(slot_num)].bind('<Button-3>', '-right')
            # self.window["slot-low-" + str(slot_num)].bind('<Enter>', '-hover-enter')
            self.window["slot-low-" + str(slot_num)].bind('<Leave>', '-hover-leave')
        for slot_num in range(MAX_DRONE_SLOTS):
            # self.window["slot-drone-" + str(slot_num)].bind('<Enter>', '-hover-enter')
            self.window["slot-drone-" + str(slot_num)].bind('<Leave>', '-hover-leave')
            self.window["slot-drone-" + str(slot_num)].bind('<Button-3>', '-right')
        for slot_num in range(MAX_RIG_SLOTS):
            self.window["slot-combat-" + str(slot_num)].bind('<Button-3>', '-right')
            self.window["slot-engineer-" + str(slot_num)].bind('<Button-3>', '-right')
        #     self.window["slot-combat-" + str(slot_num)].bind('<Enter>', '-hover-enter')
        #     self.window["slot-combat-" + str(slot_num)].bind('<Leave>', '-hover-leave')
        #     self.window["slot-engineer-" + str(slot_num)].bind('<Enter>', '-hover-enter')
        #     self.window["slot-engineer-" + str(slot_num)].bind('<Leave>', '-hover-leave')

    def enable_disable_save_fitting(self, enable=True):
        if enable:
            self.menu_def = [['&File', ['E&xit']],
                             ['F&itting', ['&New::fitting', '&Save::fitting']],
                             self.menu_def[2],
                            ]
        else:
            self.menu_def = [['&File', ['E&xit']],
                             ['F&itting', ['&New::fitting', '!&Save::fitting']],
                             self.menu_def[2],
                            ]
        self.window["menu"].Update(self.menu_def)

    def enable_disable_save_profile(self, enable=True):
        if enable:
            self.menu_def = [['&File', ['E&xit']],
                             self.menu_def[1],
                             ['&Profile', ['&New::profile', '---', '&Edit::profile', '&Save::profile', '&Load::profile']],
                            ]
        else:
            self.menu_def = [['&File', ['E&xit']],
                             self.menu_def[1],
                             ['&Profile', ['&New::profile', '---', '&Edit::profile', '!&Save::profile', '&Load::profile']],
                            ]
        self.window["menu"].Update(self.menu_def)

    def onTreeRightClick(self, event):
        row = self.window["tree"].Widget.identify_row(event.y)
        self.window["tree"].Widget.selection_set(row)
        selection = self.window["tree"].Widget.selection()
        self.selected_tree_row = self.window["tree"].Widget.item(selection)
        bbox = self.window["tree"].Widget.bbox(selection)
        pos_x = bbox[0] + bbox[2]
        pos_y = bbox[1]
        self.selected_tree_row_position = (pos_x, pos_y)

    def read(self):
        # event, values = self.window.Read()
        window, event, values = sg.read_all_windows()

        self.hide_slot_info()
        if event == "Exit" or event is None:
            exiting = sg.PopupOKCancel("Do you want to exit?", keep_on_top=True)
            if exiting == "OK":
                return False

        elif event == "tree-fittings-double-click":
            try:
                selected = values["tree-fittings"][0].split("::")
            except IndexError:
                return True
            if len(selected) >= 2:
                if selected[0] == "loadfit":
                    if selected[1] == "New*":
                        ship_name = selected[2]
                        ship_type = selected[3]
                        ship_faction = selected[4]
                        self.current_ship_data = self.ships_data[ship_faction][ship_type][ship_name]
                        self.current_ship = Ship(ship_name, self.current_ship_data, self.profile_data)
                        get_fitting_name = False
                        while not get_fitting_name:
                            self.current_fitting_name = sg.popup_get_text("Enter fitting name:", selected[2] + " fit", default_text="New " + selected[2] + " fit")
                            if not self.current_fitting_name:
                                self.current_ship = None
                                self.current_ship_data = None
                                return True
                            fitting_file = "saved_fittings/" + self.current_fitting_name + ".yaml"
                            if Path(fitting_file).is_file():
                                overwrite = sg.popup_ok_cancel("Fitting name already exists. Overwirte?")
                                if overwrite != 'OK':
                                    continue
                            with open(fitting_file, "w") as stream:
                                current_fit = self.current_ship.export_fit()
                                current_fit["fitting_name"] = self.current_fitting_name
                                yaml.safe_dump(current_fit, stream)
                                get_fitting_name = True
                        self.window.Element('tree-fittings').Update(self.make_ship_treedata(self.ship_names))
                        self.reset_ship()
                        self.update_ship()
                        self.selected_slot = None
                    else:
                        selected_item_row = self.window.Element("tree-fittings").SelectedRows[0]
                        selected = self.window.Element("tree-fittings").TreeData.tree_dict[selected_item_row]
                        self.current_fitting_name = selected.text
                        current_fit = selected.values[0]
                        self.load_fit(current_fit)
                    self.update_treedata("empty", None)
                    self.window["tab-items"].Select()
                    self.enable_disable_save_fitting(enable=True)

        elif event == "New::profile":
            new_profile = self.gui_user_profile.create_new_profile()
            if new_profile:
                self.profile_data = new_profile
        elif event == "Edit::profile":
            new_profile = self.gui_user_profile.edit_user_profile(self.profile_data)
            if new_profile:
                self.profile_data = new_profile

        elif event == "Save::fitting" and self.current_ship_data:
            current_fit = self.current_ship.export_fit()
            current_fit["fitting_name"] = self.current_fitting_name
            with open("saved_fittings/" + self.current_fitting_name + ".yaml", 'w') as stream:
                yaml.safe_dump(current_fit, stream)
            self.window.Element('tree-fittings').Update(self.make_ship_treedata(self.ship_names))

        elif "dropdown" in event:
            dropdown_type = event.split("-")[1]
            if dropdown_type == "faction":
                self.current_ship_faction = values[event]
                self.window["dropdown-type"].Update(value="", values=self.ship_types[self.current_ship_faction], disabled=False)
                self.window["dropdown-shipname"].Update(value="", values=None, disabled=True)
                self.current_ship_type = None
                self.current_ship_name = None
                self.window["Update"].Update(disabled=True)
            elif dropdown_type == "type" and self.current_ship_faction:
                self.current_ship_type = values[event]
                self.window["dropdown-shipname"].Update(value="", values=self.ship_names[self.current_ship_faction][self.current_ship_type], disabled=False)
                self.current_ship_name = None
                self.window["Update"].Update(disabled=True)
            elif dropdown_type == 'shipname':
                self.current_ship_name = values[event]
                self.current_ship_data = self.ships_data[self.current_ship_faction][self.current_ship_type][self.current_ship_name]
                self.window["Update"].Update(disabled=False)

        elif event == "tree-leave":
            if self.tooltip:
                self.tooltip.close()
                self.tooltip = None

        if self.selected_tree_row and self.selected_tree_row["values"]:
            self.selected_tree_row["text"] = values["tree"][0]
            self.show_tree_tooltip(self.selected_tree_row_position, self.selected_tree_row)
            self.selected_tree_row = None

        elif self.current_ship:
            if event == "tree-double-click" and self.selected_slot:
                if values["tree"] and len(values["tree"][0].split("_")) > 1:
                    selected_item_row = self.window.Element("tree").SelectedRows[0]
                    selected = self.window.Element("tree").TreeData.tree_dict[selected_item_row]
                    item = {}
                    item[values["tree"][0]] = copy.deepcopy(selected.values)
                    slot_added, slot_name = self.current_ship.add_slot(self.selected_slot, item)
                    if slot_added:
                        self.selected_slot = slot_name
                        if "drones" in values["tree"][0]:
                            image_filename = "-".join(values["tree"][0].split("_")[0:3])
                            image_filename += "-" + values["tree"][0].split(" ")[-1].lower()
                        else:
                            image_filename = "-".join(values["tree"][0].split("_")[0:3])
                        faction = list(item.values())[0]["faction"]
                        icon = self.get_icon(image_filename, faction=faction, size=(65, 65))
                        self.window.Element(self.selected_slot).Update(image_data=icon)
                        self.update_ship()
                    else:
                        if slot_name == "powergrid":
                            sg.PopupOK("NOT ENOUGH POWERGRID", no_titlebar=True)
                        elif slot_name == "full":
                            sg.PopupOK("ALL SLOTS FULL", no_titlebar=True)

            elif event.split("-")[0] == "slot":
                if len(event.split("-")) >= 4:
                    event_type = event.split("-")[3]
                    event_slot = "-".join(event.split("-")[0:3])
                    slot_info = self.current_ship.get_slot(event_slot)
                    if slot_info:
                        if event_type == "right":
                            menu_event = self.make_right_click_menu(event_slot)
                            if menu_event == "Unfit":
                                if self.current_ship.remove_slot(event_slot):
                                    slot_type = event_slot.split("-")[1]
                                    image_filename = slot_type + "-slot"
                                    icon = self.get_icon(image_filename, faction='none', size=(65, 65))
                                    self.window.Element(event_slot).Update(image_data=icon)
                                    self.update_ship()
                            elif menu_event == "Stats":
                                self.show_slot_info(event_slot, slot_info)
                        elif event_type == "hover":
                            hover_event = event.split("-")[4]
                            if hover_event == "leave":
                                self.hide_slot_info()
                else:
                    if self.selected_slot:
                        if event.split("-")[1] != self.selected_slot.split("-")[1]:
                            slot_type = event.split("-")[1]
                            self.update_treedata(slot_type, self.current_ship.get_max_drone_size())
                    else:
                        slot_type = event.split("-")[1]
                        self.update_treedata(slot_type, self.current_ship.get_max_drone_size())
                    self.selected_slot = event
        return True

    def reset_ship(self):
        if os.path.isfile("ships/" + self.current_ship.name + ".png"):
            self.window.Element("ship").Update(image_filename="ships/" + self.current_ship.name + ".png")
        else:
            self.window.Element("ship").Update(image_filename="ships/blank.png")
        for i in range(MAX_HIGH_SLOTS):
            self.window.Element("slot-high-" + str(i)).Update(visible=i < self.current_ship.max_slots["high"], image_filename="icons/high-slot.png")
        for i in range(MAX_MID_SLOTS):
            self.window.Element("slot-mid-" + str(i)).Update(visible=i < self.current_ship.max_slots["mid"], image_filename="icons/mid-slot.png")
        for i in range(MAX_DRONE_SLOTS):
            self.window.Element("slot-drone-" + str(i)).Update(visible=i < self.current_ship.max_slots["drone"], image_filename="icons/drone-slot.png")
        for i in range(MAX_LOW_SLOTS):
            self.window.Element("slot-low-" + str(i)).Update(visible=i < self.current_ship.max_slots["low"], image_filename="icons/low-slot.png")
        for i in range(MAX_RIG_SLOTS):
            self.window.Element("slot-combat-" + str(i)).Update(visible=i < self.current_ship.max_rigs["combat"], image_filename="icons/combat-slot.png")
            self.window.Element("slot-engineer-" + str(i)).Update(visible=i < self.current_ship.max_rigs["engineer"], image_filename="icons/engineer-slot.png")

    def update_ship(self):
        # Update DPS
        dps, total_dps, control_range = self.current_ship.get_dps()
        for key in list(dps.keys()):
            self.window.Element(key + "-dps").Update(str(dps[key]) + " dps")
        self.window.Element("dps").Update(str(total_dps) + " dps")
        self.window.Element("drones-range").Update(str(control_range) + " Km")
        # Update Powergrid
        powergrid = self.current_ship.get_powergrid()
        self.window.Element("powergrid-VAL").Update(str(powergrid["used"]) + " / " + str(powergrid["value"]) + " MW")
        self.window.Element("powergrid-PROG").update_bar(str(100 * powergrid["used"] / powergrid["value"]))
        # Update Capacitor
        capacitor = self.current_ship.get_capacitor()
        self.window.Element("capacitor-VAL").Update(str(capacitor["value"]) + " GJ")
        self.window.Element("capacitor-recharge-VAL").Update(str(capacitor["recharge"]) + " s")
        self.window.Element("capacitor-rate-VAL").Update(str(capacitor["rate"]) + " GJ/s")
        # Update Defenses
        defenses = self.current_ship.get_defenses()
        for defense_type in defenses:
            defense = defenses[defense_type]
            self.window.Element(defense_type + "-VAL").Update(defense["value"])
            for resist_type in defense["resists"]:
                resist = defense["resists"][resist_type]
                self.window.Element(resist_type + "-" + defense_type + "-VAL").Update(str(int(resist)) + "%")
                self.window.Element(resist_type + "-" + defense_type + "-PROG").update_bar(resist)
        self.window.Element("defense-VAL").Update(self.current_ship.get_ehp())
        # Update Navigation
        navigation = self.current_ship.get_navigation()
        self.window.Element("navigation-flight-velocity").Update(str(round(navigation["flight_velocity"], 2)) + " m/s")
        self.window.Element("navigation-mass").Update(str(navigation["mass"]) + " Kg")
        self.window.Element("navigation-inertia-modifier").Update(str(navigation["inertia_modifier"]))
        self.window.Element("navigation-warp-speed").Update(str(navigation["warp_speed"]) + " AU/s")

    def update_treedata(self, slot_type, max_drone_size=None):
        if slot_type == "high":
            self.window.Element("tree").Update(self.make_treedata(self.high_slots_data))
        elif slot_type == "mid":
            self.window.Element("tree").Update(self.make_treedata(self.mid_slots_data))
        elif slot_type == "drone":
            self.window.Element("tree").Update(self.make_treedata(self.drone_slots_data, is_drone=True, max_drone_size=max_drone_size))
        elif slot_type == "low":
            self.window.Element("tree").Update(self.make_treedata(self.low_slots_data))
        elif slot_type == "combat":
            self.window.Element("tree").Update(self.make_treedata(self.combat_rigs_data))
        elif slot_type == "engineer":
            self.window.Element("tree").Update(self.make_treedata(self.engineer_rigs_data))
        else:
            self.window.Element("tree").Update(sg.TreeData())

    def make_right_click_menu(self, slot_type):
        widget = self.window.Element(slot_type).Widget
        if "low" in slot_type:
            location = (widget.winfo_rootx(), widget.winfo_rooty() - 100)
        else:
            location = (widget.winfo_rootx(), widget.winfo_rooty() + 70)

        layout = [
            [sg.Button("Unfit")],
            [sg.Button("Stats")]
        ]
        window = sg.Window("test",
                            layout=[[sg.Frame('', layout)]],
                            no_titlebar=True,
                            finalize=True,
                            location=location,
                            force_toplevel=True)
        event, _ = window.read(timeout=5000)
        window.close()
        return event

    def slot_info_tooltip(self, slot_type, slot_info):
        widget = self.window.Element(slot_type).Widget
        if "low" in slot_type:
            location = (widget.winfo_rootx(), widget.winfo_rooty() - 500)
        else:
            location = (widget.winfo_rootx(), widget.winfo_rooty() + 70)

        item_name = None
        item_data = None
        for name in slot_info:
            item_name = name
            item_data = slot_info[name]
        window = self.make_tooltip(slot_type, item_name, item_data, location)

        return window

    def show_slot_info(self, slot_type, slot_info):
        if self.tooltip is None:
            self.tooltip = self.slot_info_tooltip(slot_type, slot_info)

    def hide_slot_info(self):
        if self.tooltip:
            self.tooltip.close()
        self.tooltip = None

    def tree_info_tooltip(self, item_position, item_data):
        item_name = item_data["text"]
        item_data = "{" + item_data["values"][0] + "}"
        item_data = literal_eval(item_data)
        location = (item_position[0] + 100, item_position[1] + 100)

        window = self.make_tooltip(self.selected_slot, item_name, item_data, location)

        return window

    def make_tooltip(self, slot_type, item_name, item_data, position):
        item_type, item_sub_type, item_size, *_ = item_name.split("_")
        item_name = ("-").join(item_name.split("_")[3:])
        slot_type = slot_type.split("-")[1]
        layout = []
        item_damage_percent = {}
        if slot_type in {"high", "drone"}:
            item_damage = item_data["damage"]
            total_damage = 0
            item_damage_percent = {}
            for damage_type in item_damage:
                total_damage += item_damage[damage_type]
            for damage_type in item_damage:
                item_damage_percent[damage_type] = int((item_damage[damage_type] / total_damage) * 100)

            item_dps = self.get_dps(item_data)
            if item_type == "launchers":
                layout = [
                    [sg.Text("DPS: ", size=(32, 1), justification='l')] + [sg.Text(str(item_dps), size=(10, 1), justification='r')],
                    [sg.Col([[sg.Text("EM", size=(3, 1), font=("Helvetica", 8))] + [sg.Text(str(round(item_damage["em"], 2)), size=(5, 1), justification="r", font=("Helvetica", 8))], [sg.ProgressBar(100, orientation='h', size=(6, 3), k='em', bar_color=("blue", "grey"))]])] +
                    [sg.Col([[sg.Text("THM", size=(3, 1), font=("Helvetica", 8))] + [sg.Text(str(round(item_damage["thermal"], 2)), size=(5, 1), justification="r", font=("Helvetica", 8))], [sg.ProgressBar(100, orientation='h', size=(6, 3), k='thermal', bar_color=("red", "grey"))]])] +
                    [sg.Col([[sg.Text("KIN", size=(3, 1), font=("Helvetica", 8))] + [sg.Text(str(round(item_damage["kinetic"], 2)), size=(5, 1), justification="r", font=("Helvetica", 8))], [sg.ProgressBar(100, orientation='h', size=(6, 3), k='kinetic', bar_color=("white", "grey"))]])] +
                    [sg.Col([[sg.Text("EXP", size=(3, 1), font=("Helvetica", 8))] + [sg.Text(str(round(item_damage["explosive"], 2)), size=(5, 1), justification="r", font=("Helvetica", 8))], [sg.ProgressBar(100, orientation='h', size=(6, 3), k='explosive', bar_color=("yellow", "grey"))]])],
                    [sg.Text("Tech Level: ", size=(32, 1), justification='l')] + [sg.Text(str(item_data["tech_level"]), size=(10, 1), justification='r')],
                    [sg.Text("Metalevel: ", size=(32, 1), justification='l')] + [sg.Text(str(item_data["metalevel"]), size=(10, 1), justification='r')],
                    [sg.Text("Flight Velocity: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["flight_velocity"], 2)) + "m/s", size=(10, 1), justification='r')],
                    [sg.Text("Powergrid Requirement: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["powergrid"], 2)) + "MW", size=(10, 1), justification='r')],
                    [sg.Text("Activation Time: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["activation_time"], 2)) + "s", size=(10, 1), justification='r')],
                    [sg.Text("Explosion Velocity: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["explosion_velocity"], 2)) + "m/s", size=(10, 1), justification='r')],
                    [sg.Text("Explosion Radius: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["explosion_radius"], 2)) + "m", size=(10, 1), justification='r')],
                    [sg.Text("Flight Time: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["flight_time"], 2)) + "s", size=(10, 1), justification='r')],
                    [sg.Text("Reload Time: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["reload_time"], 2)) + "s", size=(10, 1), justification='r')],
                    [sg.Text("Missile Range: ", size=(32, 1), justification='l')] + [sg.Text(str(self.get_missile_range(item_data)) + "km", size=(10, 1), justification='r')],]
            else:
                layout = [
                    [sg.Text("DPS: ", size=(32, 1), justification='l')] + [sg.Text(str(self.get_dps(item_data)), size=(10, 1), justification='r')],
                    [sg.Col([[sg.Text("EM", size=(3, 1), font=("Helvetica", 8))] + [sg.Text(str(round(item_damage["em"], 2)), size=(5, 1), justification="r", font=("Helvetica", 8))], [sg.ProgressBar(100, orientation='h', size=(6, 3), k='em', bar_color=("blue", "grey"))]])] +
                    [sg.Col([[sg.Text("THM", size=(3, 1), font=("Helvetica", 8))] + [sg.Text(str(round(item_damage["thermal"], 2)), size=(5, 1), justification="r", font=("Helvetica", 8))], [sg.ProgressBar(100, orientation='h', size=(6, 3), k='thermal', bar_color=("red", "grey"))]])] +
                    [sg.Col([[sg.Text("KIN", size=(3, 1), font=("Helvetica", 8))] + [sg.Text(str(round(item_damage["kinetic"], 2)), size=(5, 1), justification="r", font=("Helvetica", 8))], [sg.ProgressBar(100, orientation='h', size=(6, 3), k='kinetic', bar_color=("white", "grey"))]])] +
                    [sg.Col([[sg.Text("EXP", size=(3, 1), font=("Helvetica", 8))] + [sg.Text(str(round(item_damage["explosive"], 2)), size=(5, 1), justification="r", font=("Helvetica", 8))], [sg.ProgressBar(100, orientation='h', size=(6, 3), k='explosive', bar_color=("yellow", "grey"))]])],
                    [sg.Text("Tech Level: ", size=(32, 1), justification='l')] + [sg.Text(str(item_data["tech_level"]), size=(10, 1), justification='r')],
                    [sg.Text("Metalevel: ", size=(32, 1), justification='l')] + [sg.Text(str(item_data["metalevel"]), size=(10, 1), justification='r')],
                    [sg.Text("Powergrid Requirement: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["powergrid"], 2)) + "MW", size=(10, 1), justification='r')],
                    [sg.Text("Activation Time: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["activation_time"], 2)) + "s", size=(10, 1), justification='r')],
                    [sg.Text("Activation Cost: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["activation_cost"], 2)) + "GJ", size=(10, 1), justification='r')],
                    [sg.Text("Optimal Range: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["optimal_range"], 2)) + "Km", size=(10, 1), justification='r')],
                    [sg.Text("Accuracy Falloff: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["accuracy_falloff"], 2)) + "Km", size=(10, 1), justification='r')],
                    [sg.Text("Tracking Speed: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["tracking_speed"], 2)), size=(10, 1), justification='r')],]
            if slot_type == "drone":
                layout.append([sg.Text("Control Range: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["control_range"], 2)) + "Km", size=(10, 1), justification='r')])

        elif slot_type == "low":
            if item_sub_type == "hardeners":
                item_damage_percent = item_data["ship"]["defenses"][item_type]["resists"]
                layout.append([sg.Frame('',
                [
                    [sg.Text(item_type.title() + " Damage Resistance")],
                    [sg.Col([[sg.Text("EM", size=(3, 1), font=("Helvetica", 8))] + [sg.Text(str(round(item_damage_percent["em"], 2)), size=(5, 1), justification="r", font=("Helvetica", 8))], [sg.ProgressBar(100, orientation='h', size=(6, 3), k='em', bar_color=("blue", "grey"))]])] +
                    [sg.Col([[sg.Text("THM", size=(3, 1), font=("Helvetica", 8))] + [sg.Text(str(round(item_damage_percent["thermal"], 2)), size=(5, 1), justification="r", font=("Helvetica", 8))], [sg.ProgressBar(100, orientation='h', size=(6, 3), k='thermal', bar_color=("red", "grey"))]])] +
                    [sg.Col([[sg.Text("KIN", size=(3, 1), font=("Helvetica", 8))] + [sg.Text(str(round(item_damage_percent["kinetic"], 2)), size=(5, 1), justification="r", font=("Helvetica", 8))], [sg.ProgressBar(100, orientation='h', size=(6, 3), k='kinetic', bar_color=("white", "grey"))]])] +
                    [sg.Col([[sg.Text("EXP", size=(3, 1), font=("Helvetica", 8))] + [sg.Text(str(round(item_damage_percent["explosive"], 2)), size=(5, 1), justification="r", font=("Helvetica", 8))], [sg.ProgressBar(100, orientation='h', size=(6, 3), k='explosive', bar_color=("yellow", "grey"))]])],
                ])])
            elif item_sub_type == "dcus":
                for defense in ["shield", "armor", "hull"]:
                    item_damage_percent = item_data["ship"]["defenses"][defense]["resists"]
                    layout.append([sg.Frame('',
                    [
                        [sg.Text(item_type.title() + " Damage Resistance")],
                        [sg.Col([[sg.Text("EM", size=(3, 1), font=("Helvetica", 8))] + [sg.Text(str(round(item_damage_percent["em"], 2)), size=(5, 1), justification="r", font=("Helvetica", 8))], [sg.ProgressBar(100, orientation='h', size=(6, 3), k=defense + '-em', bar_color=("blue", "grey"))]])] +
                        [sg.Col([[sg.Text("THM", size=(3, 1), font=("Helvetica", 8))] + [sg.Text(str(round(item_damage_percent["thermal"], 2)), size=(5, 1), justification="r", font=("Helvetica", 8))], [sg.ProgressBar(100, orientation='h', size=(6, 3), k=defense + '-thermal', bar_color=("red", "grey"))]])] +
                        [sg.Col([[sg.Text("KIN", size=(3, 1), font=("Helvetica", 8))] + [sg.Text(str(round(item_damage_percent["kinetic"], 2)), size=(5, 1), justification="r", font=("Helvetica", 8))], [sg.ProgressBar(100, orientation='h', size=(6, 3), k=defense + '-kinetic', bar_color=("white", "grey"))]])] +
                        [sg.Col([[sg.Text("EXP", size=(3, 1), font=("Helvetica", 8))] + [sg.Text(str(round(item_damage_percent["explosive"], 2)), size=(5, 1), justification="r", font=("Helvetica", 8))], [sg.ProgressBar(100, orientation='h', size=(6, 3), k=defense + '-explosive', bar_color=("yellow", "grey"))]])],
                    ])])
            layout.append([sg.Text("Tech Level: ", size=(32, 1), justification='l')] + [sg.Text(str(item_data["tech_level"]), size=(10, 1), justification='r')])
            layout.append([sg.Text("Metalevel: ", size=(32, 1), justification='l')] + [sg.Text(str(item_data["metalevel"]), size=(10, 1), justification='r')])
            layout.append([sg.Text("Powergrid Requirement: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["powergrid"], 2)) + "MW", size=(10, 1), justification='r')])
            layout.append([sg.Text("Activation Time: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["activation_time"], 2)) + "s", size=(10, 1), justification='r')])
            if item_sub_type in {"repairers", "boosters"}:
                layout.append([sg.Text("Activation Cost: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["activation_cost"], 2)) + "GJ", size=(10, 1), justification='r')])
                layout.append([sg.Text(item_type.title() + " Amount: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["amount"], 2)), size=(10, 1), justification='r')])
            elif item_sub_type == "hardeners":
                layout.append([sg.Text("Activation Cost: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["activation_cost"], 2)) + "GJ", size=(10, 1), justification='r')])
            elif item_sub_type == "extenders":
                layout.append([sg.Text("Activation Cost: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["activation_cost"], 2)) + "GJ", size=(10, 1), justification='r')])
                layout.append([sg.Text(item_type.title() + " Bonus Amount: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["ship"]["defenses"]["shield"]["value"]["flat"], 2)), size=(10, 1), justification='r')])
                layout.append([sg.Text("Signature Radius Increase: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["ship"]["targeting"]["signature"], 2)) + " m", size=(10, 1), justification='r')])
            elif item_sub_type == "plates":
                layout.append([sg.Text("Activation Cost: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["activation_cost"], 2)) + "GJ", size=(10, 1), justification='r')])
                layout.append([sg.Text(item_type.title() + " Bonus Amount: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["ship"]["defenses"]["armor"]["value"]["flat"], 2)), size=(10, 1), justification='r')])
                layout.append([sg.Text("Mass Increase: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["ship"]["navigation"]["mass"], 2)) + " Kg", size=(10, 1), justification='r')])
            elif item_sub_type == "batteries":
                layout.append([sg.Text(item_type.title() + " Bonus Amount: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["ship"]["capacitor"]["value"]["flat"], 2)) + " GJ", size=(10, 1), justification='r')])
            elif item_sub_type == "dcus":
                layout.append([sg.Text("Activation Cost: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["activation_cost"], 2)) + "GJ", size=(10, 1), justification='r')])
            elif item_sub_type == "afterburners":
                layout.append([sg.Text("Activation Cost: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["activation_cost"], 2)) + "GJ", size=(10, 1), justification='r')])
                layout.append([sg.Text("Mass Increase: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["ship"]["navigation"]["mass"], 2)) + " Kg", size=(10, 1), justification='r')])
                layout.append([sg.Text("Flight Velocity: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["ship"]["navigation"]["flight_velocity"], 2)) + "%", size=(10, 1), justification='r')])
            elif item_sub_type == "damage upgrades":
                layout.append([sg.Text("Activation Cost: ", size=(32, 1), justification='l')] + [sg.Text(str(round(item_data["activation_cost"], 2)) + "GJ", size=(10, 1), justification='r')])


        window = sg.Window("test",
                            [[sg.Frame('', [[sg.Text(item_name)]])], [sg.Frame('', layout)]],
                            no_titlebar=True,
                            finalize=True,
                            location=position,
                            force_toplevel=True)
        if item_sub_type == "dcus":
            for defense in ["shield", "armor", "hull"]:
                item_damage_percent = item_data["ship"]["defenses"][defense]["resists"]
                for item_damage_type in item_damage_percent:
                    window[defense + "-" + item_damage_type].update_bar(item_damage_percent[item_damage_type])
        else:
            for item_damage_type in item_damage_percent:
                window[item_damage_type].update_bar(item_damage_percent[item_damage_type])
        window.read(timeout=1)
        return window

    def show_tree_tooltip(self, item_position, item_data):
        self.tooltip = self.tree_info_tooltip(item_position, item_data)

    def place(self, elem):
        '''
        Places element provided into a Column element so that its placement is retained.
        :param elem: the element to put into the layout
        :return: A column element containing the provided element
        '''
        return sg.Column([[elem]], pad=(0, 0))

    def get_dps(self, item_data):
        dps = 0
        damages = item_data["damage"]
        for damage_type in damages:
            dps += damages[damage_type]
        return round(dps / item_data["activation_time"], 2)

    def get_missile_range(self, item_data):
        flight_velocity = item_data["flight_velocity"]
        flight_time = item_data["flight_time"]
        return round(flight_velocity * flight_time / 1000.0, 2)

    def make_ship(self, image_filename):
        return self.place(sg.Button('',
                                    key="ship",
                                    button_color=sg.TRANSPARENT_BUTTON,
                                    image_filename=image_filename,
                                    image_size=(650, 650),
                                    image_subsample=1,
                                    border_width=0))

    def make_slot(self, key, image_filename="ships/blank.png"):
        return self.place(sg.Button('',
                                    key=key,
                                    button_color=sg.TRANSPARENT_BUTTON,
                                    image_filename=image_filename,
                                    image_size=(65, 65),
                                    image_subsample=1,
                                    border_width=0))

    def make_defense(self, defense_type):
        defense = [[sg.Text(defense_type.title() + ":")] + [sg.Text("", size=(7, 1), key=defense_type + "-VAL")],
                   [sg.Text("EM", size=(9, 1))] + [sg.Text("0", size=(4, 1), key="em-" + defense_type + "-VAL", justification="r")], [sg.ProgressBar(100, orientation='h', size=(10, 3), key="em-" + defense_type + "-PROG", bar_color=("blue", "grey"))],
                   [sg.Text("THM", size=(9, 1))] + [sg.Text("0", size=(4, 1), key="thermal-" + defense_type + "-VAL", justification="r")], [sg.ProgressBar(100, orientation='h', size=(10, 3), key="thermal-" + defense_type + "-PROG", bar_color=("red", "grey"))],
                   [sg.Text("KIN", size=(9, 1))] + [sg.Text("0", size=(4, 1), key="kinetic-" + defense_type + "-VAL", justification="r")], [sg.ProgressBar(100, orientation='h', size=(10, 3), key="kinetic-" + defense_type + "-PROG", bar_color=("white", "grey"))],
                   [sg.Text("EXP", size=(9, 1))] + [sg.Text("0", size=(4, 1), key="explosive-" + defense_type + "-VAL", justification="r")], [sg.ProgressBar(100, orientation='h', size=(10, 3), key="explosive-" + defense_type + "-PROG", bar_color=("yellow", "grey"))]]
        return defense

    def load_fit(self, current_fit):
        self.current_ship_faction = current_fit["ship"]["faction"]
        self.current_ship_type = current_fit["ship"]["type"]
        self.current_ship_name = current_fit["ship"]["name"]
        self.current_ship_data = self.ships_data[self.current_ship_faction][self.current_ship_type][self.current_ship_name]
        self.current_ship = Ship(current_fit["ship"]["name"], self.current_ship_data, self.profile_data)
        self.reset_ship()

        for slot_type, slot_data in zip(["high", "mid", "drone", "low", "combat", "engineer"], [self.high_slots_data, self.mid_slots_data, self.drone_slots_data, self.low_slots_data, self.combat_rigs_data, self.engineer_rigs_data]):
            slot_num = 0
            for slot in current_fit[slot_type]:
                if slot:
                    item_type, sub_item_type, item_size, item_name = slot.split("_")
                    item_data = {}
                    item_data[slot] = slot_data[item_type][sub_item_type][item_size][item_name]
                    self.current_ship.add_slot("slot-" + slot_type + "-" + str(slot_num), item_data)
                    image_filename = "-".join(slot.split("_")[0:3])
                    if slot_type == "drone":
                        image_filename += "-" + slot.split(" ")[-1].lower()
                    faction = item_data[slot]["faction"]
                    icon = self.get_icon(image_filename, faction=faction, size=(65, 65))
                    self.window.Element("slot-" + slot_type + "-" + str(slot_num)).Update(image_data=icon)
                slot_num += 1
        self.update_ship()
        self.selected_slot = None
        self.update_treedata("empty", None)

    def get_saved_fittings(self, ship_names):
        saved_fittings_fnames = glob("saved_fittings/*.yaml")
        saved_fittings = copy.deepcopy(ship_names)
        for ship_faction in saved_fittings:
            ship_types = saved_fittings[ship_faction]
            for ship_type in ship_types:
                ships = saved_fittings[ship_faction][ship_type]
                saved_fittings[ship_faction][ship_type] = {}
                for ship in ships:
                    saved_fittings[ship_faction][ship_type][ship] = []

        for saved_fitting_fname in saved_fittings_fnames:
            with open(saved_fitting_fname, 'r') as stream:
                try:
                    saved_fitting_data = yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    print(exc)
            saved_fitting_ship = saved_fitting_data["ship"]
            saved_fittings[saved_fitting_ship["faction"]][saved_fitting_ship["type"]][saved_fitting_ship["name"]].append(saved_fitting_data)

        return saved_fittings

    def make_ship_treedata(self, ship_names):
        saved_fittings_data = self.get_saved_fittings(ship_names)
        treedata = sg.TreeData()
        for ship_faction in ship_names:
            treedata.Insert('', ship_faction, ship_faction, values=[])
            ship_types = ship_names[ship_faction]
            for ship_type in ship_types:
                treedata.Insert(ship_faction, ship_type + "::" + ship_faction, ship_type, values=[])
                ships = ship_names[ship_faction][ship_type]
                for ship in ships:
                    treedata.Insert(ship_type + "::" + ship_faction, ship + "::" + ship_type, ship, values=[])
                    if saved_fittings_data[ship_faction][ship_type][ship]:
                        for saved in saved_fittings_data[ship_faction][ship_type][ship]:
                            treedata.Insert(ship + "::" + ship_type, "loadfit::" + saved["fitting_name"], saved["fitting_name"], values=[saved])
                    treedata.Insert(ship + "::" + ship_type, "loadfit::New*::" + ship + "::" + ship_type + "::" + ship_faction, "New*", values=[])
        return treedata

    def make_treedata(self, slot_data, is_drone=False, max_drone_size=None):
        treedata = sg.TreeData()
        for slot_type in slot_data:
            treedata.Insert('', slot_type, slot_type, values=[])
            sub_slot_types = slot_data[slot_type]
            for sub_slot_type in sub_slot_types:
                treedata.Insert(slot_type, sub_slot_type, sub_slot_type, values=[])
                slot_sizes = sub_slot_types[sub_slot_type]
                for slot_size in slot_sizes:
                    icon_fname = slot_type + "_" + sub_slot_type + "_" + slot_size
                    icon = None
                    if not is_drone:
                        icon = self.get_icon(icon_fname)
                    treedata.Insert(sub_slot_type, slot_size, slot_size, values=[], icon=icon)
                    items = slot_sizes[slot_size]
                    for item in items:
                        item_data = items[item]
                        if is_drone:
                            icon_fname += "_" + item.split(" ")[-1].lower()
                        icon = self.get_icon(icon_fname, faction=item_data["faction"])
                        key = slot_type + "_" + sub_slot_type + "_" + slot_size + "_" + item
                        treedata.Insert(slot_size, key, item, values=item_data, icon=icon)
                    if slot_size == max_drone_size: # limit drones to max size from ship
                        break
        return treedata

    def get_icon(self, icon_fname, faction='none', size=(24, 24)):
        icon_fname = icon_fname.replace("_", "-")
        img = cv2.imread("./icons/" + icon_fname + ".png")
        if img is not None:
            img = cv2.resize(img, size)
        else:
            img = cv2.imread("./icons/blank.png")
            img = cv2.resize(img, size)
        if faction != 'none':
            for i in range(0, int(size[0] / 3)):
                for j in range(size[1] - int(size[1] / 3) + i, size[1]):
                    img[i, j] = COLORS[faction]
        _, buffer = cv2.imencode('.png', img)
        text = base64.b64encode(buffer)
        return text
