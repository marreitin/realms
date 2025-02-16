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

from realms.ui.components import iconButton
from realms.ui.components.bindable_entries import BindableComboRow
from realms.ui.components.domain.address_row import AddressRow

from .base_device_page import BaseDevicePage


class RNGPage(BaseDevicePage):
    """Page for random number generator."""

    def build(self):
        self.group = Adw.PreferencesGroup(
            title="Random number generator",
            description="Give domain access to a source of randomness",
        )
        self.prefs_page.add(self.group)

        self.domain_caps = self.parent.domain.connection.getDomainCapabilities()

        self.model_row = BindableComboRow(
            self.domain_caps.devices["rng"]["model"],
            title="RNG model",
        )
        self.group.add(self.model_row)

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
        self.model_row.bindAttr(self.xml_tree, "model", self.showApply)
        self.address_row.setXML(self.xml_tree)

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "Random Number Generator"

    def getDescription(self) -> str:
        return "Random number generator"

    def getIconName(self) -> str:
        return "dice3-symbolic"
