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

from gi.repository import Adw, Gtk

from realms.helpers import failableAsyncJob
from realms.libvirt_wrap import Network
from realms.libvirt_wrap.constants import *
from realms.ui.builders import (
    ActionOption,
    ApplyRow,
    XMLView,
    hspacer,
    iconButton,
    selectDialog,
)
from realms.ui.builders.net import (
    BaseNetSettingsPage,
    NetDNSPage,
    NetGeneralGroup,
    NetIPPage,
    NetLeasePage,
    NetQOSPage,
    NetRoutePage,
)
from realms.ui.builders.preference_widgets import RealmsClamp, RealmsPreferencesPage

from .base_details import BaseDetailsTab


class SubsettingsRow(Adw.ActionRow):
    """A ActionRow that opens a NavigationPage with more settings."""

    def __init__(
        self,
        title: str,
        icon_name: str,
        parent: BaseDetailsTab,
        settings_page: BaseNetSettingsPage,
    ):
        super().__init__(
            title=title,
            activatable=True,
            selectable=False,
        )
        self.title = title
        self.icon_name = icon_name
        self.parent = parent
        self.settings_page = settings_page

        self.build()

    def build(self):
        main_icon = Gtk.Image.new_from_icon_name(self.icon_name)
        self.add_prefix(main_icon)

        open_icon = Gtk.Image.new_from_icon_name("go-next-symbolic")
        self.add_suffix(open_icon)

        self.connect("activated", self.onActivated)

    def updateData(self, xml_tree: ET.Element):
        self.settings_page.updateData(xml_tree)

    def onActivated(self, row):
        self.parent.onSubsettingsSelected(self.settings_page)


class NetworkDetailsTab(BaseDetailsTab):
    """Tab showing network details."""

    def __init__(self, network: Network, window: Adw.ApplicationWindow):
        super().__init__(window)

        self.network = network
        self.xml_tree = None

        self.stack = None

        # Actions
        self.actions_prefs_page = None
        self.apply_row = None

        self.back_btn = None
        self.start_btn = None
        self.stop_btn = None
        self.delete_btn = None
        self.status_label = None

        # General settings
        self.prefs_page = None

        self.xml_box = None

        self.build()

        # Only follow the events interesting for this network
        self.network.register_callback_any(self.onConnectionEvent, None)

    def build(self):
        self.set_hexpand(True)
        self.set_vexpand(True)

        toolbar_view = Adw.ToolbarView(hexpand=True, vexpand=True)
        self.append(toolbar_view)

        self.stack = Adw.ViewStack(hexpand=True, vexpand=True)
        toolbar_view.set_content(self.stack)

        self.apply_row = ApplyRow(
            self.onApplyClicked,
            self.onCancelClicked,
            "Changes only available after restart",
        )
        toolbar_view.add_bottom_bar(self.apply_row)

        switcher = Adw.ViewSwitcherBar(reveal=True, stack=self.stack)
        toolbar_view.add_bottom_bar(switcher)

        self.navigation_view = Adw.NavigationView()
        self.stack.add_titled_with_icon(
            self.navigation_view, "settings", "Settings", "settings-symbolic"
        )

        # Top group with buttons
        clamp = RealmsClamp()
        toolbar_view.add_top_bar(clamp)
        actions_box = Gtk.Box(
            spacing=6,
            margin_top=6,
            margin_bottom=6,
            margin_start=6,
            margin_end=6,
            width_request=108,
        )
        clamp.set_child(actions_box)

        self.back_btn = iconButton(
            "",
            "go-previous-symbolic",
            self.onBackClicked,
            css_classes=["flat"],
            visible=False,
        )
        actions_box.append(self.back_btn)
        self.navigation_view.connect(
            "popped",
            lambda *_: self.back_btn.set_visible(
                self.navigation_view.get_visible_page() != self.main_nav_page
            ),
        )

        self.start_btn = iconButton(
            "Start", "media-playback-start-symbolic", self.onStartClicked
        )
        actions_box.append(self.start_btn)

        self.stop_btn = iconButton(
            "Stop", "media-playback-stop-symbolic", self.onStopClicked
        )
        actions_box.append(self.stop_btn)

        actions_box.append(hspacer())

        self.status_label = Gtk.Label(label="Down", css_classes=["dim-label"])
        actions_box.append(self.status_label)

        # Settings
        prefs_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True
        )
        self.main_nav_page = Adw.NavigationPage(title="main", child=prefs_box)
        self.navigation_view.push(self.main_nav_page)

        # Group with general network settings
        self.prefs_page = RealmsPreferencesPage()
        prefs_box.append(self.prefs_page)

        self.general_prefs_group = NetGeneralGroup(
            False, self.window_ref.window, self.showApply, self.onDeleteClicked
        )
        self.prefs_page.add(self.general_prefs_group)

        # Group with links to more settings
        self.link_group = Adw.PreferencesGroup()
        self.prefs_page.add(self.link_group)

        self.dhcp_leases_row = SubsettingsRow(
            "DHCP leases",
            "tag-outline-symbolic",
            self,
            NetLeasePage(self),
        )
        self.link_group.add(self.dhcp_leases_row)

        self.dns_row = SubsettingsRow(
            "DNS",
            "address-book-alt-symbolic",
            self,
            NetDNSPage(self, self.showApply),
        )
        self.link_group.add(self.dns_row)

        self.ip_address_row = SubsettingsRow(
            "Network IP addresses",
            "network-proxy-symbolic",
            self,
            NetIPPage(self, self.showApply),
        )
        self.link_group.add(self.ip_address_row)

        self.static_route_row = SubsettingsRow(
            "Static routes",
            "distance-symbolic",
            self,
            NetRoutePage(self, self.showApply),
        )
        self.link_group.add(self.static_route_row)

        self.qos_row = SubsettingsRow(
            "Quality of service",
            "network-cellular-signal-good-symbolic",
            self,
            NetQOSPage(self, self.showApply),
        )
        self.link_group.add(self.qos_row)

        # XML
        self.xml_box = XMLView(self.showApply)
        self.stack.add_titled_with_icon(
            self.xml_box, "xml", "XML", "folder-code-legacy-symbolic"
        )

        self.updateData()
        self.setStatus()

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id, opaque):
        if type_id == CALLBACK_TYPE_NETWORK_GENERIC:
            if event_id == NETWORK_EVENT_DELETED:
                self.window_ref.window.closeTab(self)
                return
        elif type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.window_ref.window.closeTab(self)
                return
        self.setStatus()

    def setStatus(self):
        if self.network.isActive():
            self.start_btn.set_visible(False)
            self.stop_btn.set_visible(True)
            self.status_label.set_label("up")

            self.apply_row.setShowWarning(True)
        else:
            self.start_btn.set_visible(True)
            self.stop_btn.set_visible(False)
            self.status_label.set_label("down")

            self.apply_row.setShowWarning(False)

    def updateData(self):
        self.xml_tree = self.network.getETree()

        # Set QOS row visibility
        forward_mode = self.xml_tree.find("forward")
        if forward_mode is None or forward_mode.get("mode") in [
            "nat",
            "route",
            "bridge",
        ]:
            self.qos_row.set_visible(True)
        else:
            self.qos_row.set_visible(False)

        self.general_prefs_group.updateData(self.xml_tree, self.network.getAutostart())
        self.qos_row.updateData(self.xml_tree)
        self.ip_address_row.updateData(self.xml_tree)
        self.dns_row.updateData(self.xml_tree)
        self.static_route_row.updateData(self.xml_tree)

        self.xml_box.setText(self.network.getXML())

        self.apply_row.set_visible(False)

    def onSubsettingsSelected(self, page):
        self.navigation_view.push(page)
        self.back_btn.set_visible(True)

    def onApplyClicked(self, btn):
        self.network.setAutostart(self.general_prefs_group.getAutostart())

        try:
            if self.stack.get_visible_child_name() == "xml":
                self.network.updateDefinition(self.xml_box.getText())
            else:
                self.network.update(self.xml_tree)
            self.updateData()
        except Exception as e:
            self.window_ref.window.pushToastText(str(e))

    def onCancelClicked(self, btn):
        self.updateData()

    def showApply(self, *args):
        self.apply_row.set_visible(True)

    def onStartClicked(self, btn):
        self.start_btn.set_sensitive(False)
        failableAsyncJob(
            self.network.start,
            [],
            lambda e: self.window_ref.window.pushToastText(str(e)),
            lambda r: self.start_btn.set_sensitive(True),
        )

    def onStopClicked(self, btn):
        self.stop_btn.set_sensitive(False)
        failableAsyncJob(
            self.network.stop,
            [],
            lambda e: self.window_ref.window.pushToastText(str(e)),
            lambda r: self.stop_btn.set_sensitive(True),
        )

    def onBackClicked(self, btn):
        self.navigation_view.pop()

    def onDeleteClicked(self, btn):
        def onDelete():
            btn.set_sensitive(False)
            try:
                self.network.deleteNetwork()
            except Exception as e:
                self.window_ref.window.pushToastText(str(e))
            finally:
                btn.set_sensitive(True)

        dialog = selectDialog(
            "Delete network?",
            "Deleting a network is irreversible",
            [
                ActionOption(
                    "Delete", onDelete, appearance=Adw.ResponseAppearance.DESTRUCTIVE
                )
            ],
        )
        dialog.present(self.window_ref.window)

    def end(self):
        # Unsubscribe from events
        self.network.unregister_callback(self.onConnectionEvent)

    def getWindow(self):
        return self.window_ref.window

    def getUniqueIdentifier(self) -> str:
        return self.network.getUUID()
