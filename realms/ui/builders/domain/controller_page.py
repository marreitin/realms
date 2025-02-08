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

from realms.ui.builders import iconButton
from realms.ui.builders.bindable_entries import BindableComboRow, BindableEntryRow
from realms.ui.builders.domain.address_row import AddressRow

from .base_device_page import BaseDevicePage


class ControllerPage(BaseDevicePage):
    """Page for bus controller."""

    def build(self):
        self.group = Adw.PreferencesGroup(
            title=self.getTitle(), description="Bus controller"
        )
        self.prefs_page.add(self.group)

        self.type_row = BindableComboRow(
            ["ide", "fdc", "scsi", "sata", "usb", "ccid", "virtio-serial", "pci"],
            title="Controller type",
        )
        self.group.add(self.type_row)

        self.index_row = BindableEntryRow(title="Controller index")
        self.group.add(self.index_row)

        self.address_row = AddressRow(self.xml_tree, self.showApply)
        self.group.add(self.address_row)

        if not self.use_for_adding:
            delete_row = Adw.ActionRow()
            self.group.add(delete_row)
            self.delete_btn = iconButton(
                "Remove", "user-trash-symbolic", self.deleteDevice, css_classes=["flat"]
            )
            delete_row.add_prefix(self.delete_btn)

        self.attribute_rows = {}
        self.additional_attributes = {
            "pci": ["model"],
            "virtio-serial": ["ports", "vectors", "model"],
            "scsi": ["model"],
            "usb": ["model"],
            "ide": ["model"],
            "xenbus": ["maxGrantFrames"],
        }
        self.allowed_models = {
            "pci": [
                "pci-root",
                "pcie-root",
                "pcie-root-port",
                "pcie-switch-upstream-port",
                "pcie-switch-downstream-port",
            ],
            "virtio-serial": [
                "virtio",
                "virtio-transitional",
                "virtio-non-transitional",
            ],
            "scsi": [
                "am53c974",
                "auto",
                "buslogic",
                "dc390",
                "ibmvscsi",
                "lsilogic",
                "lsisas1068",
                "lsisas1078",
                "ncr53c90",
                "virtio-non-transitional",
                "virtio-scsi",
                "virtio-transitional",
                "vmpvscsi",
            ],
            "usb": [
                "ehci",
                "ich9-ehci1",
                "ich9-uhci1",
                "ich9-uhci2",
                "ich9-uhci3",
                "nex-xhci",
                "none",
                "pci-ohci",
                "piix3-uhci",
                "piix4-uhci",
                "qemu-xhci",
                "qusb1",
                "qusb2",
                "vt82c686b-uhci",
            ],
            "ide": [
                "ich6",
                "piix3",
                "piix4",
            ],
        }

        self.options_group = Adw.PreferencesGroup(title="Additional options")
        self.prefs_page.add(self.options_group)

        for attribute in ["ports", "vectors", "maxGrantFrames"]:
            row = BindableEntryRow(title=attribute.capitalize())
            self.options_group.add(row)
            self.attribute_rows[attribute] = row

        model_row = BindableComboRow([""], "", title="Model")
        self.options_group.add(model_row)
        self.attribute_rows["model"] = model_row

        self.updateData()

    def updateData(self):
        self.group.set_title(self.getTitle())
        self.type_row.bindAttr(self.xml_tree, "type", self.__onTypeChanged__)
        self.index_row.bindAttr(self.xml_tree, "index", self.showApply)
        self.address_row.setXML(self.xml_tree)

        for row in self.attribute_rows.values():
            row.unbind()
            row.set_visible(False)

        controller_type = self.type_row.getSelectedString()
        if controller_type not in self.additional_attributes:
            self.options_group.set_visible(False)
            return
        self.options_group.set_visible(True)
        attrs = self.additional_attributes[controller_type]
        for attr in attrs:
            row = self.attribute_rows[attr]
            row.set_visible(True)
            if attr == "model":
                continue
            row.set_visible(True)
            row.bindAttr(self.xml_tree, attr, self.showApply)

        if controller_type in self.allowed_models:
            row = self.attribute_rows["model"]
            row.setSelection(self.allowed_models[controller_type])
            row.bindAttr(self.xml_tree, "model", self.showApply)

    def __onTypeChanged__(self):
        self.xml_tree.clear()
        self.xml_tree.set("type", self.type_row.getSelectedString())
        self.updateData()
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return self.xml_tree.get("type", "").upper() + " Controller"

    def getDescription(self) -> str:
        return "Bus Controller"

    def getIconName(self) -> str:
        return "pci-card-symbolic"
