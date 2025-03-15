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
from realms.ui.components.domain.address_row import AddressRow

from .base_device_page import BaseDevicePage


class PanicPage(BaseDevicePage):
    def build(self):
        self.group = Adw.PreferencesGroup(
            title="Panic device",
            description="Enable libvirt to receive panic notifications",
        )
        self.prefs_page.add(self.group)

        self.model_row = BindableComboRow(
            ["isa", "pseries", "hyperv", "s390", "pvpanic"],
            "",
            title="Panic device model",
        )
        self.group.add(self.model_row)

        self.address_row = AddressRow(self.xml_tree, self.showApply)
        self.group.add(self.address_row)

        if not self.use_for_adding:
            self.group.add(deleteRow(self.deleteDevice))

        self.updateData()

    def updateData(self):
        self.model_row.bindAttr(self.xml_tree, "model", self.onModelChanged)

        model = self.model_row.getSelectedString()
        if model in ["s390", "pseries", "hyperv"]:
            self.address_row.set_visible(False)
        else:
            self.address_row.set_visible(True)
            self.address_row.setXML(self.xml_tree)

    def onModelChanged(self):
        self.xml_tree.clear()
        self.xml_tree.set("model", self.model_row.getSelectedString())
        self.updateData()
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "Panic Device"

    def getDescription(self) -> str:
        return "Receive panic notifications"

    def getIconName(self) -> str:
        return "skull-symbolic"
