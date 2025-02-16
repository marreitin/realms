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

from realms.helpers import asyncJob
from realms.ui.components import iconButton
from realms.ui.components.bindable_entries import BindableComboRow

from .base_device_page import BaseDevicePage
from .boot_order_row import BootOrderRow


class HostdevPage(BaseDevicePage):
    def build(self):
        self.group = Adw.PreferencesGroup()
        self.prefs_page.add(self.group)

        self.type_row = BindableComboRow(["usb_device", "pci"], title="Device type")
        self.group.add(self.type_row)

        self.dev_row = Adw.ComboRow(title="Device", sensitive=False)
        self.dev_row.connect("notify::selected", self.onDeviceChanged)
        self.devices = []

        self.group.add(self.dev_row)

        self.boot_row = BootOrderRow(self.xml_tree, self.showApply)
        self.group.add(self.boot_row)

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
        self.type_row.bindAttr(self.xml_tree, "type", self.onTypeChanged)

        self.boot_row.setXML(self.xml_tree)

        self.onTypeChanged(True)

    def onTypeChanged(self, first_run=False):
        def onDevsListed(node_devs: list):
            self.dev_row.set_sensitive(True)
            self.dev_row.set_title("Device")
            search_type = self.type_row.getSelectedString()
            if search_type == "usb":
                search_type = "usb_device"
            devices = [d for d in node_devs if d.getType() == search_type]

            names = [d.getDescriptiveName() for d in devices]
            self.dev_row.set_model(Gtk.StringList(strings=names))

            if first_run:
                device = None
                for dev in devices:
                    if dev.equalsHostDev(self.xml_tree):
                        device = dev
                        break
                if device is not None:
                    self.dev_row.set_selected(devices.index(device))

            self.devices = devices

        self.devices.clear()
        self.dev_row.set_sensitive(False)
        self.dev_row.set_title("Loading devices...")

        self.dev_row.set_model(Gtk.StringList(strings=[]))
        asyncJob(self.parent.domain.connection.listNodeDevices, [], onDevsListed)

    def onDeviceChanged(self, combo_row, *_):
        if not self.devices:
            return
        device = self.devices[self.dev_row.get_selected()]
        dev_tree: ET.Element = device.getXMLForDomain()
        self.xml_tree.clear()
        self.xml_tree.attrib = dev_tree.attrib
        self.xml_tree.append(dev_tree.find("source"))
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "Host Device"

    def getDescription(self) -> str:
        return "Forwarded host device"

    def getIconName(self) -> str:
        return "computer-chip-symbolic"
