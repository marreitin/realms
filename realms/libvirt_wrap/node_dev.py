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

import libvirt


class NodeDev:
    """Represents a device on the host node. Most complications
    come from incompatibility of node devices and hostdev-definitions
    in a domain's xml."""

    def __init__(self, connection, dev: libvirt.virNodeDevice):
        self.connection = connection
        self.dev = dev

    def getName(self) -> str:
        """Get the name of the device

        Returns:
            str: Name
        """
        self.connection.isAlive()
        return self.dev.name()

    def getType(self) -> str:
        """Return type of device"""
        self.connection.isAlive()
        tree = self.getETree()
        if (cap := tree.find("capability")) is not None:
            return cap.get("type")
        raise Exception("Error by libvirt, invalid xml.")

    def getDescriptiveName(self) -> str:
        """Attempt to build a descriptive, human-readable name"""
        self.connection.isAlive()

        tree = self.getETree()
        default_name = self.getName()
        name_str = ""

        if (cap := tree.find("capability")) is not None:
            if (prod := cap.find("product")) is not None:
                if prod.text is not None:
                    name_str = prod.text
            if (vend := cap.find("vendor")) is not None:
                if vend.text is not None:
                    name_str += f" ({ vend.text }) "

        if (driver := tree.find("driver")) is not None and not name_str:
            if (name := driver.find("name")) is not None:
                name_str = name.text

        name_str += default_name
        return name_str

    def getETree(self) -> ET.Element:
        """Load data from xml-definition"""
        self.connection.isAlive()
        xml = self.dev.XMLDesc()
        xml_tree = ET.fromstring(xml)
        return xml_tree

    def getXML(self) -> str:
        """Load device xml"""
        self.connection.isAlive()
        return self.dev.XMLDesc()

    def getXMLForDomain(self) -> ET.Element:
        """Get XML that can be inserted into domain xml"""
        self.connection.isAlive()

        tree = self.getETree()
        cap = tree.find("capability")
        dev_type = cap.get("type")
        if dev_type not in ["pci", "usb_device"]:
            raise Exception("Not supported")
        if dev_type == "usb_device":
            dev_type = "usb"

        new_tree = ET.Element("hostdev", attrib={"mode": "subsystem", "type": dev_type})
        source = ET.SubElement(new_tree, "source")
        if dev_type == "usb":
            ET.SubElement(source, "vendor", attrib={"id": cap.find("vendor").get("id")})
            ET.SubElement(
                source, "product", attrib={"id": cap.find("product").get("id")}
            )
        elif dev_type == "pci":
            ET.SubElement(
                source,
                "address",
                attrib={
                    "domain": cap.find("domain").text,
                    "bus": cap.find("bus").text,
                    "slot": cap.find("slot").text,
                    "function": cap.find("function").text,
                },
            )

        return new_tree

    def equalsHostDev(self, hostdev_xml: ET.Element) -> bool:
        """Check if the given hostdev-xml describes this device"""
        tree = self.getETree()
        cap = tree.find("capability")

        dev_type = cap.get("type")
        if dev_type == "usb_device":
            dev_type = "usb"
        if hostdev_xml.get("type") != dev_type:
            return False

        source = hostdev_xml.find("source")
        if source is None:
            return False

        if dev_type == "usb":
            try:
                if cap.find("vendor").get("id") == source.find("vendor").get(
                    "id"
                ) and cap.find("product").get("id") == source.find("product").get("id"):
                    return True
            except:
                pass
        elif dev_type == "pci":
            try:
                address = source.find("address")
                if (
                    cap.find("domain").text == address.get("domain")
                    and cap.find("bus").text == address.get("bus")
                    and cap.find("slot").text == address.get("slot")
                    and cap.find("function").text == address.get("function")
                ):
                    return True
            except:
                pass
        return False
