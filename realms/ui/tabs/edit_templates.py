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
from gi.repository import Adw

from realms.ui.components.common import controlButton, iconButton
from realms.ui.components.preference_widgets import RealmsPreferencesPage

from .base_details import *


class EditTemplatesTab(BaseDetailsTab):
    """Class providing an editing tab for a libvirt connection."""

    def __init__(self, window: Adw.ApplicationWindow):
        super().__init__(window)

        self.save_btn = None

        self.toolbar_view = None
        self.navigation_view = None
        self.main_nav_page = None
        self.prefs_page = None
        self.default_group = None
        self.custom_group = None

        self.build()

    def build(self):
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.title_widget = Adw.WindowTitle(title="Templates")

        self.toolbar_view = Adw.ToolbarView(hexpand=True, vexpand=True)
        self.append(self.toolbar_view)

        self.navigation_view = Adw.NavigationView(animate_transitions=True)
        self.toolbar_view.set_content(self.navigation_view)

        self.main_nav_page = Adw.NavigationPage(title="Main")
        self.navigation_view.push(self.main_nav_page)

        box = Gtk.Box(vexpand=True, hexpand=True, orientation=Gtk.Orientation.VERTICAL)
        self.main_nav_page.set_child(box)

        self.prefs_page = RealmsPreferencesPage()
        box.append(self.prefs_page)

        self.default_group = Adw.PreferencesGroup(title="Default Templates")
        self.prefs_page.add(self.default_group)

        self.custom_group = Adw.PreferencesGroup(title="Custom Templates")
        self.prefs_page.add(self.custom_group)

        add_btn = iconButton(
            "", "list-add-symbolic", self.__onAddCustomClicked__, css_classes=["flat"]
        )
        self.custom_group.set_header_suffix(add_btn)

    def __onAddCustomClicked__(self, *_):
        pass

    def end(self):
        pass

    def getUniqueIdentifier(self) -> str:
        return "edit-templates"

    def setWindowHeader(self, window):
        window.headerSetTitleWidget(self.title_widget)
        # window.headerPackStart(self.connect_btn)
        # window.headerPackStart(self.disconnect_btn)
