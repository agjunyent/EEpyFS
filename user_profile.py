# pylint: disable=line-too-long

import yaml
from pathlib import Path

class UserProfile():
    def __init__(self, profile_name=None, profile_faction=None):
        self.profile_name = profile_name
        self.profile_faction = profile_faction

        with open("templates/profile_template.yaml", 'r') as stream:
            try:
                self.profile_data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

    def save(self, profile_data):
        self.profile_data["profile"]["name"] = self.profile_name
        self.profile_data["profile"]["faction"] = self.profile_faction

        for skill_group in self.profile_data["skills"]:
            skill_types = self.profile_data["skills"][skill_group]
            for skill_type in skill_types:
                skill_names = skill_types[skill_type]
                for skill_name in skill_names:
                    self.profile_data["skills"][skill_group][skill_type][skill_name] = profile_data[skill_name]

        profile_file = "saved_profiles/" + self.profile_name + ".yaml"
        if Path(profile_file).is_file():
            return False
        else:
            with open(profile_file, "w") as stream:
                yaml.safe_dump(self.profile_data, stream)
            return True

    def overwrite(self):
        self.profile_data["profile"]["name"] = self.profile_name
        self.profile_data["profile"]["faction"] = self.profile_faction
        profile_file = "saved_profiles/" + self.profile_name + ".yaml"
        with open(profile_file, "w") as stream:
            yaml.safe_dump(self.profile_data, stream)

    def load(self, profile_name):
        profile_file = "saved_profiles/" + profile_name + ".yaml"
        if Path(profile_file).is_file():
            with open(profile_file, 'r') as stream:
                try:
                    self.profile_data = yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    print(exc)
            self.profile_name = self.profile_data["profile"]["name"]
            self.profile_faction = self.profile_data["profile"]["faction"]

    def set_skills_data(self, skills_data):
        self.profile_data["skills"] = skills_data

    def get_skills_data(self):
        skill_data = {}
        for skill_group in self.profile_data["skills"]:
            skill_types = self.profile_data["skills"][skill_group]
            for skill_type in skill_types:
                skill_names = skill_types[skill_type]
                for skill_name in skill_names:
                    skill_data[skill_name] = self.profile_data["skills"][skill_group][skill_type][skill_name]
        return skill_data

    def get_full_skills_data(self):
        return self.profile_data["skills"]
