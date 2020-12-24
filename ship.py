import yaml
import copy
import math

PROPULSION_THRUST_BONUS = {}
PROPULSION_THRUST_BONUS["small"] = 1.35
PROPULSION_THRUST_BONUS["medium"] = 13.5
PROPULSION_THRUST_BONUS["large"] = 135

class Ship():
    def __init__(self, name, ship_data, profile_data):
        self.profile_skills_data = profile_data.get_skills_data()

        self.name = name
        self.type = ship_data["type"]
        self.faction = ship_data["faction"]
        self.max_slots = ship_data["slots"]
        self.max_rigs = ship_data["rigs"]

        self.slots = {}
        self.slots["high"] = [None] * self.max_slots["high"]
        self.slots["high-base"] = [None] * self.max_slots["high"]
        self.slots["mid"] = [None] * self.max_slots["mid"]
        self.slots["drone"] = [None] * self.max_slots["drone"]
        self.slots["drone-base"] = [None] * self.max_slots["drone"]
        self.slots["drone_size"] = self.max_slots["drone_size"]
        self.slots["low"] = [None] * self.max_slots["low"]

        self.slots["combat"] = [None] * self.max_rigs["combat"]
        self.slots["engineer"] = [None] * self.max_rigs["engineer"]

        self.base_cargo = ship_data["cargo"]
        self.base_targeting = ship_data["targeting"]
        self.base_navigation = ship_data["navigation"]
        self.base_navigation["propulsion_thrust_bonus"] = 0

        self.base_defenses = ship_data["defenses"]
        self.base_capacitor = ship_data["capacitor"]
        self.base_capacitor["consumption"] = 0
        self.base_powergrid = ship_data["powergrid"]

        with open("data/bonus_data.yaml", 'r') as stream:
            try:
                self.raw_bonus_data = yaml.safe_load(stream)
                self.ship_bonus_data = copy.deepcopy(self.raw_bonus_data)
                self.ship_role_data = copy.deepcopy(self.raw_bonus_data)
                self.skills_bonus_data = copy.deepcopy(self.raw_bonus_data)
                self.fittings_bonus_data = copy.deepcopy(self.raw_bonus_data)
                self.rigs_bonus_data = copy.deepcopy(self.raw_bonus_data)
            except yaml.YAMLError as exc:
                print(exc)

        self.get_skill_data()

        ship_bonus = ship_data["bonus"]
        if ship_bonus["role"] != 'none':
            self.update_ship_bonus_data(ship_bonus["role"], is_role=True)
        self.update_ship_bonus_data(ship_bonus["skills"]["first"])
        self.update_ship_bonus_data(ship_bonus["skills"]["second"])

        self.defenses = copy.deepcopy(self.base_defenses)
        self.powergrid = copy.deepcopy(self.base_powergrid)
        self.capacitor = copy.deepcopy(self.base_capacitor)
        self.navigation = copy.deepcopy(self.base_navigation)

        self.update_ship_stats()

    def update_ship_bonus_data(self, current_bonus_type, is_role=False):
        if current_bonus_type == 'none':
            return
        current_skill_level = 1
        for bonus in current_bonus_type:
            if bonus == "name":
                try:
                    current_skill_level = self.profile_skills_data[current_bonus_type[bonus]]
                except:
                    print("Skill", current_bonus_type[bonus], "not implemented yet")
                continue
            else:
                slot_type = current_bonus_type[bonus]
                for sub_slot_type in slot_type:
                    if sub_slot_type == "any":
                        for sub_slot_type in self.ship_bonus_data[bonus]:
                            for slot in slot_type["any"]:
                                if slot == "any":
                                    for slot_size in self.ship_bonus_data[bonus][sub_slot_type]:
                                        for slot_bonus in slot_type["any"]["any"]:
                                            if slot_bonus in {"damage", "resists"}:
                                                for damage_type in slot_type["any"]["any"][slot_bonus]:
                                                    if is_role:
                                                        self.ship_role_data[bonus][sub_slot_type][slot_size][slot_bonus][damage_type] += slot_type["any"]["any"][slot_bonus][damage_type]
                                                    else:
                                                        self.ship_bonus_data[bonus][sub_slot_type][slot_size][slot_bonus][damage_type] += slot_type["any"]["any"][slot_bonus][damage_type] * current_skill_level
                                            else:
                                                if is_role:
                                                    self.ship_role_data[bonus][sub_slot_type][slot_size][slot_bonus] += slot_type["any"]["any"][slot_bonus]
                                                else:
                                                    self.ship_bonus_data[bonus][sub_slot_type][slot_size][slot_bonus] += slot_type["any"]["any"][slot_bonus] * current_skill_level
                                else:
                                    for slot_bonus in slot_type["any"][slot]:
                                        if slot_bonus in {"damage", "resists"}:
                                            for damage_type in slot_type["any"][slot][slot_bonus]:
                                                if is_role:
                                                    self.ship_role_data[bonus][sub_slot_type][slot][slot_bonus][damage_type] += slot_type["any"][slot][slot_bonus][damage_type]
                                                else:
                                                    self.ship_bonus_data[bonus][sub_slot_type][slot][slot_bonus][damage_type] += slot_type["any"][slot][slot_bonus][damage_type] * current_skill_level
                                        else:
                                            if is_role:
                                                self.ship_role_data[bonus][sub_slot_type][slot][slot_bonus] += slot_type["any"][slot][slot_bonus]
                                            else:
                                                self.ship_bonus_data[bonus][sub_slot_type][slot][slot_bonus] += slot_type["any"][slot][slot_bonus] * current_skill_level

                    else:
                        slot_size = slot_type[sub_slot_type]
                        for slot in slot_size:
                            if slot == "any":
                                for slot_size in self.ship_bonus_data[bonus][sub_slot_type]:
                                    for slot_bonus in slot_type[sub_slot_type]["any"]:
                                        if slot_bonus in {"damage", "resists"}:
                                            for damage_type in slot_type[sub_slot_type]["any"][slot_bonus]:
                                                if is_role:
                                                    self.ship_role_data[bonus][sub_slot_type][slot_size][slot_bonus][damage_type] += slot_type[sub_slot_type]["any"][slot_bonus][damage_type]
                                                else:
                                                    self.ship_bonus_data[bonus][sub_slot_type][slot_size][slot_bonus][damage_type] += slot_type[sub_slot_type]["any"][slot_bonus][damage_type] * current_skill_level
                                        elif slot_bonus == "ship":
                                            continue
                                        else:
                                            if is_role:
                                                self.ship_role_data[bonus][sub_slot_type][slot_size][slot_bonus] += slot_type[sub_slot_type]["any"][slot_bonus]
                                            else:
                                                self.ship_bonus_data[bonus][sub_slot_type][slot_size][slot_bonus] += slot_type[sub_slot_type]["any"][slot_bonus] * current_skill_level
                            else:
                                if not isinstance(slot_type[sub_slot_type][slot], dict):
                                    if is_role:
                                        self.ship_role_data[bonus][sub_slot_type][slot] += slot_type[sub_slot_type][slot]
                                    else:
                                        self.ship_bonus_data[bonus][sub_slot_type][slot] += slot_type[sub_slot_type][slot] * current_skill_level
                                    continue
                                for slot_bonus in slot_type[sub_slot_type][slot]:
                                    if slot_bonus in {"damage", "resists"}:
                                        for damage_type in slot_type[sub_slot_type][slot][slot_bonus]:
                                            if is_role:
                                                self.ship_role_data[bonus][sub_slot_type][slot][slot_bonus][damage_type] += slot_type[sub_slot_type][slot][slot_bonus][damage_type]
                                            else:
                                                self.ship_bonus_data[bonus][sub_slot_type][slot][slot_bonus][damage_type] += slot_type[sub_slot_type][slot][slot_bonus][damage_type] * current_skill_level
                                    elif slot_bonus == "value":
                                        if is_role:
                                            self.ship_role_data[bonus][sub_slot_type][slot][slot_bonus]["percent"] += slot_type[sub_slot_type][slot][slot_bonus]["percent"]
                                            self.ship_role_data[bonus][sub_slot_type][slot][slot_bonus]["flat"] += slot_type[sub_slot_type][slot][slot_bonus]["flat"]
                                        else:
                                            self.ship_bonus_data[bonus][sub_slot_type][slot][slot_bonus]["percent"] += slot_type[sub_slot_type][slot][slot_bonus]["percent"] * current_skill_level
                                            self.ship_bonus_data[bonus][sub_slot_type][slot][slot_bonus]["flat"] += slot_type[sub_slot_type][slot][slot_bonus]["flat"] * current_skill_level
                                    else:
                                        if is_role:
                                            self.ship_role_data[bonus][sub_slot_type][slot][slot_bonus] += slot_type[sub_slot_type][slot][slot_bonus]
                                        else:
                                            self.ship_bonus_data[bonus][sub_slot_type][slot][slot_bonus] += slot_type[sub_slot_type][slot][slot_bonus] * current_skill_level

    def is_slot_empty(self, slot):
        slot_type, slot_number = slot.split("-")[1:]
        current_slot = self.slots[slot_type][int(slot_number)]
        return current_slot == None

    def add_slot(self, slot, slot_data):
        item_data = copy.deepcopy(slot_data)
        slot_type, slot_number = slot.split("-")[1:]
        current_slot = self.slots[slot_type][int(slot_number)]

        if slot_type in {"high", "drone"}:
            item_data_bonus = self.apply_bonus_to_high_slot_data(item_data)
        else:
            item_data_bonus = self.apply_bonus_to_bonus_slot_data(item_data)

        data = list(item_data_bonus.values())[0]

        slot_number = int(slot_number)
        slot_added = False
        num_full_slots = 0
        slot_name = "powergrid"
        num_max_slots = self.max_rigs[slot_type] if slot_type in {"combat", "engineer"} else self.max_slots[slot_type]
        while current_slot:
            num_full_slots += 1
            if num_full_slots >= num_max_slots:
                return False, "full"
            slot_number += 1
            if slot_number >= num_max_slots:
                slot_number = 0
            current_slot = self.slots[slot_type][int(slot_number)]

        if (self.powergrid["used"] + data["powergrid"]) <= self.powergrid["value"]:
            if slot_type == "high":
                self.slots["high-base"][slot_number] = item_data
                self.slots[slot_type][slot_number] = item_data_bonus
            elif slot_type == "low":
                self.slots[slot_type][slot_number] = item_data_bonus
            elif slot_type == "drone":
                self.slots["drone-base"][slot_number] = item_data
                self.slots[slot_type][slot_number] = item_data_bonus
            elif slot_type == "combat":
                self.slots[slot_type][slot_number] = None
                self.slots[slot_type][slot_number] = item_data_bonus
            elif slot_type == "engineer":
                self.slots[slot_type][slot_number] = None
                self.slots[slot_type][slot_number] = item_data_bonus
            else:
                self.slots[slot_type][slot_number] = item_data_bonus
            self.powergrid["used"] += data["powergrid"]
            slot_added = True

            self.fittings_bonus_data = copy.deepcopy(self.raw_bonus_data)
            self.capacitor["consumption"] = 0
            for slot_type in ["low", "combat", "engineer"]:
                self.update_fittings_bonus_data(slot_type)
            self.update_slots_stats()
            slot = slot.split("-")[0:-1]
            slot.append(str(slot_number))
            slot_name = ("-").join(slot)
        return slot_added, slot_name

    def remove_slot(self, slot):
        slot_type, slot_number = slot.split("-")[1:]
        current_slot = self.slots[slot_type][int(slot_number)]
        slot_removed = False
        if current_slot:
            slot_powergrid = list(current_slot.values())[0]["powergrid"]
            if slot_type == "high":
                self.slots["high-base"][int(slot_number)] = None
                self.slots[slot_type][int(slot_number)] = None
            elif slot_type == "low":
                self.slots[slot_type][int(slot_number)] = None
            elif slot_type == "drone":
                self.slots["drone-base"][int(slot_number)] = None
                self.slots[slot_type][int(slot_number)] = None
            elif slot_type == "combat":
                self.slots[slot_type][int(slot_number)] = None
            elif slot_type == "engineer":
                self.slots[slot_type][int(slot_number)] = None
            else:
                self.slots[slot_type][int(slot_number)] = None
            self.powergrid["used"] -= slot_powergrid
            slot_removed = True
            self.fittings_bonus_data = copy.deepcopy(self.raw_bonus_data)
            self.capacitor["consumption"] = 0
            for slot_type in ["low", "combat", "engineer"]:
                self.update_fittings_bonus_data(slot_type)
            self.update_slots_stats()
        return slot_removed

    def apply_bonus_to_high_slot_data(self, item_data):
        item_data_with_bonus = copy.deepcopy(item_data)
        item_name = list(item_data_with_bonus.keys())[0]
        item_info = item_name.split("_")
        item_type, sub_item_type, item_size, *_ = item_info
        stat_ship_bonus = self.ship_bonus_data[item_type][sub_item_type][item_size]
        role_ship_bonus = self.ship_role_data[item_type][sub_item_type][item_size]
        stat_skill_bonus = self.skills_bonus_data[item_type][sub_item_type][item_size]
        for item_stat in stat_ship_bonus:
            item_stat_data = item_data_with_bonus[item_name][item_stat]
            if item_stat in {"damage", "resists"}:
                for val in item_stat_data:
                    item_stat_data[val] = item_stat_data[val] * ((1 + stat_ship_bonus[item_stat][val] / 100) *
                                                                 (1 + role_ship_bonus[item_stat][val] / 100) *
                                                                 (1 + (stat_skill_bonus[item_stat][val] / 100) +
                                                                      (self.fittings_bonus_data[item_type][sub_item_type][item_size][item_stat][val] / 100)))
            elif item_stat == "activation_time":
                item_data_with_bonus[item_name][item_stat] = item_data_with_bonus[item_name][item_stat] * ((1 - stat_ship_bonus[item_stat] / 100) *
                                                                                                           (1 - stat_skill_bonus[item_stat] / 100) *
                                                                                                           (1 - role_ship_bonus[item_stat] / 100) *
                                                                                                           (1 - self.fittings_bonus_data[item_type][sub_item_type][item_size][item_stat] / 100))
            elif item_stat == "control_range":
                item_data_with_bonus[item_name][item_stat] += (stat_ship_bonus[item_stat] +
                                                               role_ship_bonus[item_stat] +
                                                               stat_skill_bonus[item_stat] +
                                                               self.fittings_bonus_data[item_type][sub_item_type][item_size][item_stat])
            else:
                item_data_with_bonus[item_name][item_stat] = item_data_with_bonus[item_name][item_stat] * ((1 + stat_ship_bonus[item_stat] / 100) *
                                                                                                           (1 + role_ship_bonus[item_stat] / 100) *
                                                                                                           (1 + stat_skill_bonus[item_stat] / 100))
        return item_data_with_bonus

    def apply_bonus_to_bonus_slot_data(self, item_data):
        item_data_with_bonus = copy.deepcopy(item_data)
        item_name = list(item_data_with_bonus.keys())[0]
        item_info = item_name.split("_")
        item_type, sub_item_type, item_size, *_ = item_info
        stat_ship_bonus = self.ship_bonus_data[item_type][sub_item_type][item_size]
        role_ship_bonus = self.ship_role_data[item_type][sub_item_type][item_size]
        stat_skill_bonus = self.skills_bonus_data[item_type][sub_item_type][item_size]
        ship_bonus = None
        high_slot_bonus = None
        high_slot_bonus_type = None
        for item_stat in stat_ship_bonus:
            item_stat_data = item_data_with_bonus[item_name][item_stat]
            if item_stat == "ship":
                for ship_bonus in item_stat_data:
                    if ship_bonus == "navigation":
                        stat_data = item_stat_data[ship_bonus]
                        for bonus in stat_data:
                            item_data_with_bonus[item_name][item_stat][ship_bonus][bonus] += (stat_ship_bonus[item_stat][ship_bonus][bonus] +
                                                                                              role_ship_bonus[item_stat][ship_bonus][bonus] +
                                                                                              stat_skill_bonus[item_stat][ship_bonus][bonus])
                    else:
                        print("Ship Bonus", ship_bonus, "not implemented yet!")
            elif item_stat in {"launchers", "lasers", "railguns", "cannons", "turrets", "drones"}:
                high_slot_bonus_type = ["lasers", "railguns", "cannons"] if item_stat == "turrets" else [item_stat]
                high_slot_bonus = item_stat_data
            elif item_stat == "activation_cost":
                item_data_with_bonus[item_name][item_stat] = item_data_with_bonus[item_name][item_stat] * ((1 + -abs(stat_ship_bonus[item_stat])) *
                                                                                                           (1 + -abs(role_ship_bonus[item_stat])) *
                                                                                                           (1 + -abs(stat_skill_bonus[item_stat])))
                if item_data_with_bonus[item_name][item_stat] >= 100:
                    item_data_with_bonus[item_name][item_stat] = round(item_data_with_bonus[item_name][item_stat], 0)
            elif item_stat == "activation_time":
                if stat_skill_bonus[item_stat] >= 1:
                    item_data_with_bonus[item_name][item_stat] += role_ship_bonus[item_stat] + stat_ship_bonus[item_stat] + stat_skill_bonus[item_stat]
                else:
                    item_data_with_bonus[item_name][item_stat] = item_data_with_bonus[item_name][item_stat] * ((1 + stat_ship_bonus[item_stat]) *
                                                                                                               (1 + role_ship_bonus[item_stat]) *
                                                                                                               (1 + stat_skill_bonus[item_stat]))
                if item_data_with_bonus[item_name][item_stat] >= 100:
                    item_data_with_bonus[item_name][item_stat] = round(item_data_with_bonus[item_name][item_stat], 0)
            else:
                item_data_with_bonus[item_name][item_stat] = item_data_with_bonus[item_name][item_stat] * ((1 + stat_ship_bonus[item_stat] / 100) *
                                                                                                           (1 + role_ship_bonus[item_stat] / 100) *
                                                                                                           (1 + stat_skill_bonus[item_stat] / 100))
                if item_data_with_bonus[item_name][item_stat] >= 100:
                    item_data_with_bonus[item_name][item_stat] = round(item_data_with_bonus[item_name][item_stat], 0)
        return item_data_with_bonus

    def update_fittings_bonus_data(self, slot_type):
        item_names = []
        for slot_data in self.slots[slot_type]:
            if not slot_data:
                continue
            item_data_with_bonus = copy.deepcopy(slot_data)
            item_name = list(slot_data.keys())[0]
            item_info = item_name.split("_")
            item_type, sub_item_type, item_size, *_ = item_info
            if item_type == "propulsion":
                self.navigation["propulsion_thrust_bonus"] = PROPULSION_THRUST_BONUS[item_size]
            num_same_items = 0
            for same_item_name in item_names:
                same_item_info = same_item_name.split("_")
                same_item_type, same_sub_item_type, same_item_size, *_ = same_item_info
                if item_type == same_item_type and sub_item_type == same_sub_item_type and item_size == same_item_size:
                    num_same_items += 1
            item_names.append(item_name)
            stat_ship_bonus = self.ship_bonus_data[item_type][sub_item_type][item_size]
            for item_stat in stat_ship_bonus:
                item_stat_data = item_data_with_bonus[item_name][item_stat]
                if item_stat == "activation_cost":
                    act_cost = item_data_with_bonus[item_name]["activation_cost"]
                    act_time = item_data_with_bonus[item_name]["activation_time"]
                    self.add_capacitor_cost(act_cost, act_time)
                if item_stat == "ship":
                    ship_bonus = item_stat_data
                    for stat_type in ship_bonus:
                        if stat_type == "defenses":
                            stat_data = ship_bonus[stat_type]
                            for stat_name in stat_data:
                                stat_bonus = stat_data[stat_name]
                                for bonus in stat_bonus:
                                    if bonus == "value":
                                        self.fittings_bonus_data["ship"][stat_type][stat_name]["value"]["percent"] += ship_bonus[stat_type][stat_name]["value"]["percent"]
                                        self.fittings_bonus_data["ship"][stat_type][stat_name]["value"]["flat"] += ship_bonus[stat_type][stat_name]["value"]["flat"]
                                    else:
                                        for resist_type in stat_bonus["resists"]:
                                            self.fittings_bonus_data["ship"][stat_type][stat_name]["resists"][resist_type] = (1 - ((1 - (self.fittings_bonus_data["ship"][stat_type][stat_name]["resists"][resist_type] / 100)) *
                                                                                                                                   (1 - (self.get_stack_penalty(num_same_items) * ship_bonus[stat_type][stat_name]["resists"][resist_type] / 100)))) * 100
                        elif stat_type in {"capacitor", "powergrid"}:
                            stat_data = ship_bonus[stat_type]
                            for bonus in stat_data:
                                if bonus == "value":
                                    self.fittings_bonus_data["ship"][stat_type]["value"]["percent"] += ship_bonus[stat_type]["value"]["percent"]
                                    self.fittings_bonus_data["ship"][stat_type]["value"]["flat"] += ship_bonus[stat_type]["value"]["flat"]
                                elif bonus == "recharge":
                                    self.fittings_bonus_data["ship"][stat_type]["recharge"] += ship_bonus[stat_type]["recharge"]
                        elif stat_type == "navigation":
                            stat_data = ship_bonus[stat_type]
                            for bonus in stat_data:
                                self.fittings_bonus_data["ship"][stat_type][bonus] += ship_bonus[stat_type][bonus]
                        else:
                            print("Stat", stat_type, "not yet implemented!")
                elif item_stat in {"launchers", "lasers", "railguns", "cannons", "turrets", "drones"}:
                    high_slot_bonus_type = ["lasers", "railguns", "cannons"] if item_stat == "turrets" else [item_stat]
                    high_slot_bonus = item_stat_data
                    for high_slot_type in high_slot_bonus_type:
                        for sub_slot_type in self.ship_bonus_data[high_slot_type]:
                            for slot_size in self.ship_bonus_data[high_slot_type][sub_slot_type]:
                                for bonus in high_slot_bonus["any"]["any"]:
                                    if bonus == "damage":
                                        for damage_type in high_slot_bonus["any"]["any"]["damage"]:
                                            self.fittings_bonus_data[high_slot_type][sub_slot_type][slot_size][bonus][damage_type] += self.get_stack_penalty(num_same_items) * high_slot_bonus["any"]["any"]["damage"][damage_type]
                                    elif bonus == "activation_time":
                                        self.fittings_bonus_data[high_slot_type][sub_slot_type][slot_size][bonus] = (1 - (1 - self.fittings_bonus_data[high_slot_type][sub_slot_type][slot_size][bonus] / 100) *
                                                                                                                         (1 + (self.get_stack_penalty(num_same_items) * high_slot_bonus["any"]["any"][bonus] / 100))) * 100
                                    else:
                                        self.fittings_bonus_data[high_slot_type][sub_slot_type][slot_size][bonus] += self.get_stack_penalty(num_same_items) * high_slot_bonus["any"]["any"][bonus]
        return

    def update_slots_stats(self):
        for i in range(self.max_slots["high"]):
            if self.slots["high-base"][i]:
                self.slots["high"][i] = self.apply_bonus_to_high_slot_data(self.slots["high-base"][i])
        for i in range(self.max_slots["drone"]):
            if self.slots["drone-base"][i]:
                self.slots["drone"][i] = self.apply_bonus_to_high_slot_data(self.slots["drone-base"][i])
        return

    def update_ship_stats(self):
        self.update_powergrid()
        self.update_capacitor()
        self.update_defenses()
        self.update_navigation()

    def update_powergrid(self):
        self.powergrid["value"] = round((self.base_powergrid["value"] +
                                         self.skills_bonus_data["ship"]["powergrid"]["value"]["flat"] +
                                         self.fittings_bonus_data["ship"]["powergrid"]["value"]["flat"]) *
                                        (1 + self.ship_bonus_data["ship"]["powergrid"]["value"]["percent"] / 100) *
                                        (1 + (self.skills_bonus_data["ship"]["powergrid"]["value"]["percent"] / 100) +
                                        (self.fittings_bonus_data["ship"]["powergrid"]["value"]["percent"] / 100)))
        self.powergrid["used"] = round(self.powergrid["used"])

    def add_capacitor_cost(self, act_cost, act_time):
        consumption = act_cost / act_time
        self.capacitor["consumption"] += consumption

    def update_capacitor(self):
        self.capacitor["value"] = round((self.base_capacitor["value"]) *
                                        (1 + self.ship_bonus_data["ship"]["capacitor"]["value"]["percent"] / 100) *
                                        (1 + (self.skills_bonus_data["ship"]["capacitor"]["value"]["percent"] / 100) +
                                        (self.fittings_bonus_data["ship"]["capacitor"]["value"]["percent"] / 100)) +
                                        (self.skills_bonus_data["ship"]["capacitor"]["value"]["flat"] +
                                         self.fittings_bonus_data["ship"]["capacitor"]["value"]["flat"]), 0)
        self.capacitor["recharge"] = round(self.base_capacitor["recharge"] *
                                          (1 + self.ship_bonus_data["ship"]["capacitor"]["recharge"] / 100) *
                                          (1 + (self.skills_bonus_data["ship"]["capacitor"]["recharge"] / 100) +
                                          (self.fittings_bonus_data["ship"]["capacitor"]["recharge"] / 100)), 0)
        self.capacitor["rate"] = self.get_capacitor_rate()

        rate_percentage_list = []
        for i in range(1001):
            rate_percentage = round((10 * self.capacitor["value"] / self.capacitor["recharge"]) * (math.sqrt(i / 1000.0) - (i / 1000.0)), 2)
            rate_percentage_list.append(rate_percentage)

        seconds = 0
        percentage = 100
        current_cap = self.capacitor["value"]
        if self.capacitor["consumption"] > self.capacitor["rate"]:
            percentage = 0
            while current_cap >= self.capacitor["consumption"]:
                current_cap += rate_percentage_list[round(1000 * (current_cap / self.capacitor["value"]))]
                current_cap -= self.capacitor["consumption"]
                seconds += 1
        elif self.capacitor["consumption"] > 0:
            while True:
                current_cap -= self.capacitor["consumption"]
                recharge = rate_percentage_list[round(1000 * (current_cap / self.capacitor["value"]))]
                if recharge > self.capacitor["consumption"]:
                    break
                current_cap += recharge
            percentage = round(100 * (current_cap/self.capacitor["value"]))
        self.capacitor["stability"] = seconds
        self.capacitor["percentage"] = percentage
        # print(seconds, self.capacitor["rate"] - self.capacitor["consumption"])

    def update_defenses(self):
        for defense in self.defenses:
            self.defenses[defense]["value"] = round((self.base_defenses[defense]["value"]) *
                                                    (1 + self.ship_bonus_data["ship"]["defenses"][defense]["value"]["percent"] / 100) *
                                                    (1 + self.skills_bonus_data["ship"]["defenses"][defense]["value"]["percent"] / 100) *
                                                    (1 + self.fittings_bonus_data["ship"]["defenses"][defense]["value"]["percent"] / 100) +
                                                    (self.skills_bonus_data["ship"]["defenses"][defense]["value"]["flat"]) +
                                                    (self.fittings_bonus_data["ship"]["defenses"][defense]["value"]["flat"]), 0)
            for res in self.defenses[defense]["resists"]:
                self.defenses[defense]["resists"][res] = round(((1 - ((1 - self.base_defenses[defense]["resists"][res] / 100) *
                                                                (1 - self.ship_bonus_data["ship"]["defenses"][defense]["resists"][res] / 100) *
                                                                (1 - self.skills_bonus_data["ship"]["defenses"][defense]["resists"][res] / 100) *
                                                                (1 - self.fittings_bonus_data["ship"]["defenses"][defense]["resists"][res] / 100)))) * 100, 2)

    def update_navigation(self):
        self.navigation["mass"] = round(self.base_navigation["mass"] + self.fittings_bonus_data["ship"]["navigation"]["mass"], 0)
        self.navigation["warp_speed"] = round(self.base_navigation["warp_speed"] * ((1 + self.fittings_bonus_data["ship"]["navigation"]["warp_speed"] / 100) *
                                                                                    (1 + self.skills_bonus_data["ship"]["navigation"]["warp_speed"] / 100) *
                                                                                    (1 + self.ship_role_data["ship"]["navigation"]["warp_speed"] / 100)), 1)


        self.navigation["inertia_modifier"] = round(self.base_navigation["inertia_modifier"] * ((1 + self.fittings_bonus_data["ship"]["navigation"]["inertia_modifier"] / 100) *
                                                                                                (1 + self.skills_bonus_data["ship"]["navigation"]["inertia_modifier"] / 100)), 2)
        self.navigation["flight_velocity"] = round(self.base_navigation["flight_velocity"] * ((1 + self.skills_bonus_data["ship"]["navigation"]["flight_velocity"] / 100) *
                                                                                              (1 + (self.navigation["propulsion_thrust_bonus"] / (self.navigation["mass"] / 1000000.0)) * self.fittings_bonus_data["ship"]["navigation"]["flight_velocity"] / 100)), 1)

    def get_max_drone_size(self):
        return self.slots["drone_size"]

    def get_slot(self, slot):
        slot_type, slot_number = slot.split("-")[1:]
        return self.slots[slot_type][int(slot_number)]

    def get_ehp(self):
        self.update_defenses()
        total_ehp = 0
        for defense_type in self.defenses:
            defense = self.defenses[defense_type]
            min_resist = min(defense["resists"][val] for val in defense["resists"])
            total_ehp += defense["value"] / (1 - min_resist / 100.0)
        return int(total_ehp)

    def get_capacitor_rate(self):
        rate = (10 * self.capacitor["value"] / self.capacitor["recharge"]) * 0.25
        return round(rate, 2)

    def get_defenses(self):
        self.update_defenses()
        return self.defenses

    def get_capacitor(self):
        self.update_capacitor()
        return self.capacitor

    def get_powergrid(self):
        self.update_powergrid()
        return self.powergrid

    def get_navigation(self):
        self.update_navigation()
        return self.navigation

    def get_dps(self):
        dps = {}
        dps["launchers"] = 0
        dps["turrets"] = 0
        dps["drones"] = 0
        control_range = 0
        for slot in self.slots["high"]:
            if slot:
                slot_key = list(slot.keys())[0]
                slot_info = slot_key.split("_")
                slot_type, sub_slot_type, slot_size, *_ = slot_info
                if slot_type == "launchers":
                    dps["launchers"] += self.get_launcher_dps(slot[slot_key])
                else:
                    dps["turrets"] += self.get_turret_dps(slot[slot_key])
        for slot in self.slots["drone"]:
            if slot:
                drone_dps, drone_control_range = self.get_drone_dps(slot)
                dps["drones"] += drone_dps
                control_range = drone_control_range
        for dps_type in dps:
            dps[dps_type] = round(dps[dps_type], 2)
        total_dps = round(dps["launchers"] + dps["turrets"] + dps["drones"], 2)
        return dps, total_dps, control_range

    def get_launcher_dps(self, launcher_data):
        total_damage = 0
        launcher_damages = launcher_data["damage"]
        for val in launcher_damages:
            total_damage += launcher_damages[val]
        total_damage /= launcher_data["activation_time"]
        return total_damage

    def get_turret_dps(self, turret_data):
        total_damage = 0
        turret_damages = turret_data["damage"]
        for val in turret_damages:
            total_damage += turret_damages[val]
        total_damage /= turret_data["activation_time"]
        return total_damage

    def get_drone_dps(self, drone):
        total_damage = 0
        for dr in drone:
            current_drone_stats = drone[dr]
        drone_damages = current_drone_stats["damage"]
        for val in drone_damages:
            total_damage += drone_damages[val]
        total_damage /= current_drone_stats["activation_time"]
        control_range = current_drone_stats["control_range"]
        return total_damage, control_range

    def get_stack_penalty(self, num_items):
        val = math.pow(math.e, -math.pow(num_items / 2.67, 2))
        return val

    def export_fit(self):
        current_fit = {}
        current_fit["ship"] = {}
        current_fit["ship"]["faction"] = self.faction
        current_fit["ship"]["type"] = self.type
        current_fit["ship"]["name"] = self.name
        current_fit["high"] = []
        for slot in self.slots["high"]:
            current_fit["high"].append(list(slot.keys())[0] if slot else None)
        current_fit["mid"] = []
        for slot in self.slots["mid"]:
            current_fit["mid"].append(list(slot.keys())[0] if slot else None)
        current_fit["low"] = []
        for slot in self.slots["low"]:
            current_fit["low"].append(list(slot.keys())[0] if slot else None)
        current_fit["drone"] = []
        for slot in self.slots["drone"]:
            current_fit["drone"].append(list(slot.keys())[0] if slot else None)
        current_fit["engineer"] = []
        for slot in self.slots["engineer"]:
            current_fit["engineer"].append(list(slot.keys())[0] if slot else None)
        current_fit["combat"] = []
        for slot in self.slots["combat"]:
            current_fit["combat"].append(list(slot.keys())[0] if slot else None)
        return current_fit

    def get_skill_data(self):
        with open("data/skills_data.yaml", 'r') as stream:
            try:
                skill_data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        for skill_group_name in skill_data:
            skill_group = skill_data[skill_group_name]
            for skill_name in skill_group:
                current_skill_level = self.profile_skills_data[skill_name]
                if current_skill_level > 0:
                    skill = skill_group[skill_name][current_skill_level]
                    for skill_type in skill:
                        if skill_type == "ship":
                            if skill["ship"]["type"] == self.type:
                                skill_bonus = skill["ship"]["skill"]
                                for bonus_type in skill_bonus:
                                    for bonus in skill_bonus[bonus_type]:
                                        if bonus_type == "defenses":
                                            self.skills_bonus_data["ship"][bonus_type][bonus]["value"]["percent"] += skill_bonus[bonus_type][bonus]["value"]["percent"]
                                            self.skills_bonus_data["ship"][bonus_type][bonus]["value"]["flat"] += skill_bonus[bonus_type][bonus]["value"]["flat"]
                                        elif bonus == "value":
                                            self.skills_bonus_data["ship"][bonus_type][bonus]["percent"] += skill_bonus[bonus_type][bonus]["percent"]
                                            self.skills_bonus_data["ship"][bonus_type][bonus]["flat"] += skill_bonus[bonus_type][bonus]["flat"]
                                        else:
                                            self.skills_bonus_data["ship"][bonus_type][bonus] += skill_bonus[bonus_type][bonus]
                        else:
                            slot_type = skill[skill_type]
                            for sub_slot_type in slot_type:
                                if sub_slot_type == "any":
                                    for sub_slot_type in self.skills_bonus_data[skill_type]:
                                        for slot in slot_type["any"]:
                                            if slot == "any":
                                                for slot_size in self.skills_bonus_data[skill_type][sub_slot_type]:
                                                    for slot_bonus in slot_type["any"]["any"]:
                                                        if slot_bonus in {"damage", "resists"}:
                                                            for damage_type in slot_type["any"]["any"][slot_bonus]:
                                                                self.skills_bonus_data[skill_type][sub_slot_type][slot_size][slot_bonus][damage_type] += slot_type["any"]["any"][slot_bonus][damage_type]
                                                        elif slot_bonus == "value":
                                                            self.skills_bonus_data[skill_type][sub_slot_type][slot_size][slot_bonus]["percent"] += slot_type["any"]["any"][slot_bonus]["percent"]
                                                            self.skills_bonus_data[skill_type][sub_slot_type][slot_size][slot_bonus]["flat"] += slot_type["any"]["any"][slot_bonus]["flat"]
                                                        else:
                                                            self.skills_bonus_data[skill_type][sub_slot_type][slot_size][slot_bonus] += slot_type["any"]["any"][slot_bonus]
                                            elif slot in list(self.skills_bonus_data[skill_type][sub_slot_type].keys()):
                                                for slot_bonus in slot_type["any"][slot]:
                                                    if slot_bonus in {"damage", "resists"}:
                                                        for damage_type in slot_type["any"][slot][slot_bonus]:
                                                            self.skills_bonus_data[skill_type][sub_slot_type][slot][slot_bonus][damage_type] += slot_type["any"][slot][slot_bonus][damage_type]
                                                    elif slot_bonus == "value":
                                                        self.skills_bonus_data[skill_type][sub_slot_type][slot][slot_bonus]["percent"] += slot_type["any"][slot][slot_bonus]["percent"]
                                                        self.skills_bonus_data[skill_type][sub_slot_type][slot][slot_bonus]["flat"] += slot_type["any"][slot][slot_bonus]["flat"]
                                                    else:
                                                        self.skills_bonus_data[skill_type][sub_slot_type][slot][slot_bonus] += slot_type["any"][slot][slot_bonus]
                                else:
                                    slot_size = slot_type[sub_slot_type]
                                    for slot in slot_size:
                                        if slot == "any":
                                            for slot_size in self.skills_bonus_data[skill_type][sub_slot_type]:
                                                for slot_bonus in slot_type[sub_slot_type]["any"]:
                                                    if slot_bonus in {"damage", "resists"}:
                                                        for damage_type in slot_type[sub_slot_type]["any"][slot_bonus]:
                                                            self.skills_bonus_data[skill_type][sub_slot_type][slot_size][slot_bonus][damage_type] += slot_type[sub_slot_type]["any"][slot_bonus][damage_type]
                                                    elif slot_bonus == "value":
                                                        self.skills_bonus_data[skill_type][sub_slot_type][slot_size][slot_bonus]["percent"] += slot_type[sub_slot_type]["any"][slot_bonus]["percent"]
                                                        self.skills_bonus_data[skill_type][sub_slot_type][slot_size][slot_bonus]["flat"] += slot_type[sub_slot_type]["any"][slot_bonus]["flat"]
                                                    elif slot_bonus == "activation_time":
                                                        self.skills_bonus_data[skill_type][sub_slot_type][slot_size][slot_bonus] = ((1 + self.skills_bonus_data[skill_type][sub_slot_type][slot_size][slot_bonus]) * (1 + slot_type[sub_slot_type]["any"][slot_bonus] / 100)) - 1
                                                    elif slot_bonus == "activation_cost":
                                                        # self.skills_bonus_data[skill_type][sub_slot_type][slot_size][slot_bonus] = 1 - ((1 - self.skills_bonus_data[skill_type][sub_slot_type][slot_size][slot_bonus]) * (1 + slot_type[sub_slot_type]["any"][slot_bonus] / 100))
                                                        if sub_slot_type in {"boosters", "reparirers"}:
                                                            self.skills_bonus_data[skill_type][sub_slot_type][slot_size][slot_bonus] += slot_type[sub_slot_type]["any"][slot_bonus] / 100
                                                        else:
                                                            self.skills_bonus_data[skill_type][sub_slot_type][slot_size][slot_bonus] = 1 - ((1 - self.skills_bonus_data[skill_type][sub_slot_type][slot_size][slot_bonus]) * (1 + slot_type[sub_slot_type]["any"][slot_bonus] / 100))
                                                    elif slot_bonus == "ship":
                                                        for ship_bonus_type in slot_type[sub_slot_type]["any"]["ship"]:
                                                            ship_bonus_list = slot_type[sub_slot_type]["any"]["ship"][ship_bonus_type]
                                                            for ship_bonus in ship_bonus_list:
                                                                self.skills_bonus_data[skill_type][sub_slot_type][slot_size][slot_bonus][ship_bonus_type][ship_bonus] += slot_type[sub_slot_type]["any"][slot_bonus][ship_bonus_type][ship_bonus]
                                                    else:
                                                        self.skills_bonus_data[skill_type][sub_slot_type][slot_size][slot_bonus] += slot_type[sub_slot_type]["any"][slot_bonus]
                                        else:
                                            for slot_bonus in slot_type[sub_slot_type][slot]:
                                                if slot_bonus in {"damage", "resists"}:
                                                    for damage_type in slot_type[sub_slot_type][slot][slot_bonus]:
                                                        self.skills_bonus_data[skill_type][sub_slot_type][slot][slot_bonus][damage_type] += slot_type[sub_slot_type][slot][slot_bonus][damage_type]
                                                elif slot_bonus == "value":
                                                    self.skills_bonus_data[skill_type][sub_slot_type][slot][slot_bonus]["percent"] += slot_type[sub_slot_type][slot][slot_bonus]["percent"]
                                                    self.skills_bonus_data[skill_type][sub_slot_type][slot][slot_bonus]["flat"] += slot_type[sub_slot_type][slot][slot_bonus]["flat"]
                                                elif slot_bonus == "activation_time":
                                                    if skill_type == "weapons":
                                                        self.skills_bonus_data[skill_type][sub_slot_type][slot][slot_bonus] += slot_type[sub_slot_type][slot][slot_bonus]
                                                    else:
                                                        self.skills_bonus_data[skill_type][sub_slot_type][slot][slot_bonus] = ((1 + self.skills_bonus_data[skill_type][sub_slot_type][slot][slot_bonus]) * (1 + slot_type[sub_slot_type][slot][slot_bonus] / 100)) - 1
                                                elif slot_bonus == "activation_cost":
                                                    if sub_slot_type in {"boosters", "repairers"}:
                                                        self.skills_bonus_data[skill_type][sub_slot_type][slot][slot_bonus] += slot_type[sub_slot_type][slot][slot_bonus] / 100
                                                    else:
                                                        self.skills_bonus_data[skill_type][sub_slot_type][slot][slot_bonus] = 1 - ((1 - self.skills_bonus_data[skill_type][sub_slot_type][slot][slot_bonus]) * (1 + slot_type[sub_slot_type][slot][slot_bonus] / 100))
                                                elif slot_bonus == "ship":
                                                    for ship_bonus_type in slot_type[sub_slot_type][slot]["ship"]:
                                                        ship_bonus_list = slot_type[sub_slot_type][slot]["ship"][ship_bonus_type]
                                                        for ship_bonus in ship_bonus_list:
                                                            self.skills_bonus_data[skill_type][sub_slot_type][slot][slot_bonus][ship_bonus_type][ship_bonus] += slot_type[sub_slot_type][slot][slot_bonus][ship_bonus_type][ship_bonus]
                                                else:
                                                    self.skills_bonus_data[skill_type][sub_slot_type][slot][slot_bonus] += slot_type[sub_slot_type][slot][slot_bonus]
