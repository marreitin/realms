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

from realms.helpers import Settings, asyncJob
from realms.libvirt_wrap.common import libvirtVersionToString

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
        self.__state__ = CONNECTION_STATE_DISCONNECTED
        self.is_local = False

        self.__connection__: libvirt.virConnect = None

        self.driver_capabilities = None
        self.pool_capabilities = None
        self.domain_capabilities = None
        self.supports_secrets = False

        self.settings = conn_settings
        self.loadSettings()

        atexit.register(self.onExit)

    def onExit(self):
        """Exit handler, should close the connection automatically."""
        if self.__connection__ is not None:
            self.__connection__.close()

    ############################################
    # Event handlers
    ############################################

    def onDomainEvent(self, conn, dom: libvirt.virDomain, event, detail, _):
        """Top Level handler for domain events."""
        self.sendEvent(conn, dom, CALLBACK_TYPE_DOMAIN_LIFECYCLE, event, detail)

    def onStorageEvent(self, conn, pool, event, detail, _):
        """Top Level handler for pool events."""
        self.sendEvent(conn, pool, CALLBACK_TYPE_POOL_LIFECYCLE, event, detail)

    def onNetworkEvent(self, conn, network, event, detail, _):
        """Top Level handler for network events."""
        self.sendEvent(conn, network, CALLBACK_TYPE_NETWORK_LIFECYCLE, event, detail)

    def onSecretEvent(self, conn, secret, event, detail, _):
        """Top Level handler for secret events. (Connection secrets)"""
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
        if self.__state__ != CONNECTION_STATE_CONNECTED:
            raise Exception("Connection is still not alive")

        if self.__connection__ is None or not self.__connection__.isAlive():
            self.__state__ = CONNECTION_STATE_DISCONNECTED
            self.sendEvent(
                self.__connection__,
                None,
                CALLBACK_TYPE_CONNECTION_GENERIC,
                CONNECTION_EVENT_DISCONNECTED,
                0,
            )
            if self.__connection__ is not None:
                self.__connection__.close()
                self.__connection__ = None
            raise Exception("Connection is not alive")

    def tryConnect(self) -> None:
        """Try to connect to the libvirt url of this instance. Sends out
        events if connection is established/connection failed.
        """
        if self.__connection__:
            return

        self.__state__ = CONNECTION_STATE_CONNECTING
        self.sendEvent(
            self.__connection__,
            None,
            CALLBACK_TYPE_CONNECTION_GENERIC,
            CONNECTION_EVENT_ATTEMPT_CONNECT,
            0,
        )

        def init() -> bool:
            try:
                self.__connection__ = libvirt.open(self.url)
                if not self.__connection__:
                    raise Exception

                self.__connection__.registerCloseCallback(
                    lambda *_: self.disconnect(from_disconnect=True),
                    None,
                )

                # Domain events
                self.__connection__.domainEventRegisterAny(
                    None,
                    libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE,
                    self.onDomainEvent,
                    None,
                )
                # Network events
                self.__connection__.networkEventRegisterAny(
                    None,
                    libvirt.VIR_NETWORK_EVENT_ID_LIFECYCLE,
                    self.onNetworkEvent,
                    None,
                )
                # Storage pool events
                self.__connection__.storagePoolEventRegisterAny(
                    None,
                    libvirt.VIR_STORAGE_POOL_EVENT_ID_LIFECYCLE,
                    self.onStorageEvent,
                    None,
                )

                try:
                    # Secrets
                    self.__connection__.secretEventRegisterAny(
                        None,
                        libvirt.VIR_SECRET_EVENT_ID_LIFECYCLE,
                        self.onSecretEvent,
                        None,
                    )
                    self.supports_secrets = True
                except:
                    self.supports_secrets = False

                self.__loadCapabilities__()

                # We're ready
                print(f"Connected to { self.url }")
                return True
            except Exception:
                print(f"Connection failed to { self.url }")
                self.__connection__ = None
                return False

        def finish(connected):
            if connected:
                self.__state__ = CONNECTION_STATE_CONNECTED
                self.sendEvent(
                    self.__connection__,
                    None,
                    CALLBACK_TYPE_CONNECTION_GENERIC,
                    CONNECTION_EVENT_CONNECTED,
                    0,
                )
            else:
                self.__state__ = CONNECTION_STATE_DISCONNECTED
                self.sendEvent(
                    self.__connection__,
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
            self.__connection__.close()

        if self.isConnected() or from_disconnect:
            self.__connection__ = None
            self.__state__ = CONNECTION_STATE_DISCONNECTED
            self.sendEvent(
                self.__connection__,
                None,
                CALLBACK_TYPE_CONNECTION_GENERIC,
                CONNECTION_EVENT_DISCONNECTED,
                0,
            )

    def loadSettings(self):
        """Load the given settings of this connection."""
        self.url = self.settings["url"]
        self.autoconnect = self.settings["autoconnect"]
        self.name = self.settings["name"]
        self.description = self.settings["desc"]

        self.isLocalConnection()

    def isLocalConnection(self):
        """Find out wheter the URL is to a local hypervisor
        or not."""
        self.is_local = True

        if ":" not in self.url:
            return
        if "+" in self.url.split(":")[0]:
            self.is_local = False

    def listDomains(self, ready_cb: callable) -> None:
        """List all domains on that connection asynchronously.

        Args:
            ready_cb (callable): Callback with list of virDomain.
        """
        self.isAlive()

        def getDomains() -> list[libvirt.virDomain]:
            flag = 0
            vir_domains = self.__connection__.listAllDomains(flag)
            return vir_domains

        asyncJob(getDomains, [], ready_cb)

    def listStoragePools(self, ready_cb: callable) -> None:
        """List all pools on that connection asynchronously.

        Args:
            ready_cb (callable): Callback with list of virStoragePool.
        """
        self.isAlive()

        def getPools() -> list[libvirt.virStoragePool]:
            flag = 0  # All storage pools
            vir_pools = self.__connection__.listAllStoragePools(flag)
            return vir_pools

        asyncJob(getPools, [], ready_cb)

    def listNetworks(self, ready_cb) -> None:
        """List all network on that connection asynchronously.

        Args:
            ready_cb (callable): Callback with list of virNetwork.
        """
        self.isAlive()

        def getNetworks() -> list[libvirt.virNetwork]:
            vir_networks = self.__connection__.listAllNetworks()
            return vir_networks

        asyncJob(getNetworks, [], ready_cb)

    def listSecrets(self, ready_cb) -> None:
        """List all connection secrets on that connection asynchronously.

        Args:
            ready_cb (callable): Callback with list of virSecret.
        """
        self.isAlive()
        if not self.supports_secrets:
            return

        def getSecrets() -> list[libvirt.virSecret]:
            vir_secrets = self.__connection__.listAllSecrets()
            return vir_secrets

        asyncJob(getSecrets, [], ready_cb)

    def addNetworkTree(self, tree: ET.Element, autostart: bool):
        """Add a network given its xml tree."""
        self.isAlive()

        xml = ET.tostring(tree, encoding="unicode")
        self.addNetwork(xml, autostart)

    def addNetwork(self, xml: str, autostart: bool):
        """Add a network given its xml description."""
        self.isAlive()
        network = self.__connection__.networkDefineXML(xml)
        network.setAutostart(autostart)
        self.sendEvent(
            self.__connection__,
            network,
            CALLBACK_TYPE_NETWORK_GENERIC,
            NETWORK_EVENT_ADDED,
            0,
        )

    def addPoolTree(self, tree: ET.Element, autostart: bool):
        """Add a pool given its xml tree."""
        self.__connection__.isAlive()

        xml = ET.tostring(tree, encoding="unicode")
        self.addPool(xml, autostart)

    def addPool(self, xml: str, autostart: bool):
        """Add a pool given its xml description."""
        self.isAlive()
        pool = self.__connection__.storagePoolDefineXML(xml)
        pool.setAutostart(autostart)
        self.sendEvent(
            self.__connection__,
            pool,
            CALLBACK_TYPE_POOL_GENERIC,
            POOL_EVENT_ADDED,
            0,
        )

    def addDomain(self, xml: str):
        """Add a domain given its xml description."""
        self.isAlive()
        domain = self.__connection__.defineXML(xml)
        # Make sure the event is on the main thread.
        # The event will make the tab of the new domain appear.
        GLib.idle_add(
            self.sendEvent,
            self.__connection__,
            domain,
            CALLBACK_TYPE_DOMAIN_GENERIC,
            DOMAIN_EVENT_ADDED,
            0,
        )

    def addSecret(self, xml: str, value: str):
        """Add a secret given its xml and a string secret value."""
        self.isAlive()
        if not self.supports_secrets:
            raise OperationUnsupportedException
        secret = self.__connection__.secretDefineXML(xml)
        if value != "":
            secret.setValue(value)
        self.sendEvent(
            self.__connection__,
            secret,
            CALLBACK_TYPE_SECRET_GENERIC,
            SECRET_EVENT_ADDED,
            0,
        )

    def deleteConnection(self):
        """Delete this connection. Handles removing it from the
        persistent settings."""
        # First notify all other widgets of this event
        # so they can destroy themselves
        if self.isConnected():
            self.__connection__.close()
        self.__connection__ = None

        self.sendEvent(
            self.__connection__,
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
        conn_settings = Settings.get("connections")
        conn_settings.remove(self.settings)
        Settings.put("connections", conn_settings)

        # Now this connection can be safely deleted

    def __loadCapabilities__(self):
        """Load this connections capabilities after connecting."""
        try:
            xml = self.__connection__.getCapabilities()
            xml_tree = ET.fromstring(xml)
            self.driver_capabilities = DriverCapabilities(xml_tree)
        except:
            traceback.print_exc()
            self.driver_capabilities = DriverCapabilities(None)

        try:
            xml = self.__connection__.getStoragePoolCapabilities()
            xml_tree = ET.fromstring(xml)
            self.pool_capabilities = PoolCapabilities(xml_tree)
        except:
            self.pool_capabilities = PoolCapabilities(None)

        try:
            xml = self.__connection__.getDomainCapabilities()
            xml_tree = ET.fromstring(xml)
            self.domain_capabilities = DomainCapabilities(xml_tree)
        except:
            self.domain_capabilities = DomainCapabilities(None)

    def isConnected(self) -> bool:
        """If it is connected."""
        return (
            self.__state__ == CONNECTION_STATE_CONNECTED
            and self.__connection__ is not None
        )

    def isSecure(self) -> bool:
        """If it is securely connected."""
        self.isAlive()
        return self.__connection__.isSecure()

    def isEncrypted(self) -> bool:
        """If the connection is encrypted."""
        self.isAlive()
        return self.__connection__.isEncrypted()

    def maxVCPUs(self) -> int:
        """Maximum number of running VCPUS."""
        self.isAlive()
        return self.__connection__.getMaxVcpus(None)

    def maxMemory(self) -> int:
        """Get the hypervisors max memory in bytes

        Returns:
            int: Max memory
        """
        self.isAlive()
        return self.__connection__.getInfo()[1] * 1024**2

    def hostname(self) -> str:
        """Hostname of hypervisor."""
        self.isAlive()
        return self.__connection__.getHostname()

    def getURLCurr(self) -> str:
        """Return either the URL of the running connection or the one from the settings"""
        if self.isConnected():
            return self.__connection__.getURI()
        return self.url

    def getDriverCapabilities(self) -> DriverCapabilities:
        """Retrieve the hypervisors capabilities."""
        self.isAlive()
        return self.driver_capabilities

    def getPoolCapabilities(self) -> PoolCapabilities:
        """Get the hypervisors pool capabilities."""
        self.isAlive()
        return self.pool_capabilities

    def getDomainCapabilities(self) -> DomainCapabilities:
        """Get the hypervisors domain capabilities."""
        self.isAlive()
        return self.domain_capabilities

    def getLibvirtVersion(self) -> str:
        """Get the libvirt version as major.minor.release"""
        self.isAlive()
        version = libvirt.getVersion()
        return libvirtVersionToString(version)

    def setSettings(self, new_settings: dict) -> None:
        """Update the settings."""
        conn_settings = Settings.get("connections")
        conn_settings[conn_settings.index(self.settings)] = new_settings
        Settings.put("connections", conn_settings)
        self.settings = new_settings
        self.loadSettings()
        # Emit an event that the settings changed
        self.sendEvent(
            self.__connection__,
            None,
            CALLBACK_TYPE_CONNECTION_GENERIC,
            CONNECTION_EVENT_SETTINGS_CHANGED,
            0,
        )

    def getState(self) -> int:
        """Get the current state."""
        return self.__state__

    ############################################
    # Methods for host management
    ############################################

    def getHypervisorVersion(self):
        """Get the libvirt version on the hypervisor
        as major.minor.release"""
        self.isAlive()
        version = self.__connection__.getVersion()
        return libvirtVersionToString(version)

    def getHostCPUTime(self) -> int:
        """Get the hosts used CPU time in ns

        Returns:
            int: CPU time in ns normed to correspond to one core
        """
        self.isAlive()
        try:
            stats = self.__connection__.getCPUStats(libvirt.VIR_NODE_CPU_STATS_ALL_CPUS)
            if "kernel" not in stats or "user" not in stats:
                return 0
            # Divide usage by number of CPUs
            return (stats["kernel"] + stats["user"]) / self.__connection__.getCPUMap()[
                2
            ]
        except:
            return 0

    def getHostIOWait(self) -> int:
        """Return the hosts IO-wait time in ns

        Returns:
            int: IO wait time
        """
        self.isAlive()
        try:
            stats = self.__connection__.getCPUStats(libvirt.VIR_NODE_CPU_STATS_ALL_CPUS)
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
            stats = self.__connection__.getMemoryStats(
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
        for vir_dev in self.__connection__.listAllDevices():
            dev = NodeDev(self, vir_dev)
            devs.append(dev)
        return devs
