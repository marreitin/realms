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

from gi.repository import Adw

from realms.ui.components.bindable_entries import BindableComboRow
from realms.ui.components.common import deleteRow
from realms.ui.components.domain.address_row import AddressRow

from .base_device_page import BaseDevicePage


class InputPage(BaseDevicePage):
    def build(self):
        self.group = Adw.PreferencesGroup(
            title=self.getTitle(), description="Input device"
        )
        self.prefs_page.add(self.group)

        self.type_row = BindableComboRow(
            ["mouse", "keyboard", "tablet", "passthrough", "evdev"],
            title="Interface type",
        )
        self.group.add(self.type_row)

        self.bus_row = BindableComboRow(
            ["xen", "ps2", "usb", "virtio"], title="Device bus type"
        )
        self.group.add(self.bus_row)

        self.address_row = AddressRow(self.xml_tree, self.showApply, ["pci"])
        self.group.add(self.address_row)

        if not self.use_for_adding:
            self.group.add(deleteRow(self.deleteDevice))

        self.updateData()

    def updateData(self):
        self.group.set_title(self.getTitle())
        self.type_row.bindAttr(self.xml_tree, "type", self.showApply)
        self.bus_row.bindAttr(self.xml_tree, "bus", self.showApply)
        self.address_row.setXML(self.xml_tree)

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return self.xml_tree.get("type", "").capitalize()

    def getDescription(self) -> str:
        return "Input device"

    def getIconName(self) -> str:
        t = self.xml_tree.get("type")
        if t == "mouse":
            return "mouse-wireless-symbolic"
        if t == "keyboard":
            return "keyboard3-symbolic"
        if t == "tablet":
            return "wacom-symbolic"
        return "gamepad-symbolic"
