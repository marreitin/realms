# Realms, a libadwaita libvirt client.
# Copyright (C) 2025
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import json
import os
import traceback

home_dir = os.path.expanduser("~")
config_dir = os.path.join(home_dir, ".config")
realms_config_dir = os.path.join(config_dir, "realms")
settings_path = os.path.join(realms_config_dir, "settings.json")

__settings_data = None


def prepareSettings():
    global __settings_data
    try:
        print(realms_config_dir)
        print(settings_path)
        if not os.path.exists(realms_config_dir):
            os.mkdir(realms_config_dir)
    except Exception:
        traceback.print_exc()
        __settings_data = {}


def getSettings(key):
    global __settings_data
    with open(settings_path, "r") as f:
        __settings_data = json.load(f)
    if key in __settings_data:
        return __settings_data[key]
    else:
        return None


def putSettings(key, data):
    __settings_data[key] = data
    saveSettings()


def saveSettings():
    with open(settings_path, "w") as f:
        json.dump(__settings_data, f)
