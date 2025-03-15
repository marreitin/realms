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

from realms.helpers import *

from .connection import Connection
from .constants import *
from .event_manager import EventManager


class Secret(EventManager):
    def __init__(self, connection: Connection, secret: libvirt.virSecret):
        super().__init__()
        self.connection = connection
        self.connection.isAlive()
        self.connection.registerCallback(self.onConnectionEvent)
        self.secret = secret

    ############################################
    # Callbacks
    ############################################

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id):
        # Filter unwanted stuff
        if (
            type_id in [CALLBACK_TYPE_SECRET_LIFECYCLE, CALLBACK_TYPE_SECRET_GENERIC]
            and obj.UUIDString() != self.secret.UUIDString()
        ):
            return
        elif type_id not in [
            CALLBACK_TYPE_CONNECTION_GENERIC,
            CALLBACK_TYPE_SECRET_LIFECYCLE,
            CALLBACK_TYPE_SECRET_GENERIC,
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

    def deleteSecret(self) -> None:
        self.connection.isAlive()
        self.connection.sendEvent(
            self.connection,
            self.secret,
            CALLBACK_TYPE_SECRET_GENERIC,
            SECRET_EVENT_DELETED,
            0,
        )

        self.secret.undefine()

    def update(self, new_tree: ET.Element):
        """Update the secret with the given xml tree.

        Args:
            new_tree (ET.Element): XML Tree for new secret definition
        """
        self.connection.isAlive()

        xml = ET.tostring(new_tree, encoding="unicode")
        print(xml)
        self.updateDefinition(xml)

    def updateDefinition(self, xml: str):
        """Update secret xml definition

        Args:
            xml (str): XML string for secret
        """
        self.connection.isAlive()

        new_secret = self.connection.connection.secretDefineXML(xml)
        self.secret = new_secret

    ############################################
    # Small getters
    ############################################
    def getETree(self) -> ET.Element:
        """Load data from xml-definition"""
        self.connection.isAlive()
        xml = self.secret.XMLDesc()
        xml_tree = ET.fromstring(xml)
        return xml_tree

    def getDisplayName(self) -> str:
        self.connection.isAlive()
        desc_xml = self.getETree().find("description")
        if desc_xml is not None:
            if desc_xml.text is not None:
                return desc_xml.text
        return self.getUsageType().capitalize() + " secret"

    def getUsageType(self) -> str:
        usage_type = self.secret.usageType()
        if usage_type == libvirt.VIR_SECRET_USAGE_TYPE_NONE:
            return "unused"
        if usage_type == libvirt.VIR_SECRET_USAGE_TYPE_VOLUME:
            return "volume"
        if usage_type == libvirt.VIR_SECRET_USAGE_TYPE_CEPH:
            return "ceph"
        if usage_type == libvirt.VIR_SECRET_USAGE_TYPE_ISCSI:
            return "iscsi"
        if usage_type == libvirt.VIR_SECRET_USAGE_TYPE_TLS:
            return "tls"
        if usage_type == libvirt.VIR_SECRET_USAGE_TYPE_VTPM:
            return "vtpm"
        return "unknown"

    def getUUID(self) -> str:
        self.connection.isAlive()
        return self.secret.UUIDString()

    def getXML(self) -> str:
        self.connection.isAlive()
        return self.secret.XMLDesc()

    def getSecretValue(self) -> str:
        self.connection.isAlive()
        return self.secret.value().decode()

    ############################################
    # Small setters
    ############################################

    def setSecretValue(self, val: str):
        self.connection.isAlive()
        self.secret.setValue(val)
