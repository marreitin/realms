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
import atexit
import traceback
import xml.etree.ElementTree as ET

import libvirt
from gi.repository import GLib

from realms.helpers import asyncJob, getSettings, putSettings

from .constants import *
from .domain_capabilities import DomainCapabilities
from .driver_capabilities import DriverCapabilities
from .event_manager import EventManager
from .node_dev import NodeDev
from .pool_capabilities import PoolCapabilities


class OperationUnsupportedException(Exception):
    """Operation is unsupported by libvirt driver."""

    pass


class Connection(EventManager):
    def __init__(self, conn_settings: dict):
        super().__init__()

        self.settings = None
        self.url = None
        self.autoconnect = False
        self.name = None
        self.description = None
        self.__is_alive__ = False

        self.connection: libvirt.virConnect = None

        self.driver_capabilities = None
        self.pool_capabilities = None
        self.domain_capabilities = None
        self.supports_secrets = False

        self.settings = conn_settings
        self.loadSettings()

        atexit.register(self.onExit)

    def onExit(self):
        if self.connection is not None:
            self.connection.close()

    ############################################
    # Event handlers
    ############################################

    def onDomainEvent(self, conn, dom: libvirt.virDomain, event, detail, opaque):
        self.sendEvent(conn, dom, CALLBACK_TYPE_DOMAIN_LIFECYCLE, event, detail)

    def onStorageEvent(self, conn, pool, event, detail, opaque):
        self.sendEvent(conn, pool, CALLBACK_TYPE_POOL_LIFECYCLE, event, detail)

    def onNetworkEvent(self, conn, network, event, detail, opaque):
        self.sendEvent(conn, network, CALLBACK_TYPE_NETWORK_LIFECYCLE, event, detail)

    def onSecretEvent(self, conn, secret, event, detail, opaque):
        self.sendEvent(conn, secret, CALLBACK_TYPE_SECRET_LIFECYCLE, event, detail)

    ############################################
    # Other methods
    ############################################

    def isAlive(self):
        """Check if connection is alive. Use as a barrier before interacting
        with connection objects. Sends out CONNECTION_EVENT_DISCONNECTED upon
        detecting that the connection disconnected.

        Raises:
            Exception: Raise if not alive
        """
        # This variable is mostly to prevent weird recursions
        if self.__is_alive__ == False:
            raise Exception("Connection is still not alive")

        if self.connection is None or not self.connection.isAlive():
            self.__is_alive__ = False
            self.sendEvent(
                self.connection,
                None,
                CALLBACK_TYPE_CONNECTION_GENERIC,
                CONNECTION_EVENT_DISCONNECTED,
                0,
            )
            if self.connection is not None:
                self.connection.close()
                self.connection = None
            raise Exception("Connection is not alive")

    def tryConnect(self) -> None:
        """Try to connect to the libvirt url of this instance. Sends out
        events if connection is established/connection failed.
        """
        if self.connection:
            return

        self.sendEvent(
            self.connection,
            None,
            CALLBACK_TYPE_CONNECTION_GENERIC,
            CONNECTION_EVENT_ATTEMPT_CONNECT,
            0,
        )

        def init() -> bool:
            try:
                self.connection = libvirt.open(self.url)
                if not self.connection:
                    raise Exception
                self.__is_alive__ = True

                self.connection.registerCloseCallback(
                    lambda *x: self.disconnect(from_disconnect=True),
                    None,
                )

                # Domain events
                self.connection.domainEventRegisterAny(
                    None,
                    libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE,
                    self.onDomainEvent,
                    None,
                )
                # Network events
                self.connection.networkEventRegisterAny(
                    None,
                    libvirt.VIR_NETWORK_EVENT_ID_LIFECYCLE,
                    self.onNetworkEvent,
                    None,
                )
                # Storage pool events
                self.connection.storagePoolEventRegisterAny(
                    None,
                    libvirt.VIR_STORAGE_POOL_EVENT_ID_LIFECYCLE,
                    self.onStorageEvent,
                    None,
                )

                try:
                    # Secrets
                    self.connection.secretEventRegisterAny(
                        None,
                        libvirt.VIR_SECRET_EVENT_ID_LIFECYCLE,
                        self.onSecretEvent,
                        None,
                    )
                    self.supports_secrets = True
                except:
                    pass

                self.loadCapabilities()

                # We're ready
                print(f"Connected to { self.url }")
                return True
            except Exception:
                print(f"Connection failed to { self.url }")
                self.connection = None
                return False

        def finish(connected):
            if connected:
                self.sendEvent(
                    self.connection,
                    None,
                    CALLBACK_TYPE_CONNECTION_GENERIC,
                    CONNECTION_EVENT_CONNECTED,
                    0,
                )
            else:
                self.sendEvent(
                    self.connection,
                    None,
                    CALLBACK_TYPE_CONNECTION_GENERIC,
                    CONNECTION_EVENT_CONNECTION_FAILED,
                    0,
                )

        asyncJob(init, [], finish)

    def disconnect(self, from_disconnect=False) -> None:
        """Disconnect this instance. Sends out disconnect event.

        Args:
            from_disconnect (bool, optional): Handle already disconnected connection.
            This terminates everything properly when the connection was closed
            from outside.
        """
        if self.isConnected():
            self.connection.close()

        if self.isConnected() or from_disconnect:
            self.connection = None
            self.__is_alive__ = False
            self.sendEvent(
                self.connection,
                None,
                CALLBACK_TYPE_CONNECTION_GENERIC,
                CONNECTION_EVENT_DISCONNECTED,
                0,
            )

    def loadSettings(self):
        self.url = self.settings["url"]
        self.autoconnect = self.settings["autoconnect"]
        self.name = self.settings["name"]
        self.description = self.settings["desc"]

    def listDomains(self, ready_cb) -> None:
        self.isAlive()

        def getDomains() -> list[libvirt.virDomain]:
            flag = 0
            vir_domains = self.connection.listAllDomains(flag)
            return vir_domains

        asyncJob(getDomains, [], ready_cb)

    def listStoragePools(self, ready_cb) -> None:
        self.isAlive()

        def getPools() -> list[libvirt.virStoragePool]:
            flag = 0  # All storage pools
            vir_pools = self.connection.listAllStoragePools(flag)
            return vir_pools

        asyncJob(getPools, [], ready_cb)

    def listNetworks(self, ready_cb) -> None:
        self.isAlive()

        def getNetworks() -> list[libvirt.virNetwork]:
            vir_networks = self.connection.listAllNetworks()
            return vir_networks

        asyncJob(getNetworks, [], ready_cb)

    def listSecrets(self, ready_cb) -> None:
        self.isAlive()
        if not self.supports_secrets:
            return

        def getSecrets() -> list[libvirt.virSecret]:
            vir_secrets = self.connection.listAllSecrets()
            return vir_secrets

        asyncJob(getSecrets, [], ready_cb)

    def addNetworkTree(self, tree: ET.Element, autostart: bool):
        self.isAlive()

        xml = ET.tostring(tree, encoding="unicode")
        self.addNetwork(xml, autostart)

    def addNetwork(self, xml: str, autostart: bool):
        self.isAlive()
        network = self.connection.networkDefineXML(xml)
        network.setAutostart(autostart)
        self.sendEvent(
            self.connection,
            network,
            CALLBACK_TYPE_NETWORK_GENERIC,
            NETWORK_EVENT_ADDED,
            0,
        )

    def addPoolTree(self, tree: ET.Element, autostart: bool):
        self.connection.isAlive()

        xml = ET.tostring(tree, encoding="unicode")
        self.addPool(xml, autostart)

    def addPool(self, xml: str, autostart: bool):
        self.isAlive()
        pool = self.connection.storagePoolDefineXML(xml)
        pool.setAutostart(autostart)
        self.sendEvent(
            self.connection,
            pool,
            CALLBACK_TYPE_POOL_GENERIC,
            POOL_EVENT_ADDED,
            0,
        )

    def addDomain(self, xml: str):
        self.isAlive()
        domain = self.connection.defineXML(xml)
        # Make sure the event is on the main thread.
        # The event will make the tab of the new domain appear.
        GLib.idle_add(
            self.sendEvent,
            self.connection,
            domain,
            CALLBACK_TYPE_DOMAIN_GENERIC,
            DOMAIN_EVENT_ADDED,
            0,
        )

    def addSecret(self, xml: str, value: str):
        self.isAlive()
        if not self.supports_secrets:
            raise OperationUnsupportedException
        secret = self.connection.secretDefineXML(xml)
        if value != "":
            secret.setValue(value)
        self.sendEvent(
            self.connection, secret, CALLBACK_TYPE_SECRET_GENERIC, SECRET_EVENT_ADDED, 0
        )

    def deleteConnection(self):
        # First notify all other widgets of this event
        # so they can destroy themselves
        if self.isConnected():
            self.connection.close()
        self.connection = None

        self.sendEvent(
            self.connection,
            None,
            CALLBACK_TYPE_CONNECTION_GENERIC,
            CONNECTION_EVENT_DELETED,
            0,
        )

        # Check if any callbacks are still there
        if len(self.event_callbacks) > 0:
            print([cb.cb for cb in self.event_callbacks])
            raise Exception("Something didn't unregister properly")

        # Delete self from settings
        conn_settings = getSettings("connections")
        conn_settings.remove(self.settings)
        putSettings("connections", conn_settings)

        # Now this connection can be safely deleted

    def loadCapabilities(self):
        try:
            xml = self.connection.getCapabilities()
            xml_tree = ET.fromstring(xml)
            self.driver_capabilities = DriverCapabilities(xml_tree)
        except:
            traceback.print_exc()
            self.driver_capabilities = DriverCapabilities(None)

        try:
            xml = self.connection.getStoragePoolCapabilities()
            xml_tree = ET.fromstring(xml)
            self.pool_capabilities = PoolCapabilities(xml_tree)
        except:
            self.pool_capabilities = PoolCapabilities(None)

        try:
            xml = self.connection.getDomainCapabilities()
            xml_tree = ET.fromstring(xml)
            self.domain_capabilities = DomainCapabilities(xml_tree)
        except:
            self.domain_capabilities = DomainCapabilities(None)

    def isConnected(self) -> bool:
        return self.__is_alive__ and self.connection is not None

    def isSecure(self) -> bool:
        self.isAlive()
        return self.connection.isSecure()

    def isEncrypted(self) -> bool:
        self.isAlive()
        return self.connection.isEncrypted()

    def maxVCPUs(self) -> int:
        self.isAlive()
        return self.connection.getMaxVcpus(None)

    def maxMemory(self) -> int:
        """Get the hypervisors max memory in bytes

        Returns:
            int: Max memory
        """
        self.isAlive()
        return self.connection.getInfo()[1] * 1024**2

    def hostname(self) -> str:
        self.isAlive()
        return self.connection.getHostname()

    def getURLCurr(self) -> str:
        """Return either the URL of the running connection or the one from the settings"""
        if self.isConnected():
            return self.connection.getURI()
        else:
            return self.url

    def getDriverCapabilities(self) -> DriverCapabilities:
        self.isAlive()
        return self.driver_capabilities

    def getPoolCapabilities(self) -> PoolCapabilities:
        self.isAlive()
        return self.pool_capabilities

    def getDomainCapabilities(self) -> DomainCapabilities:
        self.isAlive()
        return self.domain_capabilities

    def getLibvirtVersion(self):
        self.isAlive()
        version = libvirt.getVersion()
        if version == -1:
            return "unknown"
        release = int(version % 1000)
        minor = int(((version - release) % 1000000) / 1000)
        major = int((version - minor * 1000 - release) / 1000000)
        return f"{major}.{minor}.{release}"

    def setSettings(self, new_settings: dict) -> None:
        conn_settings = getSettings("connections")
        conn_settings[conn_settings.index(self.settings)] = new_settings
        putSettings("connections", conn_settings)
        self.settings = new_settings
        self.loadSettings()
        # Emit an event that the settings changed
        self.sendEvent(
            self.connection,
            None,
            CALLBACK_TYPE_CONNECTION_GENERIC,
            CONNECTION_EVENT_SETTINGS_CHANGED,
            0,
        )

    ############################################
    # Methods for host management
    ############################################

    def getHypervisorVersion(self):
        self.isAlive()
        version = self.connection.getVersion()
        if version == -1:
            return "unknown"
        release = int(version % 1000)
        minor = int(((version - release) % 1000000) / 1000)
        major = int((version - minor * 1000 - release) / 1000000)
        return f"{major}.{minor}.{release}"

    def getHostCPUTime(self) -> int:
        """Get the hosts used CPU time in ns

        Returns:
            int: CPU time in ns normed to correspond to one core
        """
        self.isAlive()
        try:
            stats = self.connection.getCPUStats(libvirt.VIR_NODE_CPU_STATS_ALL_CPUS)
            if "kernel" not in stats or "user" not in stats:
                return 0
            # Divide usage by number of CPUs
            return (stats["kernel"] + stats["user"]) / self.connection.getCPUMap()[2]
        except:
            return 0

    def getHostIOWait(self) -> int:
        """Return the hosts IO-wait time in ns

        Returns:
            int: IO wait time
        """
        self.isAlive()
        try:
            stats = self.connection.getCPUStats(libvirt.VIR_NODE_CPU_STATS_ALL_CPUS)
            if "iowait" not in stats:
                return 0
            return stats["iowait"]
        except:
            return 0

    def getHostMemoryUsage(self) -> int:
        """Return memory usage in KB

        Returns:
            int: Memory usage
        """
        self.isAlive()
        try:
            stats = self.connection.getMemoryStats(
                libvirt.VIR_NODE_MEMORY_STATS_ALL_CELLS
            )
            if (
                "total" not in stats
                or "cached" not in stats
                or "buffers" not in stats
                or "free" not in stats
            ):
                return 0
            return stats["total"] - (stats["cached"] + stats["buffers"] + stats["free"])
        except:
            return 0

    def listNodeDevices(self) -> list[NodeDev]:
        """List all devices available on the host node.

        Returns:
            list: List of devices
        """
        self.isAlive()

        devs = []
        for vir_dev in self.connection.listAllDevices():
            dev = NodeDev(self, vir_dev)
            devs.append(dev)
        return devs
