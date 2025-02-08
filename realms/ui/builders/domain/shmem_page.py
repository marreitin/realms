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
from realms.ui.builders import iconButton
from realms.ui.builders.bindable_entries import BindableComboRow, BindableEntryRow
from realms.ui.builders.domain.address_row import AddressRow

from .base_device_page import BaseDevicePage


class SHMemPage(BaseDevicePage):
    def build(self):
        self.group = Adw.PreferencesGroup()
        self.prefs_page.add(self.group)

        self.name_row = BindableEntryRow(title="Name")
        self.group.add(self.name_row)

        self.role_row = BindableComboRow(["peer", "master"], "", title="Role")
        self.group.add(self.role_row)

        self.model_row = BindableComboRow(
            ["ivshmem", "ivshmem-plain", "ivshmem-doorbell"], "", title="Model"
        )
        self.group.add(self.model_row)

        self.size_row = BindableEntryRow(title="Size")
        self.group.add(self.size_row)

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

        self.name_row.bindAttr(self.xml_tree, "name", self.showApply)

        self.role_row.bindAttr(self.xml_tree, "role", self.showApply)

        model = self.xml_tree.find("model")
        if model is None:
            model = ET.Element("model")
        self.model_row.bindAttr(model, "type", self.onModelChanged)

        size = self.xml_tree.find("size")
        if size is None:
            size = ET.Element("size", attrib={"unit": "M"})
        self.size_row.bindText(
            size,
            self.onSizeChanged,
            lambda t: str(stringToBytes(t, size.get("unit", "M"))),
            lambda t: bytesToString(t, size.get("unit", "M")),
        )

    def onModelChanged(self):
        model = self.xml_tree.find("model")
        if self.model_row.getSelectedString() == "":
            if model is not None:
                self.xml_tree.remove(model)
        else:
            if model is None:
                self.xml_tree.append(self.model_row.elem)
        self.showApply()

    def onSizeChanged(self):
        size = self.xml_tree.find("size")
        if self.size_row.getWidget().get_text() == "":
            if size is not None:
                self.xml_tree.remove(size)
        else:
            if size is None:
                self.xml_tree.append(self.size_row.elem)
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "Shared Memory"

    def getDescription(self) -> str:
        return "Shared memory"

    def getIconName(self) -> str:
        return "memory-symbolic"
