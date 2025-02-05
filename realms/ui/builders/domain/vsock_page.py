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

from realms.ui.builders import iconButton
from realms.ui.builders.bindable_entries import (
    BindableComboRow,
    BindableSpinRow,
    BindableSwitchRow,
)

from .base_device_page import BaseDevicePage


class VSockPage(BaseDevicePage):
    def build(self):
        self.group = Adw.PreferencesGroup(
            title="Vsock",
        )
        self.prefs_page.add(self.group)

        self.model_row = BindableComboRow(
            ["virtio", "virtio-transitional", "virtio-non-transitional"], title="Model"
        )
        self.group.add(self.model_row)

        self.auto_cpi_row = BindableSwitchRow("yes", "no", True, title="Automatic CPI")
        self.group.add(self.auto_cpi_row.getWidget())

        self.address_row = BindableSpinRow(
            lambda x: str(int(x)),
            title="CID",
            adjustment=Gtk.Adjustment(lower=1, upper=4294967296, step_increment=1),
        )
        self.group.add(self.address_row.getWidget())

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

        cid = self.xml_tree.find("cid")
        if cid is None:
            cid = ET.SubElement(self.xml_tree, "cid")
        self.auto_cpi_row.bindAttr(cid, "auto", self.showApply)

        self.address_row.bindAttr(cid, "address", self.showApply)

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return self.xml_tree.tag.capitalize()

    def onCIDChanged(self):
        self.showApply()

    def getDescription(self) -> str:
        return "Virtual socket"

    def getIconName(self) -> str:
        return "horizontal-arrows-symbolic"
