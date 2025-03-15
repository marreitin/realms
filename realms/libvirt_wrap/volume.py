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

from .constants import *
from .pool import Pool


def getVolumeFromName(pool: Pool, name: str):
    """Find the volume by the given name in the pool

    Args:
        pool (Pool): Pool wrapper
        name (str): Volume name

    Returns:
        _type_: New volume wrapper
    """
    vir_vol = pool.pool.storageVolLookupByName(name)
    return Volume(pool, vir_vol)


class Volume:
    """Simple class to represent storage volumes. Since there are no events for volumes,
    this class is much more slim than other wrappers.
    """

    def __init__(self, pool: Pool, volume: libvirt.virStorageVol):
        self.pool = pool
        self.volume = volume

    ############################################
    # Actions
    ############################################

    def delete(self):
        """Delete this volume"""
        self.pool.deleteVolume(self.volume)

    def wipe(self):
        """Wipe this volume."""
        self.volume.wipe()

    def clone(self, new_name: str):
        """Clone this volume.

        Args:
            new_name (str): Name of the new volume
        """
        tree = self.getETree()
        name = tree.find("name")
        name.text = new_name

        xml = ET.tostring(tree, encoding="unicode")

        new_vol = self.pool.pool.createXMLFrom(
            xml, self.volume, libvirt.VIR_STORAGE_VOL_CREATE_PREALLOC_METADATA
        )

        return Volume(self.pool, new_vol)

    ############################################
    # Small getters
    ############################################
    def getETree(self) -> ET.Element:
        """Load XML and parse it

        Returns:
            ET.Element: XML tree
        """
        self.pool.connection.isAlive()
        xml = self.volume.XMLDesc()
        xml_tree = ET.fromstring(xml)
        return xml_tree

    def getName(self) -> str:
        self.pool.connection.isAlive()
        return self.volume.name()

    def getUUID(self) -> str:
        self.pool.connection.isAlive()
        return self.volume.UUIDString()

    def getType(self) -> str:
        """Get the type of this volume (how it actually is represented)

        Returns:
            str: Name of the type
        """
        self.pool.connection.isAlive()
        info = self.volume.info()
        vol_type = info[0]

        types = ["file", "block", "dir", "network", "netdir", "ploop"]

        return types[vol_type]

    def getCapacity(self) -> int:
        """Get volume capacity

        Returns:
            int: Capacity in bytes
        """
        self.pool.connection.isAlive()
        info = self.volume.info()
        return info[1]

    def getAllocation(self) -> int:
        """Get volume allocation

        Returns:
            int: Allocated bytes
        """
        self.pool.connection.isAlive()
        info = self.volume.info()
        return info[2]

    def getXML(self) -> str:
        """Get XML description

        Returns:
            str: description
        """
        self.pool.connection.isAlive()
        return self.volume.XMLDesc()

    ############################################
    # Small setters
    ############################################

    def setCapacity(self, new_capacity: int) -> None:
        """Set new capacity

        Args:
            new_capacity (int): New capacity in bytes
        """
        self.volume.resize(new_capacity)
