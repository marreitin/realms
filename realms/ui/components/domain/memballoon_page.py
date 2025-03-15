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

from realms.ui.components.bindable_entries import BindableComboRow, BindableSwitchRow
from realms.ui.components.common import deleteRow
from realms.ui.components.domain.address_row import AddressRow

from .base_device_page import BaseDevicePage


class MemballoonPage(BaseDevicePage):
    def __init__(
        self, parent, xml_tree: ET.Element, use_for_adding=False, can_update=False
    ):
        super().__init__(parent, xml_tree, use_for_adding, can_update)

    def build(self):
        self.group = Adw.PreferencesGroup()
        self.prefs_page.add(self.group)

        self.model_row = BindableComboRow(
            ["none", "virtio", "virtio-transitional", "virtio-non-transitional", "xen"],
            title="Model",
        )
        self.group.add(self.model_row)

        self.autodeflate_row = BindableSwitchRow("on", "off", title="Autodeflate")
        self.group.add(self.autodeflate_row.getWidget())

        self.free_page_reporting_row = BindableSwitchRow(
            "on", "off", title="Free page reporting"
        )
        self.group.add(self.free_page_reporting_row.getWidget())

        self.address_row = AddressRow(self.xml_tree, self.showApply)
        self.group.add(self.address_row)

        if not self.use_for_adding:
            self.group.add(deleteRow(self.deleteDevice))

        self.updateData()

    def updateData(self):
        self.group.set_title(self.getTitle())

        self.model_row.bindAttr(self.xml_tree, "model", self.showApply)

        self.autodeflate_row.bindAttr(self.xml_tree, "autodeflate", self.showApply)

        self.free_page_reporting_row.bindAttr(
            self.xml_tree, "freePageReporting", self.showApply
        )

        self.address_row.setXML(self.xml_tree)

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return self.xml_tree.tag.capitalize()

    def getDescription(self) -> str:
        return "Memory balloon"

    def getIconName(self) -> str:
        return "memory-symbolic"
