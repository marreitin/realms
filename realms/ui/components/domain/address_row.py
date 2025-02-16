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

from realms.ui.components.bindable_entries import (
    BindableComboRow,
    BindableEntryRow,
    BindableSwitchRow,
)


class AddressRow(Adw.ExpanderRow):
    """Row to set the <address> element of devices.
    Used in almost all of them."""

    def __init__(
        self,
        device_xml: ET.Element,
        show_apply_cb: callable,
        available_bus_types_override: list[str] = None,
        **kwargs
    ):
        if "title" not in kwargs:
            super().__init__(
                title="Explicit device address",
                subtitle="Will be assigned by libvirt if ommited",
                show_enable_switch=True,
                **kwargs
            )
        else:
            super().__init__(show_enable_switch=True, **kwargs)

        self.device_xml = device_xml
        self.show_apply_cb = show_apply_cb

        self.available_types = [
            "ccid",
            "ccw",
            "drive",
            "isa",
            "pci",
            "spapr-vio",
            "usb",
            "unassigned",
            "virtio-mmio",
            "virtio-serial",
        ]
        if available_bus_types_override is not None:
            self.available_types = available_bus_types_override

        self.type_row = BindableComboRow(
            self.available_types,
            title="Address type",
        )
        self.add_row(self.type_row)

        self.visible_rows_per_type = {
            "pci": ["domain", "bus", "slot", "function", "multifunction"],
            "drive": ["controller", "bus", "target", "unit"],
            "ccid": ["bus", "slot"],
            "usb": ["bus", "port"],
            "spapr-vio": ["reg"],
            "ccw": ["cssid", "ssid", "devno"],
            "virtio-mmio": None,
            "virtio-serial": ["controller", "bus", "slot"],
            "isa": ["iobase", "irq"],
            "unassigned": None,
        }
        self.attr_rows = {}

        for item in [
            "domain",
            "controller",
            "bus",
            "target",
            "slot",
            "unit",
            "function",
            "port",
            "reg",
            "cssid",
            "ssid",
            "devno",
            "iobase",
            "irq",
        ]:
            row = BindableEntryRow(title=item.capitalize())
            self.attr_rows[item] = row
            self.add_row(row)

        self.multifunction_row = BindableSwitchRow(
            "yes", "no", title="Multifunction", subtitle="Set the multifunction bit"
        )
        self.attr_rows["multifunction"] = self.multifunction_row
        self.add_row(self.multifunction_row.switch_row)

        self.connect("notify::enable-expansion", self.__onSwitchChanged__)

        self.updateData()

    def updateData(self):
        """Refresh."""
        self.disconnect_by_func(self.__onSwitchChanged__)
        address = self.device_xml.find("address")
        if address is None:
            self.set_enable_expansion(False)
            self.set_expanded(False)
        else:
            self.set_enable_expansion(True)
            self.type_row.bindAttr(address, "type", self.__onTypeChanged__)
            self.bindRows()
        self.connect("notify::enable-expansion", self.__onSwitchChanged__)

    def bindRows(self):
        """Bind this row to xml."""
        for row in self.attr_rows.values():
            row.unbind()
            row.set_visible(False)

        address = self.device_xml.find("address")
        address_type = self.type_row.getSelectedString()
        attributes = self.visible_rows_per_type[address_type]
        if attributes is None:
            return
        for attribute in attributes:
            row = self.attr_rows[attribute]
            row.bindAttr(address, attribute, self.show_apply_cb)
            row.set_visible(True)

    def setXML(self, xml_tree: ET.Element):
        """Update the xml. The row will then take appropriate action
        to react to the changes."""
        self.device_xml = xml_tree
        self.updateData()

    def __onTypeChanged__(self, *_):
        """The address type changed."""
        t = self.type_row.getSelectedString()
        address = self.device_xml.find("address")
        address.clear()
        address.set("type", t)
        self.updateData()
        self.show_apply_cb()

    def __onSwitchChanged__(self, row, *_):
        """The "use explicit address"-switch changed."""
        address = self.device_xml.find("address")
        if self.get_enable_expansion():
            self.set_expanded(True)
            if address is None:
                address = ET.SubElement(self.device_xml, "address")
            self.updateData()
        else:
            if address is not None:
                self.device_xml.remove(address)
        self.show_apply_cb()
