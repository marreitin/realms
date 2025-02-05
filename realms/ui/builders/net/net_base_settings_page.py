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
import xml.etree.ElementTree as ET

from gi.repository import Adw, Gtk


class BaseNetSettingsPage(Adw.NavigationPage):
    def __init__(self, parent):
        super().__init__(title="settings")

        self.parent = parent

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.box)

        self.prefs_page = Adw.PreferencesPage()
        self.box.append(self.prefs_page)

    def build(self):
        raise NotImplementedError

    def updateData(self, xml_tree: ET.Element):
        raise NotImplementedError
