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
"""Build the main row inside the main window's sidebar,
one for each connection."""

import libvirt
from gi.repository import Adw, Gtk, Pango

from realms.libvirt_wrap import Connection, Domain, Network, Pool
from realms.libvirt_wrap.constants import *
from realms.ui.rows import DomainRow, NetworkRow, PoolRow
from realms.ui.rows.row_sorting import rowSortingFunc
from realms.ui.tabs import ConnectionDetailsTab

from .dialogs.add_domain_dialog import AddDomainDialog
from .dialogs.add_net_dialog import AddNetDialog
from .dialogs.add_pool_dialog import AddPoolDialog


def buildQuickAction(icon: str, tooltip: str, clicked_cb) -> Gtk.Button:
    """Build one of the small quick actions in the sidebar, that
    allow i.e. creating a domain."""
    button = Gtk.Button(icon_name=icon, width_request=48)
    button.set_tooltip_text(tooltip)

    if clicked_cb is not None:
        button.connect("clicked", clicked_cb)

    return button


def buildSubExpander(title: str, expanded=False) -> Gtk.Expander:
    """Build an expander inside of each domains, networks and storage pools are listed."""
    expander = Gtk.Expander(expanded=expanded, resize_toplevel=False)
    label = Gtk.Label(
        label=title,
        css_classes=["heading"],
        margin_top=6,
        margin_bottom=6,
        margin_start=6,
        margin_end=6,
    )
    expander.set_label_widget(label)
    return expander


def buildSubListbox() -> Gtk.ListBox:
    """Builds the listbox used for listing domains, pool and networks"""

    def onSubRowActivated(_, row):
        row.onActivate()

    listbox = Gtk.ListBox(
        show_separators=False,
        css_classes=["navigation-sidebar"],
        selection_mode=Gtk.SelectionMode.NONE,
    )
    listbox.connect("row-activated", onSubRowActivated)

    listbox.set_sort_func(rowSortingFunc)

    return listbox


class ConnectionRow(Gtk.ListBoxRow):
    """Large "row" for the navigation sidebar. Represent an individual connection."""

    def __init__(self, conn_settings: dict, window: Adw.ApplicationWindow):
        super().__init__()

        self.connection = None
        self.window = None

        self.status_icon = None
        self.loading_spinner = None
        self.name_label = None
        self.url_label = None
        self.quick_action_box = None
        self.quick_actions = {}
        self.storage_expander = None
        self.network_expander = None
        self.domain_expander = None

        self.storage_listbox = None
        self.network_listbox = None
        self.domain_listbox = None

        self.storage_rows = {}  # Dict from uuid to storage-row
        self.network_rows = {}  # Dict from uuid to network-row
        self.domain_rows = {}  # Dict from uuid to domain-row

        self.window = window
        self.connection = Connection(conn_settings)
        self.connection.register_callback_any(self.onConnectionEvent, None)

        self.build()

        if self.connection.autoconnect:
            self.connection.tryConnect()

        self.setStatus()

    def build(self):
        """Build self."""
        self.set_activatable(False)
        self.set_css_classes(["frame"])
        self.set_margin_bottom(6)

        # Main Box with the subexpanders
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_margin_bottom(6)
        self.set_child(box)

        # Label widget
        label_box = Gtk.Box(
            spacing=6, margin_top=8, margin_bottom=8, margin_start=6, margin_end=6
        )
        box.append(label_box)

        self.name_label = Gtk.Label(label=self.connection.name)
        self.name_label.set_css_classes(["heading"])
        label_box.append(self.name_label)

        self.url_label = Gtk.Label(
            label=self.connection.url, hexpand=True, halign=Gtk.Align.START
        )
        self.url_label.set_tooltip_text(self.connection.url)
        self.url_label.set_css_classes(["monospace", "dim-label"])
        self.url_label.set_ellipsize(Pango.EllipsizeMode.END)
        label_box.append(self.url_label)

        self.status_icon = Gtk.Image.new_from_icon_name("network-wired-symbolic")
        label_box.append(self.status_icon)

        self.loading_spinner = Gtk.Spinner(visible=False)
        label_box.append(self.loading_spinner)

        # Some quick actions
        self.quick_action_box = Gtk.Box(hexpand=True, css_classes=["linked"])
        box.append(self.quick_action_box)

        self.quick_actions = {
            "edit-conn": buildQuickAction(
                "document-edit-symbolic",
                "Edit connection details",
                self.onEditConnClicked,
            ),
            "add-net": buildQuickAction(
                "network-wired-symbolic", "Add virtual network", self.onAddNetClicked
            ),
            "add-pool": buildQuickAction(
                "drive-multidisk-symbolic", "Add storage pool", self.onAddPoolClicked
            ),
            "add-dom": buildQuickAction(
                "computer-symbolic", "Add domain", self.onAddDomainClicked
            ),
            "connect": buildQuickAction(
                "update-symbolic",
                "Try to connect again",
                self.onTryConnectClicked,
            ),
        }

        for widget in self.quick_actions.values():
            self.quick_action_box.append(widget)

        self.storage_expander = buildSubExpander("Storage pools", False)
        self.storage_listbox = buildSubListbox()
        self.storage_expander.set_child(self.storage_listbox)
        box.append(self.storage_expander)

        self.network_expander = buildSubExpander("Networks", False)
        self.network_listbox = buildSubListbox()
        self.network_expander.set_child(self.network_listbox)
        box.append(self.network_expander)

        self.domain_expander = buildSubExpander("Virtual machines", True)
        self.domain_listbox = buildSubListbox()
        self.domain_expander.set_child(self.domain_listbox)
        self.domain_expander.set_expanded(True)
        box.append(self.domain_expander)

        self.setStatus()

    def buildNetworkRows(self):
        """Build the network sub-rows."""

        def finish(vir_networks: list[libvirt.virNetwork]):
            self.network_listbox.remove_all()
            self.network_rows.clear()
            for vnet in vir_networks:
                self.addNetwork(vnet)

        if self.connection.isConnected():
            self.connection.listNetworks(finish)

    def buildPoolRows(self):
        """Build the pool sub-rows."""

        def finish(vir_pools: list[libvirt.virStoragePool]):
            self.storage_listbox.remove_all()
            self.storage_rows.clear()
            for pool in vir_pools:
                self.addPool(pool)

        if self.connection.isConnected():
            self.connection.listStoragePools(finish)

    def buildDomainRows(self):
        """Build the domain sub-rows."""

        def finish(vir_domains: list[libvirt.virDomain]):
            self.domain_listbox.remove_all()
            self.domain_rows.clear()
            for dom in vir_domains:
                self.addDomain(dom)

        if self.connection.isConnected():
            self.connection.listDomains(finish)

    def handleConnectionEvents(self, conn, obj, type_id, event_id, detail_id):
        """Handle general events."""
        if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id == CONNECTION_EVENT_SETTINGS_CHANGED:
                pass
            elif event_id == CONNECTION_EVENT_DELETED:
                self.connection.unregister_callback(self.onConnectionEvent)
                self.window.removeConnection(self.connection.url)
            elif event_id == CONNECTION_EVENT_ATTEMPT_CONNECT:
                self.quick_actions["connect"].set_sensitive(False)
            elif event_id == CONNECTION_EVENT_CONNECTED:
                self.buildNetworkRows()
                self.buildPoolRows()
                self.buildDomainRows()
                self.quick_actions["connect"].set_sensitive(True)
            elif event_id == CONNECTION_EVENT_CONNECTION_FAILED:
                self.window.pushToastText(
                    f"Failed to connect to { self.connection.url } ('{ self.connection.name }')"
                )
                self.quick_actions["connect"].set_sensitive(True)

    def handleNetworkEvents(self, conn, obj, type_id, event_id, detail_id):
        """Handle network events."""
        if type_id == CALLBACK_TYPE_NETWORK_LIFECYCLE:
            if event_id == libvirt.VIR_NETWORK_EVENT_DEFINED:
                self.addNetwork(obj)

        elif type_id == CALLBACK_TYPE_NETWORK_GENERIC:
            if event_id == NETWORK_EVENT_DELETED:
                uuid = obj.UUIDString()
                row = self.network_rows.pop(uuid)
                self.network_listbox.remove(row)
                print("removed row")
            elif event_id == NETWORK_EVENT_ADDED:
                self.addNetwork(obj, open_tab=True)

    def handlePoolEvents(self, conn, obj, type_id, event_id, detail_id):
        """Handle pool events."""
        if type_id == CALLBACK_TYPE_POOL_LIFECYCLE:
            if event_id == libvirt.VIR_STORAGE_POOL_EVENT_DEFINED:
                self.addPool(obj)

        elif type_id == CALLBACK_TYPE_POOL_GENERIC:
            if event_id == POOL_EVENT_DELETED:
                uuid = obj.UUIDString()
                row = self.storage_rows.pop(uuid)
                self.storage_listbox.remove(row)
                print("removed row")
            elif event_id == POOL_EVENT_ADDED:
                self.addPool(obj, open_tab=True)

    def handleDomainEvents(self, conn, obj, type_id, event_id, detail_id):
        """Handle domain events."""
        if type_id == CALLBACK_TYPE_DOMAIN_LIFECYCLE:
            if event_id == libvirt.VIR_DOMAIN_EVENT_DEFINED:
                self.addDomain(obj)

        elif type_id == CALLBACK_TYPE_DOMAIN_GENERIC:
            if event_id == DOMAIN_EVENT_DELETED:
                uuid = obj.UUIDString()
                row = self.domain_rows.pop(uuid)
                self.domain_listbox.remove(row)
                print("removed row")
            elif event_id == DOMAIN_EVENT_ADDED:
                self.addDomain(obj, open_tab=True)

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id, opaque):
        """Top level event handler."""
        print(
            "Connection Row registered connection event: ", type_id, event_id, detail_id
        )
        self.handleConnectionEvents(conn, obj, type_id, event_id, detail_id)
        # Networks
        self.handleNetworkEvents(conn, obj, type_id, event_id, detail_id)

        # Storage pools
        self.handlePoolEvents(conn, obj, type_id, event_id, detail_id)

        # Domains
        self.handleDomainEvents(conn, obj, type_id, event_id, detail_id)

        self.setStatus()

    def setStatus(self) -> None:
        """Update what should be visible and what hidden."""
        state = self.connection.getState()

        self.window.updateConnectionURL(self.url_label.get_label(), self.connection.url)
        self.url_label.set_label(self.connection.getURLCurr())
        self.url_label.set_tooltip_text(self.connection.getURLCurr())
        self.name_label.set_label(self.connection.name)

        if state == CONNECTION_STATE_CONNECTED:
            self.quick_actions["add-dom"].set_visible(True)
            self.quick_actions["add-net"].set_visible(True)
            self.quick_actions["add-pool"].set_visible(True)
            self.quick_actions["edit-conn"].set_visible(True)
            self.quick_actions["connect"].set_visible(False)
            self.quick_actions["connect"].set_sensitive(True)

            self.status_icon.set_from_icon_name("network-transmit-receive-symbolic")
            self.status_icon.set_visible(True)
            self.loading_spinner.set_visible(False)
            self.loading_spinner.stop()

            self.storage_expander.set_visible(True)
            self.network_expander.set_visible(True)
            self.domain_expander.set_visible(True)
        elif state == CONNECTION_STATE_CONNECTING:
            self.quick_actions["add-dom"].set_visible(False)
            self.quick_actions["add-net"].set_visible(False)
            self.quick_actions["add-pool"].set_visible(False)
            self.quick_actions["edit-conn"].set_visible(False)
            self.quick_actions["connect"].set_visible(False)
            self.quick_actions["connect"].set_sensitive(False)

            self.status_icon.set_from_icon_name("network-offline-symbolic")
            self.status_icon.set_visible(False)
            self.loading_spinner.set_visible(True)
            self.loading_spinner.start()

            self.storage_expander.set_visible(False)
            self.network_expander.set_visible(False)
            self.domain_expander.set_visible(False)
        else:
            self.quick_actions["add-dom"].set_visible(False)
            self.quick_actions["add-net"].set_visible(False)
            self.quick_actions["add-pool"].set_visible(False)
            self.quick_actions["edit-conn"].set_visible(True)
            self.quick_actions["connect"].set_visible(True)
            self.quick_actions["connect"].set_sensitive(True)

            self.status_icon.set_from_icon_name("network-offline-symbolic")
            self.status_icon.set_visible(True)
            self.loading_spinner.set_visible(False)
            self.loading_spinner.stop()

            self.storage_expander.set_visible(False)
            self.network_expander.set_visible(False)
            self.domain_expander.set_visible(False)

    def onEditConnClicked(self, _):
        """Show the edit-connection tab."""
        uuid = self.connection.url
        if not self.window.tabExists(uuid):
            tab_page_content = ConnectionDetailsTab(self.connection, self.window)
            self.window.addOrShowTab(
                tab_page_content,
                self.connection.name,
                "network-transmit-receive-symbolic",
            )

    def onAddNetClicked(self, _):
        """Show add-network dialog."""
        AddNetDialog(self.window, self.connection)

    def onAddPoolClicked(self, _):
        """Show add-pool dialog."""
        AddPoolDialog(self.window, self.connection)

    def onAddDomainClicked(self, _):
        """Show add-domain dialog."""
        AddDomainDialog(self.window, self.connection)

    def onTryConnectClicked(self, _):
        """Try to connect."""
        self.connection.tryConnect()

    def addNetwork(self, network: libvirt.virNetwork, open_tab=False) -> None:
        """Add a network row, but only if necessary"""
        uuid = network.UUIDString()
        if uuid not in self.network_rows:
            net = Network(self.connection, network)
            row = NetworkRow(net, self.window)
            self.network_listbox.append(row)
            self.network_rows[uuid] = row
            if open_tab:
                row.onActivate()

    def addPool(self, pool: libvirt.virStoragePool, open_tab=False) -> None:
        """Add a pool row, but only if necessary"""
        uuid = pool.UUIDString()
        if uuid not in self.storage_rows:
            p = Pool(self.connection, pool)
            row = PoolRow(p, self.window)
            self.storage_listbox.append(row)
            self.storage_rows[uuid] = row
            if open_tab:
                row.onActivate()

    def addDomain(self, domain: libvirt.virDomain, open_tab=False) -> None:
        """Add a pool row, but only if necessary"""
        uuid = domain.UUIDString()
        if uuid not in self.domain_rows:
            p = Domain(self.connection, domain)
            row = DomainRow(p, self.window)
            self.domain_listbox.append(row)
            self.domain_rows[uuid] = row
            if open_tab:
                row.onActivate()
        elif open_tab:
            self.domain_rows[uuid].onActivate()
