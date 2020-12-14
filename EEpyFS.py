import yaml

from gui import GUI

def main():
    with open("data/ships.yaml", 'r') as stream:
        try:
            ships_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open("data/high_slots.yaml", 'r') as stream:
        try:
            high_slots_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open("data/mid_slots.yaml", 'r') as stream:
        try:
            mid_slots_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open("data/drones.yaml", 'r') as stream:
        try:
            drone_slots_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open("data/low_slots.yaml", 'r') as stream:
        try:
            low_slots_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open("data/combat_rigs.yaml", 'r') as stream:
        try:
            combat_rigs_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open("data/engineer_rigs.yaml", 'r') as stream:
        try:
            engineer_rigs_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    app_gui = GUI(ships_data, high_slots_data, mid_slots_data, drone_slots_data, low_slots_data, combat_rigs_data, engineer_rigs_data)

    while True:
        if not app_gui.read():
            break

if __name__ == '__main__':
    main()
