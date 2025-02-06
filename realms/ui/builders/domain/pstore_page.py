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

from realms.helpers import bytesToString, stringToBytes
from realms.ui.builders.bindable_entries import BindableComboRow, BindableEntryRow
from realms.ui.builders.common import iconButton
from realms.ui.builders.domain.address_row import AddressRow

from .base_device_page import BaseDevicePage


class PstorePage(BaseDevicePage):
    def build(self):
        self.group = Adw.PreferencesGroup()
        self.prefs_page.add(self.group)

        self.backend_row = BindableComboRow(["acpi-erst"], title="Backend")
        self.group.add(self.backend_row)

        self.size_row = BindableEntryRow(title="Log store size")
        self.group.add(self.size_row)

        self.path_row = BindableEntryRow(title="Path")
        self.group.add(self.path_row)

        self.address_row = AddressRow(self.xml_tree, self.showApply)
        self.group.add(self.address_row)

        if not self.use_for_adding:
            delete_row = Adw.ActionRow()
            self.group.add(delete_row)
            self.delete_btn = iconButton(
                "Remove", "user-trash-symbolic", self.deleteDevice, css_classes=["flat"]
            )
            delete_row.add_prefix(self.delete_btn)

        self.updateData()

    def updateData(self):
        self.group.set_title(self.getTitle())

        size = self.xml_tree.find("size")
        if size is None:
            size = ET.SubElement(self.xml_tree, "size", attrib={"unit": "B"})
        self.size_row.bindText(
            size,
            self.showApply,
            lambda t: str(stringToBytes(t, "KiB")),
            lambda t: bytesToString(t, "KiB"),
        )

        path = self.xml_tree.find("path")
        if path is None:
            path = ET.Element("path")
        self.path_row.bindText(path, self.onPathChanged)

        self.address_row.setXML(self.xml_tree)

    def onPathChanged(self):
        path = self.xml_tree.find("path")
        if self.path_row.get_text() == "":
            if path is not None:
                self.xml_tree.remove(path)
        else:
            if path is None:
                self.xml_tree.add(self.path_row.elem)
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return self.xml_tree.tag.capitalize()

    def getDescription(self) -> str:
        return "Pstore"

    def getIconName(self) -> str:
        return "archive-symbolic"
