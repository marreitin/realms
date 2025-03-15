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

from realms.helpers.async_jobs import asyncJob

from .connection import Connection
from .constants import *
from .event_manager import EventManager


class Network(EventManager):
    def __init__(self, connection: Connection, network: libvirt.virNetwork):
        super().__init__()
        self.event_callbacks = []

        self.connection = connection
        self.connection.isAlive()
        self.connection.registerCallback(self.onConnectionEvent)
        self.network = network

    ############################################
    # Callbacks
    ############################################

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id):
        # Filter unwanted stuff
        if (
            type_id in [CALLBACK_TYPE_NETWORK_LIFECYCLE, CALLBACK_TYPE_NETWORK_GENERIC]
            and obj.UUIDString() != self.network.UUIDString()
        ):
            return
        if type_id not in [
            CALLBACK_TYPE_CONNECTION_GENERIC,
            CALLBACK_TYPE_NETWORK_GENERIC,
            CALLBACK_TYPE_NETWORK_LIFECYCLE,
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

    def update(self, new_tree: ET.Element):
        """Update the network with the given xml tree.

        Args:
            new_tree (ET.Element): XML Tree for new network definition
        """
        self.connection.isAlive()

        xml = ET.tostring(new_tree, encoding="unicode")
        self.updateDefinition(xml)

    def updateDefinition(self, xml: str):
        self.connection.isAlive()

        new_network = self.connection.connection.networkDefineXML(xml)
        self.network = new_network

    def start(self):
        self.connection.isAlive()
        self.network.create()

    def stop(self):
        self.connection.isAlive()
        self.network.destroy()

    def deleteNetwork(self):
        self.connection.isAlive()
        self.connection.sendEvent(
            self.connection,
            self.network,
            CALLBACK_TYPE_NETWORK_GENERIC,
            NETWORK_EVENT_DELETED,
            0,
        )

        # Check if any callbacks are still there
        if len(self.event_callbacks) > 0:
            print([cb.cb for cb in self.event_callbacks])
            raise Exception("Something didn't unregister properly")

        if self.network.isActive():
            self.network.destroy()
        self.network.undefine()

    ############################################
    # Small getters
    ############################################
    def getETree(self):
        """Load data from xml-definition"""
        self.connection.isAlive()
        xml = self.network.XMLDesc()
        xml_tree = ET.fromstring(xml)
        return xml_tree

    def getDisplayName(self):
        self.connection.isAlive()
        title_xml = self.getETree().find("title")
        if title_xml is not None:
            if title_xml.text is not None:
                return title_xml.text
        return self.network.name()

    def isActive(self):
        self.connection.isAlive()
        return self.network.isActive()

    def isPersistent(self):
        self.connection.isAlive()
        return self.network.isPersistent()

    def getXML(self):
        self.connection.isAlive()
        xml = self.network.XMLDesc()
        return xml

    def getAutostart(self):
        self.connection.isAlive()
        return self.network.autostart()

    def getUUID(self):
        self.connection.isAlive()
        return self.network.UUIDString()

    def getDHCPLeases(self, ready_cb: callable) -> list:
        self.connection.isAlive()

        def listLeases():
            try:
                leases = self.network.DHCPLeases()
                return leases
            except:
                return None

        asyncJob(listLeases, [], ready_cb)

    ############################################
    # Small setters
    ############################################
    def setAutostart(self, autostart: bool):
        self.connection.isAlive()
        self.network.setAutostart(autostart)
