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
from realms.ui.builders.domain.boot_order_row import BootOrderRow

from .base_device_page import BaseDevicePage


class InterfacePage(BaseDevicePage):
    rows_per_type = {
        "network": [
            "source",
        ],
        "bridge": ["source"],
        "user": ["source", "ipv4", "ipv6"],
        "ethernet": ["script", "downscript", "target"],
        "direct": ["source", "source-direct-mode"],
        "hostdev": ["source-bus-address"],
        "vdpa": ["source"],
        "mcast": ["source-address", "source-port"],
        "server": ["source-address", "source-port"],
        "client": ["source-address", "source-port"],
        "udp": [
            "source-address",
            "source-port",
            "source-local-address",
            "source-local-port",
        ],
        "null": [],
        "vds": [],
        "vhostuser": [
            "source-type",
            "source-path",
            "source-vhostuser-mode",
        ],
    }

    source_attribute_name = {
        "network": "network",
        "bridge": "bridge",
        "user": "dev",
        "direct": "dev",
        "vdpa": "dev",
    }

    nic_models = [
        "virtio",
        "virtio-transitional",
        "virtio-non-transitional",
        "e1000",
        "e1000e",
        "igb",
        "rtl8139",
        "netfront",
        "usb-net",
        "spapr-vlan",
        "lan9118",
        "scm91c111",
        "vlance",
        "vmxnet",
        "vmxnet2",
        "vmxnet3",
        "Am79C970A",
        "Am79C973",
        "82540EM",
        "82545EM",
        "82543GC",
    ]

    def __init__(
        self, parent, xml_tree: ET.Element, use_for_adding=False, can_update=False
    ):
        super().__init__(parent, xml_tree, use_for_adding, can_update)

        self.attr_rows = {}

    def build(self):
        self.group = Adw.PreferencesGroup(title=self.getTitle())
        self.prefs_page.add(self.group)

        self.type_row = BindableComboRow(
            list(self.rows_per_type.keys()), title="Interface type"
        )
        self.group.add(self.type_row)

        self.mac_row = BindableEntryRow(title="MAC address")
        self.group.add(self.mac_row)

        self.model_row = BindableComboRow(self.nic_models, "", title="NIC model")
        self.group.add(self.model_row)

        self.address_row = AddressRow(self.xml_tree, self.showApply, ["pci"])
        self.group.add(self.address_row)
        self.boot_row = BootOrderRow(self.xml_tree, self.showApply)
        self.group.add(self.boot_row)

        # Additional attribute rows, dependent on the network type
        self.attr_rows["source"] = BindableEntryRow(title="Source")
        self.group.add(self.attr_rows["source"])

        self.attr_rows["ipv4"] = BindableEntryRow(title="Network IPv4 address")
        self.group.add(self.attr_rows["ipv4"])

        self.attr_rows["ipv6"] = BindableEntryRow(title="Network IPv6 address")
        self.group.add(self.attr_rows["ipv6"])

        self.attr_rows["script"] = BindableEntryRow(title="Script (Up)")
        self.group.add(self.attr_rows["script"])

        self.attr_rows["downscript"] = BindableEntryRow(title="Script (Down)")
        self.group.add(self.attr_rows["downscript"])

        self.attr_rows["target"] = BindableEntryRow(title="Target device")
        self.group.add(self.attr_rows["target"])

        self.attr_rows["source-direct-mode"] = BindableComboRow(
            ["vepa", "bridge", "private", "passthrough"], title="Source mode"
        )
        self.group.add(self.attr_rows["source-direct-mode"])

        source_address = ET.Element("address")
        self.attr_rows["source-bus-address"] = AddressRow(
            source_address, self.showApply, ["pci"], title="Source bus address"
        )
        self.group.add(self.attr_rows["source-bus-address"])

        self.attr_rows["source-address"] = BindableEntryRow(title="Source address")
        self.group.add(self.attr_rows["source-address"])

        self.attr_rows["source-port"] = BindableEntryRow(title="Source port")
        self.group.add(self.attr_rows["source-port"])

        self.attr_rows["source-local-address"] = BindableEntryRow(
            title="Local source address"
        )
        self.group.add(self.attr_rows["source-local-address"])

        self.attr_rows["source-local-port"] = BindableEntryRow(
            title="Local source port"
        )
        self.group.add(self.attr_rows["source-local-port"])

        self.attr_rows["source-type"] = BindableComboRow(["unix"], title="Source type")
        self.group.add(self.attr_rows["source-type"])

        self.attr_rows["source-path"] = BindableEntryRow(title="Source path")
        self.group.add(self.attr_rows["source-path"])

        self.attr_rows["source-vhostuser-mode"] = BindableComboRow(
            ["server", "client"], title="Source vhost-user mode"
        )
        self.group.add(self.attr_rows["source-vhostuser-mode"])

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

        mac = self.xml_tree.find("mac")
        if mac is None:
            mac = ET.Element("mac")
        self.mac_row.bindAttr(mac, "address", self.onMacChanged)

        model = self.xml_tree.find("model")
        if model is None:
            model = ET.Element("model")
        self.model_row.bindAttr(model, "type", self.onModelChanged)

        self.address_row.setXML(self.xml_tree)
        self.boot_row.setXML(self.xml_tree)

        # Additional attribute rows, dependent on the network type
        for key, row in self.attr_rows.items():
            if key == "source-bus-address":
                elem = ET.Element("address")
                row.setXML(elem)
            else:
                row.unbind()
            row.set_visible(False)

        network_type = self.type_row.getSelectedString()
        for row_name in self.rows_per_type[network_type]:
            row = self.attr_rows[row_name]
            row.set_visible(True)

            if row_name == "source":
                source = self.xml_tree.find("source")
                if source is None:
                    source = ET.SubElement(self.xml_tree, "source")
                row.bindAttr(
                    source, self.source_attribute_name[network_type], self.showApply
                )

            elif row_name == "source-direct-mode":
                source = self.xml_tree.find("source")
                if source is None:
                    source = ET.SubElement(self.xml_tree, "source")
                row.bindAttr(source, "mode", self.showApply)

            elif row_name == "source-bus-address":
                source = self.xml_tree.find("source")
                if source is None:
                    source = ET.SubElement(self.xml_tree, "source")
                address = source.find("address")
                if address is None:
                    address = ET.SubElement(source, "address")
                row.setXML(address)

            elif row_name == "source-address":
                source = self.xml_tree.find("source")
                if source is None:
                    source = ET.SubElement(self.xml_tree, "source")
                row.bindAttr(source, "address", self.showApply)

            elif row_name == "source-port":
                source = self.xml_tree.find("source")
                if source is None:
                    source = ET.SubElement(self.xml_tree, "source")
                row.bindAttr(source, "port", self.showApply)

            elif row_name == "source-local-address":
                source = self.xml_tree.find("source")
                if source is None:
                    source = ET.SubElement(self.xml_tree, "source")
                local = source.find("local")
                if local is None:
                    local = ET.SubElement(source, "local")
                row.bindAttr(local, "address", self.showApply)

            elif row_name == "source-local-port":
                source = self.xml_tree.find("source")
                if source is None:
                    source = ET.SubElement(self.xml_tree, "source")
                local = source.find("local")
                if local is None:
                    local = ET.SubElement(source, "local")
                row.bindAttr(local, "port", self.showApply)

            elif row_name == "source-type":
                source = self.xml_tree.find("source")
                if source is None:
                    source = ET.SubElement(self.xml_tree, "source")
                row.bindAttr(source, "type", self.showApply)

            elif row_name == "source-path":
                source = self.xml_tree.find("source")
                if source is None:
                    source = ET.SubElement(self.xml_tree, "source")
                row.bindAttr(source, "path", self.showApply)

            elif row_name == "source-vhostuser-mode":
                source = self.xml_tree.find("source")
                if source is None:
                    source = ET.SubElement(self.xml_tree, "source")
                row.bindAttr(source, "mode", self.showApply)

            elif row_name == "script":
                script = self.xml_tree.find("script")
                if script is None:
                    script = ET.Element("script")
                row.bindAttr(script, "path", self.onScriptChanged)

            elif row_name == "downscript":
                downscript = self.xml_tree.find("downscript")
                if downscript is None:
                    downscript = ET.Element("downscript")
                row.bindAttr(downscript, "path", self.onDownscriptChanged)

            elif row_name == "target":
                target = self.xml_tree.find("target")
                if target is None:
                    target = ET.Element("target")
                row.bindAttr(target, "dev", self.onTargetDevChanged)

            elif row_name == "ipv4":
                all_ip = self.xml_tree.findall("ip")
                ipv4 = None
                for el in all_ip:
                    if el.family == "ipv4":
                        ipv4 = el
                if ipv4 is None:
                    ipv4 = ET.Element("ip", attrib={"family": "ipv4"})
                row.bindAttr(ipv4, "address", self.onIPV4Changed)

            elif row_name == "ipv6":
                all_ip = self.xml_tree.findall("ip")
                ipv6 = None
                for el in all_ip:
                    if el.family == "ipv6":
                        ipv6 = el
                if ipv6 is None:
                    ipv6 = ET.Element("ip", attrib={"family": "ipv6"})
                row.bindAttr(ipv6, "address", self.onIPV6Changed)

        if network_type == "vhostuser":
            self.model_row.setSelectedString(
                "virtio"
            )  # Required by https://libvirt.org/formatdomain.html#vhost-user-interface
            self.model_row.set_sensitive(False)
        else:
            self.model_row.set_sensitive(True)

    def onTypeChanged(self):
        self.updateData()
        self.showApply()

    def onMacChanged(self):
        mac = self.xml_tree.find("mac")
        if self.mac_row.get_text() == "":
            if mac is not None:
                self.xml_tree.remove(self.mac_row.elem)
        else:
            if mac is None:
                self.xml_tree.append(self.mac_row.elem)
        self.showApply()

    def onModelChanged(self):
        model = self.xml_tree.find("model")
        if self.model_row.getSelectedString() == "":
            if model is not None:
                self.xml_tree.remove(self.model_row.elem)
        else:
            if model is None:
                self.xml_tree.append(self.model_row.elem)
        self.showApply()

    def onIPV4Changed(self):
        all_ip = self.xml_tree.findall("ip")
        ipv4 = None
        for el in all_ip:
            if el.family == "ipv4":
                ipv4 = el

        if ipv4 is None:
            ipv4 = ET.Element("ip", attrib={"family": "ipv4"})
        if self.attr_rows["ipv4"].getSelectedString() == "":
            if ipv4 is not None:
                self.xml_tree.remove(self.attr_rows["ipv4"].elem)
        else:
            if ipv4 is None:
                self.xml_tree.append(self.attr_rows["ipv4"].elem)
        self.showApply()

    def onIPV6Changed(self):
        all_ip = self.xml_tree.findall("ip")
        ipv6 = None
        for el in all_ip:
            if el.family == "ipv6":
                ipv6 = el

        if ipv6 is None:
            ipv6 = ET.Element("ip", attrib={"family": "ipv6"})
        if self.attr_rows["ipv6"].getSelectedString() == "":
            if ipv6 is not None:
                self.xml_tree.remove(self.attr_rows["ipv6"].elem)
        else:
            if ipv6 is None:
                self.xml_tree.append(self.attr_rows["ipv6"].elem)
        self.showApply()

    def onScriptChanged(self):
        script = self.xml_tree.findall("script")
        if script is None:
            script = ET.Element("script")
        if self.attr_rows["script"].getSelectedString() == "":
            if script is not None:
                self.xml_tree.remove(self.attr_rows["script"].elem)
        else:
            if script is None:
                self.xml_tree.append(self.attr_rows["script"].elem)
        self.showApply()

    def onDownscriptChanged(self):
        downscript = self.xml_tree.findall("downscript")
        if downscript is None:
            downscript = ET.Element("downscript")
        if self.attr_rows["downscript"].getSelectedString() == "":
            if downscript is not None:
                self.xml_tree.remove(self.attr_rows["downscript"].elem)
        else:
            if downscript is None:
                self.xml_tree.append(self.attr_rows["downscript"].elem)
        self.showApply()

    def onTargetDevChanged(self):
        target = self.xml_tree.findall("target")
        if target is None:
            target = ET.Element("target")
        if self.attr_rows["target"].getSelectedString() == "":
            if target is not None:
                self.xml_tree.remove(self.attr_rows["target"].elem)
        else:
            if target is None:
                self.xml_tree.append(self.attr_rows["target"].elem)
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "Network interface"

    def getDescription(self) -> str:
        return "Virtual network interface"

    def getIconName(self) -> str:
        return "network-server-symbolic"
