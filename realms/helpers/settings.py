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


class Settings:
    """Settings singleton object."""

    __home_dir__ = os.path.expanduser("~")
    __config_dir__ = os.path.join(__home_dir__, ".config")
    __realms_config_dir__ = os.path.join(__config_dir__, "realms")
    __settings_path__ = os.path.join(__realms_config_dir__, "settings.json")

    __settings_data__ = {}

    @classmethod
    def prepare(cls):
        """Create settings directory if necessary."""
        try:
            if not os.path.exists(cls.__realms_config_dir__):
                os.mkdir(cls.__realms_config_dir__)
        except Exception:
            traceback.print_exc()

        cls.__settings_data__ = {}

    @classmethod
    def get(cls, key: str) -> any:
        """Get a key from the settings. Always reloads
        them from disk.

        Args:
            key (str): Key

        Returns:
            any: Value or None
        """
        with open(cls.__settings_path__, "r") as f:
            cls.__settings_data__ = json.load(f)
        if key in cls.__settings_data__:
            return cls.__settings_data__[key]
        else:
            return None

    @classmethod
    def put(cls, key: str, data: any) -> None:
        """Put or update key in settings.

        Args:
            key (str): Key
            data (any): Value
        """
        cls.__settings_data__[key] = data
        cls.__save__()

    @classmethod
    def __save__(cls):
        """Save settings dict."""
        with open(cls.__settings_path__, "w") as f:
            json.dump(cls.__settings_data__, f)
