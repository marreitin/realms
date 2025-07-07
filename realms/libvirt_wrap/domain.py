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
from .pool import Pool, getPoolFromName
from .volume import Volume, getVolumeFromName


class Domain(EventManager):
    def __init__(self, connection: Connection, domain: libvirt.virDomain):
        super().__init__()

        self.connection = connection
        self.connection.isAlive()
        self.connection.registerCallback(self.onConnectionEvent)
        self.domain_capabilites = self.connection.getDomainCapabilities()
        self.domain = domain

    ############################################
    # Callbacks
    ############################################

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id):
        # Filter unwanted stuff
        if (
            type_id in [CALLBACK_TYPE_DOMAIN_LIFECYCLE, CALLBACK_TYPE_DOMAIN_GENERIC]
            and obj.UUIDString() != self.domain.UUIDString()
        ):
            return
        elif type_id not in [
            CALLBACK_TYPE_CONNECTION_GENERIC,
            CALLBACK_TYPE_DOMAIN_GENERIC,
            CALLBACK_TYPE_DOMAIN_LIFECYCLE,
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
        self.domain.create()

    def resume(self) -> None:
        self.connection.isAlive()
        self.domain.resume()

    def shutdown(self) -> None:
        """Most secure way of stopping a domain, requests a regular shutdown"""
        self.connection.isAlive()
        self.domain.shutdown()

    def destroy(self) -> None:
        """Less secure than shutdown, might kill domain."""
        self.connection.isAlive()
        self.domain.destroy()

    def reset(self) -> None:
        """Pull the virtual power cable."""
        self.connection.isAlive()
        self.domain.reset()

    def pause(self) -> None:
        self.connection.isAlive()
        self.domain.suspend()

    def takeSnapshot(self, xml: str) -> None:
        """Take a snapshot. The newly created snapshot object will be
        sent out by event.

        Args:
            xml (str): Snapshot XML definition
        """
        self.connection.isAlive()
        snapshot = self.domain.snapshotCreateXML(xml)
        self.sendEvent(
            self.connection,
            snapshot,
            CALLBACK_TYPE_DOMAIN_GENERIC,
            DOMAIN_EVENT_SNAPSHOT_TAKEN,
            0,
        )

    def deleteSnapshot(self, snapshot: libvirt.virDomainSnapshot) -> None:
        """Delete the given snapshot.

        Args:
            snapshot (libvirt.virDomainSnapshot):
        """
        self.connection.isAlive()
        snapshot.delete()
        self.sendEvent(
            self.connection,
            snapshot,
            CALLBACK_TYPE_DOMAIN_GENERIC,
            DOMAIN_EVENT_SNAPSHOT_DELETED,
            0,
        )

    def revertToSnapshot(self, snapshot: libvirt.virDomainSnapshot):
        """Revert domain state to the given snapshot."""
        self.connection.isAlive()
        self.domain.revertToSnapshot(snapshot)

    def listSnapshots(self, ready_cb: callable):
        """List all snapshots

        Args:
            ready_cb (callable): Will be called with list of libvirt.virDomainSnapshot
        """
        self.connection.isAlive()
        asyncJob(self.domain.listAllSnapshots, [], ready_cb)

    def deleteDomain(self) -> None:
        """Delete this domain and perform additional checks that there are no
        registered callbacks left dangling. Deletion only happens if all checks
        pass.

        Raises:
            Exception: If some callbacks were not unregistered
        """
        self.connection.isAlive()
        self.connection.sendEvent(
            self.connection,
            self.domain,
            CALLBACK_TYPE_DOMAIN_GENERIC,
            DOMAIN_EVENT_DELETED,
            0,
        )

        # Check if any callbacks are still there
        if len(self.event_callbacks) > 0:
            print([cb.cb for cb in self.event_callbacks])
            raise Exception("Something didn't unregister properly")

        if self.isActive():
            self.domain.destroy()

        # Use almost all the flags so it really get's deleted, see
        # https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainUndefineFlags
        flags = libvirt.VIR_DOMAIN_UNDEFINE_MANAGED_SAVE
        flags ^= libvirt.VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA
        flags ^= libvirt.VIR_DOMAIN_UNDEFINE_NVRAM
        flags ^= libvirt.VIR_DOMAIN_UNDEFINE_CHECKPOINTS_METADATA
        flags ^= libvirt.VIR_DOMAIN_UNDEFINE_TPM
        self.domain.undefineFlags(flags)

    def update(self, new_tree: ET.Element):
        """Update the domain with the given xml tree.

        Args:
            new_tree (ET.Element): XML Tree for new secret definition
        """
        self.connection.isAlive()

        xml = ET.tostring(new_tree, encoding="unicode")
        print(xml)
        self.updateDefinition(xml)

    def updateDefinition(self, xml: str):
        """Update persistent xml definition

        Args:
            xml (str): XML string for domain
        """
        self.connection.isAlive()

        new_domain = self.connection.__connection__.defineXML(xml)
        self.domain = new_domain

    def updateDevice(self, device_xml: ET.Element):
        """Update the definition of a virtual device, regardless
        of the current state

        Args:
            device_xml (ET.Element): XML of the virtual device only
        """
        self.connection.isAlive()
        xml = ET.tostring(device_xml, "unicode")
        self.domain.updateDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CURRENT)

    def attachDevice(self, device_xml: ET.Element):
        """Attach the given device to the domain, regardless
        of current state."""
        self.connection.isAlive()
        xml = ET.tostring(device_xml, "unicode")
        self.domain.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CURRENT)

    def detachDevice(self, device_xml: ET.Element):
        """Detach the given device from the domain when active."""
        self.connection.isAlive()
        xml = ET.tostring(device_xml, "unicode")
        self.domain.detachDevice(xml)

    ############################################
    # Small getters
    ############################################
    def getETree(self) -> ET.Element:
        """Load data from xml-definition"""
        self.connection.isAlive()
        xml = self.domain.XMLDesc()
        xml_tree = ET.fromstring(xml)
        return xml_tree

    def getDisplayName(self) -> str:
        """Get either the domain's title or it's name for display

        Returns:
            str: Domains name for displaying
        """
        self.connection.isAlive()
        title_xml = self.getETree().find("title")
        if title_xml is not None:
            if title_xml.text is not None:
                return title_xml.text
        return self.domain.name()

    def getUUID(self) -> str:
        self.connection.isAlive()
        return self.domain.UUIDString()

    def isPersistent(self) -> bool:
        self.connection.isAlive()
        return self.domain.isPersistent()

    def isActive(self) -> bool:
        self.connection.isAlive()
        return self.domain.isActive()

    def getXML(self) -> str:
        self.connection.isAlive()
        return self.domain.XMLDesc()

    def getAutostart(self) -> bool:
        self.connection.isAlive()
        return self.domain.autostart()

    def getStateID(self) -> int:
        self.connection.isAlive()
        state = self.domain.info()[0]
        return state

    def getStateText(self) -> str:
        """Return a descriptive string of the current domain state"""
        self.connection.isAlive()
        state = self.getStateID()
        if state == libvirt.VIR_DOMAIN_NOSTATE:
            return "no state"
        if state == libvirt.VIR_DOMAIN_RUNNING:
            return "running"
        if state == libvirt.VIR_DOMAIN_BLOCKED:
            return "blocked"
        if state == libvirt.VIR_DOMAIN_PAUSED:
            return "paused"
        if state == libvirt.VIR_DOMAIN_SHUTDOWN:
            return "shutting down"
        if state == libvirt.VIR_DOMAIN_SHUTOFF:
            return "shut off"
        if state == libvirt.VIR_DOMAIN_CRASHED:
            return "crashed"
        if state == libvirt.VIR_DOMAIN_PMSUSPENDED:
            return "pm-suspended"

    def getVCPUs(self) -> int:
        self.connection.isAlive()
        return self.domain.info()[3]

    def getCPUTime(self) -> int:
        """Return the CPU time in ns averaged for all vcpus
        Returns:
            Float: CPU time in ns (max is one second)
        """
        self.connection.isAlive()
        if self.isActive():
            return self.domain.info()[4]
        else:
            return 0

    def getMaxMemory(self) -> int:
        self.connection.isAlive()
        return self.domain.info()[1]

    def getMemoryUsage(self) -> int:
        self.connection.isAlive()
        if self.isActive():
            try:
                stats = self.domain.memoryStats()
                # Just show how much memory the guest process uses
                # from the hosts perspective.
                return stats["rss"]
            except:
                return 0
        else:
            return 0

    def getAttachedStorageVolumes(self) -> list[Volume]:
        self.connection.isAlive()
        xml = self.getETree()

        volumes = []

        for device_xml in xml.find("devices"):
            if device_xml.tag == "disk" and device_xml.get("type", "") == "volume":
                source_xml = device_xml.find("source")
                if source_xml is None:
                    continue

                pool_name = source_xml.get("pool", "")
                vol_name = source_xml.get("volume", "")

                if not pool_name or not vol_name:
                    continue

                pool: Pool = getPoolFromName(self.connection, pool_name)
                volume = getVolumeFromName(pool, vol_name)
                volumes.append(volume)
        return volumes

    def getNICs(self) -> list[str]:
        """Find all network interfaces names attached to this domain.
        Will return none when shut off.
        """
        nics = []

        if self.isActive():
            xml = self.getETree()

            volumes = []

            for device_xml in xml.find("devices"):
                if device_xml.tag == "interface":
                    target = device_xml.find("target")
                    if target is None:
                        continue

                    dev = target.get("dev")

                    if not dev:
                        continue

                    nics.append(dev)

        return nics

    def getNICStats(self, nic: str) -> tuple[int, int]:
        """Get network interface usage on the given interface
        for (rx, tx).
        """
        if self.isActive():
            try:
                stats = self.domain.interfaceStats(nic)
                return (stats[0], stats[4])
            except libvirt.libvirtError:
                pass

        return (0, 0)

    ############################################
    # Small setters
    ############################################

    def setAutostart(self, autostart: bool) -> None:
        self.connection.isAlive()
        self.domain.setAutostart(autostart)
