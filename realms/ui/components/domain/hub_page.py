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

from realms.ui.components.bindable_entries import BindableComboRow
from realms.ui.components.common import deleteRow

from .base_device_page import BaseDevicePage


class HubPage(BaseDevicePage):
    def build(self):
        self.group = Adw.PreferencesGroup(
            title=self.getTitle(), description="USB hub device"
        )
        self.prefs_page.add(self.group)

        type_row = BindableComboRow(["usb"], title="Hub type")
        self.group.add(type_row)
        type_row.bindAttr(self.xml_tree, "type", self.showApply)

        if not self.use_for_adding:
            self.group.add(deleteRow(self.deleteDevice))

    def updateData(self):
        pass

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "USB Hub"

    def getDescription(self) -> str:
        return ""

    def getIconName(self) -> str:
        return "dock-symbolic"
