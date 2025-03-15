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
from realms.ui.components.domain.boot_order_row import BootOrderRow

from .base_device_page import BaseDevicePage


class RedirdevPage(BaseDevicePage):
    """Redirection device."""

    def __init__(
        self, parent, xml_tree: ET.Element, use_for_adding=False, can_update=False
    ):
        super().__init__(parent, xml_tree, use_for_adding, can_update)

    def build(self):
        self.group = Adw.PreferencesGroup()
        self.prefs_page.add(self.group)

        self.bus_row = BindableComboRow(["bus"], title="Source bus")
        self.group.add(self.bus_row)

        # TODO: More types, but they're badly documented
        self.type_row = BindableComboRow(
            ["tcp", "spicevmc", "unix"], title="Device type"
        )
        self.group.add(self.type_row)

        self.boot_row = BootOrderRow(self.xml_tree, self.showApply)
        self.group.add(self.boot_row)

        self.address_row = AddressRow(self.xml_tree, self.showApply)
        self.group.add(self.address_row)

        if not self.use_for_adding:
            self.group.add(deleteRow(self.deleteDevice))

        self.updateData()

    def updateData(self):
        self.group.set_title(self.getTitle())

        self.bus_row.bindAttr(self.xml_tree, "bus", self.showApply)

        self.type_row.bindAttr(self.xml_tree, "type", self.showApply)

        self.boot_row.setXML(self.xml_tree)
        self.address_row.setXML(self.xml_tree)

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "Redirected Device"

    def getDescription(self) -> str:
        return "Redirected USB device"

    def getIconName(self) -> str:
        return "computer-chip-symbolic"
