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

from realms.helpers import asyncJob

from .connection import Connection
from .constants import *
from .event_manager import EventManager


def getPoolFromName(conn: Connection, name: str):
    """Find a pool by the given name on the host.

    Args:
        conn (Connection): Connection wrapper
        name (str): Pool name

    Returns:
        _type_: Pool wrapper.
    """
    vir_pool = conn.__connection__.storagePoolLookupByName(name)
    return Pool(conn, vir_pool)


class Pool(EventManager):
    def __init__(self, connection: Connection, pool: libvirt.virStoragePool):
        super().__init__()
        self.event_callbacks = []

        self.connection = connection
        self.pool = pool

        self.connection.isAlive()
        self.pool_capabilities = self.connection.getPoolCapabilities()

        self.connection.registerCallback(self.onConnectionEvent)

    ############################################
    # Callbacks
    ############################################

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id):
        # Filter unwanted stuff
        if (
            type_id in [CALLBACK_TYPE_POOL_LIFECYCLE, CALLBACK_TYPE_POOL_GENERIC]
            and event_id not in [POOL_EVENT_VOLUME_ADDED, POOL_EVENT_VOLUME_DELETED]
            and obj.UUIDString() != self.pool.UUIDString()
        ):
            return
        if type_id not in [
            CALLBACK_TYPE_CONNECTION_GENERIC,
            CALLBACK_TYPE_POOL_LIFECYCLE,
            CALLBACK_TYPE_POOL_GENERIC,
        ]:
            return

        if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            # What happens if we disconnect or the connection gets deleted?
            # Only unsubscribe for connection event multiplexer, other objects
            # unsubscribe by themselves
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.connection.unregisterCallback(self.onConnectionEvent)

        self.sendEvent(conn, obj, type_id, event_id, detail_id)

    ############################################
    # Actions
    ############################################

    def start(self) -> None:
        self.connection.isAlive()
        self.pool.create()

    def stop(self) -> None:
        self.connection.isAlive()
        self.pool.destroy()

    def deletePool(self) -> None:
        self.connection.isAlive()
        self.connection.sendEvent(
            self.connection,
            self.pool,
            CALLBACK_TYPE_POOL_GENERIC,
            POOL_EVENT_DELETED,
            0,
        )

        # Check if any callbacks are still there
        if len(self.event_callbacks) > 0:
            raise Exception("Something didn't unregister properly")

        if self.isActive():
            self.pool.destroy()
        self.pool.undefine()

    def update(self, new_tree: ET.Element):
        """Update the pool with the given xml tree.

        Args:
            new_tree (ET.Element): XML Tree for new pool definition
        """
        self.connection.isAlive()

        xml = ET.tostring(new_tree, encoding="unicode")
        print(xml)
        self.updateDefinition(xml)

    def updateDefinition(self, xml: str):
        self.connection.isAlive()

        new_pool = self.connection.__connection__.storagePoolDefineXML(xml)
        self.pool = new_pool

    def listVolumes(self, ready_cb, refresh=False) -> None:
        self.connection.isAlive()

        def getVolumes() -> list[libvirt.virStorageVol]:
            if refresh:
                self.pool.refresh()
            vir_volumes = self.pool.listAllVolumes(0)
            return vir_volumes

        asyncJob(getVolumes, [], ready_cb)

    def addVolume(self, xml_tree: ET.Element) -> libvirt.virStorageVol:
        """Create a new volume

        Args:
            xml_tree (ET.Element): Volume XML Tree
        """
        self.connection.isAlive()

        xml = ET.tostring(xml_tree, encoding="unicode")
        return self.addVolumeXML(xml)

    def addVolumeXML(self, xml: str) -> libvirt.virStorageVol:
        """Create a new volume

        Args:
            xml (str): Volume XML
        """
        self.connection.isAlive()

        vir_volume = self.pool.createXML(xml)

        self.connection.sendEvent(
            self.connection,
            vir_volume,
            CALLBACK_TYPE_POOL_GENERIC,
            POOL_EVENT_VOLUME_ADDED,
            0,
        )

        return vir_volume

    def deleteVolume(self, volume: libvirt.virStorageVol) -> None:
        """Delete this volume

        Args:
            volume (libvirt.virStorageVol): Volume to delete
        """
        self.connection.isAlive()

        volume.delete()

        self.connection.sendEvent(
            self.connection,
            volume,
            CALLBACK_TYPE_POOL_GENERIC,
            POOL_EVENT_VOLUME_DELETED,
            0,
        )

    ############################################
    # Small getters
    ############################################
    def getETree(self):
        """Load data from xml-definition"""
        self.connection.isAlive()
        xml = self.pool.XMLDesc()
        xml_tree = ET.fromstring(xml)
        return xml_tree

    def getDisplayName(self) -> str:
        self.connection.isAlive()
        return self.pool.name()

    def getUUID(self) -> str:
        self.connection.isAlive()
        return self.pool.UUIDString()

    def getCapacity(self) -> int:
        self.connection.isAlive()
        info = self.pool.info()
        return info[1]

    def getAllocation(self) -> int:
        self.connection.isAlive()
        info = self.pool.info()
        return info[2]

    def getAvailable(self) -> int:
        self.connection.isAlive()
        info = self.pool.info()
        return info[3]

    def isPersistent(self) -> bool:
        self.connection.isAlive()
        return self.pool.isPersistent()

    def isActive(self) -> bool:
        self.connection.isAlive()
        return self.pool.isActive()

    def getXML(self) -> str:
        self.connection.isAlive()
        return self.pool.XMLDesc()

    def getAutostart(self):
        self.connection.isAlive()
        return self.pool.autostart()

    ############################################
    # Small setters
    ############################################
    def setAutostart(self, autostart: bool):
        self.connection.isAlive()
        self.pool.setAutostart(autostart)
