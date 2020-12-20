import yaml

from gui import GUI
from data_loader import DataLoader

def main():

    data_loader = DataLoader()

    app_gui = GUI(*data_loader.get_loaded_data())

    while True:
        if not app_gui.read():
            break

if __name__ == '__main__':
    main()
