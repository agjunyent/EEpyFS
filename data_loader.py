import yaml

class DataLoader():
    def __init__(self):
        with open("data/ships.yaml", 'r') as stream:
            try:
                self.ships_data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        with open("data/high_slots.yaml", 'r') as stream:
            try:
                self.high_slots_data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        with open("data/mid_slots.yaml", 'r') as stream:
            try:
                self.mid_slots_data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        with open("data/drones.yaml", 'r') as stream:
            try:
                self.drone_slots_data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        with open("data/low_slots.yaml", 'r') as stream:
            try:
                self.low_slots_data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        with open("data/combat_rigs.yaml", 'r') as stream:
            try:
                self.combat_rigs_data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        with open("data/engineer_rigs.yaml", 'r') as stream:
            try:
                self.engineer_rigs_data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

    def get_loaded_data(self):
        return self.ships_data, self.high_slots_data, self.mid_slots_data, self.drone_slots_data, self.low_slots_data, self.combat_rigs_data, self.engineer_rigs_data

