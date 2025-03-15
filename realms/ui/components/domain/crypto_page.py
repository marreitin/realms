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

from realms.ui.components.bindable_entries import BindableComboRow, BindableSpinRow
from realms.ui.components.common import deleteRow

from .base_device_page import BaseDevicePage


class CryptoPage(BaseDevicePage):
    """Page for crypto device."""

    def __init__(
        self, parent, xml_tree: ET.Element, use_for_adding=False, can_update=False
    ):
        super().__init__(parent, xml_tree, use_for_adding, can_update)

    def build(self):
        self.group = Adw.PreferencesGroup()
        self.prefs_page.add(self.group)

        self.backend_model_row = BindableComboRow(
            ["builtin", "lkcf"], title="Backend model"
        )
        self.group.add(self.backend_model_row)

        self.backend_queues_row = BindableSpinRow(
            lambda i: str(int(i)),
            title="Queues",
            adjustment=Gtk.Adjustment(lower=1, step_increment=1, upper=32),
        )
        self.group.add(self.backend_queues_row.getWidget())

        if not self.use_for_adding:
            self.group.add(deleteRow(self.deleteDevice))

        self.updateData()

    def updateData(self):
        self.group.set_title(self.getTitle())

        # Set required attributes if they don't exist yet
        if self.xml_tree.get("model") is None:
            self.xml_tree.set("model", "virtio")
            self.showApply()

        if self.xml_tree.get("type") is None:
            self.xml_tree.set("type", "qemu")
            self.showApply()

        backend = self.xml_tree.find("backend")
        if backend is None:
            if self.xml_tree.get("type") == "qemu":
                backend = ET.SubElement(self.xml_tree, "backend")
            else:
                backend = ET.Element("backend")

        self.backend_model_row.bindAttr(backend, "model", self.__onBackendChanged__)
        self.backend_queues_row.bindAttr(backend, "queues", self.__onBackendChanged__)

    def __onBackendChanged__(self):
        backend = self.xml_tree.find("backend")
        if backend is None:
            self.xml_tree.append(self.backend_model_row.elem)
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return self.xml_tree.tag.capitalize()

    def getDescription(self) -> str:
        return "Crypto device"

    def getIconName(self) -> str:
        return "computer-chip-symbolic"
