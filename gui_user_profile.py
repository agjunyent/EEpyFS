# pylint: disable=line-too-long

import copy
import PySimpleGUI as sg

from user_profile import UserProfile

FACTIONS = ["Amarr", "Caldari", "Gallente", "Minmatar"]

class GUIUserProfile():
    def __init__(self):
        self.default_user = UserProfile()
        self.user_profile = UserProfile()

    def create_new_profile(self):
        profile_name = None
        profile_faction = None

        layout = self.get_layout()

        window = sg.Window("New profile", layout=layout, force_toplevel=True, modal=True)
        window.Finalize()

        while True:
            event, values = window.read()
            if event == "create":
                profile_name = values["name"]
                self.user_profile = UserProfile(profile_name, profile_faction)
                if not self.user_profile.save(values):
                    overwrite = sg.popup_ok_cancel("Profile name already exists. Overwirte?")
                    if overwrite == 'OK':
                        self.user_profile.overwrite()
                        break
                else:
                    break
            elif event == "faction":
                profile_faction = values["faction"]
            elif event in {sg.WIN_CLOSED, "Cancel"}:
                window.close()
                return

            if values and values["name"] and profile_faction:
                window["create"].Update(disabled=False)
            elif values and not values["name"]:
                window["create"].Update(disabled=True)
        window.close()
        return copy.deepcopy(self.user_profile)

    def edit_user_profile(self, user_profile):
        profile_name = user_profile.profile_name
        profile_faction = user_profile.profile_faction

        if profile_name:
            self.user_profile = user_profile
            layout = self.get_layout()

            window = sg.Window("New profile", layout=layout, force_toplevel=True, modal=True)
            window.Finalize()
            window["save"].Update(disabled=False)
            window["name"].Update(profile_name, disabled=True)
            window["faction"].Update(profile_faction, disabled=True)

            while True:
                event, values = window.read()
                if event == "save":
                    if not self.user_profile.save(values):
                        overwrite = sg.popup_ok_cancel("Save changes?")
                        if overwrite == 'OK':
                            self.user_profile.overwrite()
                    else:
                        break
                elif event in {sg.WIN_CLOSED, "Cancel"}:
                    window.close()
                    return
            window.close()
            return copy.deepcopy(self.user_profile)
        else:
            return self.create_new_profile()

    def get_skills_layout(self):
        skill_levels = self.user_profile.get_skills_data()
        skills_data = self.default_user.get_full_skills_data()
        layout = []
        for skill_group in skills_data:
            skill_types = skills_data[skill_group]
            skill_types_layout = []
            skill_group_layout = []
            for skill_type in skill_types:
                skill_names = skill_types[skill_type]
                skill_names_layout = [[sg.Text(skill_name, size=(50, 1))] + [sg.Combo([0, 1, 2, 3, 4, 5], key=skill_name, size=(10, 1), default_value=skill_levels[skill_name])] for skill_name in skill_names]
                skill_types_layout.append(sg.Tab(skill_type, layout=skill_names_layout))
            skill_group_layout.append(sg.TabGroup([skill_types_layout]))
            layout.append(sg.Tab(skill_group, [skill_group_layout]))
        return [sg.TabGroup([layout])]

    def get_layout(self):
        name_layout = [sg.Text('Name: ', size=(8, 1))] + [sg.InputText("", key="name", enable_events=True, size=(20, 1))]
        factions_layout = [sg.Text('Faction: ', size=(8, 1))] + [sg.Combo(FACTIONS, key="faction", enable_events=True, size=(20, 1))]

        save_button = sg.Button("Save", key="save", disabled=True)
        cancel_button = sg.Cancel()
        buttons_layout = [save_button] + [cancel_button]
        skills_layout = self.get_skills_layout()
        layout = [
            name_layout,
            factions_layout,
            skills_layout,
            buttons_layout,
        ]
        return layout
