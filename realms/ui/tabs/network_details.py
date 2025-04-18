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
from realms.ui.components import (
    ActionOption,
    ApplyRow,
    XMLView,
    iconButton,
    selectDialog,
)
from realms.ui.components.net import (
    BaseNetSettingsPage,
    NetDNSPage,
    NetGeneralGroup,
    NetIPPage,
    NetLeasePage,
    NetQOSPage,
    NetRoutePage,
)
from realms.ui.components.preference_widgets import RealmsPreferencesPage

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
        self.__title__ = title
        self.__icon_name__ = icon_name
        self.__parent__ = parent
        self.__settings_page__ = settings_page

        self.__build__()

    def __build__(self):
        main_icon = Gtk.Image.new_from_icon_name(self.__icon_name__)
        self.add_prefix(main_icon)

        open_icon = Gtk.Image.new_from_icon_name("right-symbolic")
        self.add_suffix(open_icon)

        self.connect("activated", self.__onActivated__)

    def __onActivated__(self, _):
        """The row was clicked."""
        self.__parent__.onSubsettingsSelected(self.__settings_page__)

    def updateData(self, xml_tree: ET.Element):
        """Update the xml tree with new data."""
        self.__settings_page__.updateData(xml_tree)


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

        self.title_widget = None
        self.back_btn = None
        self.start_btn = None
        self.stop_btn = None
        self.delete_btn = None

        # General settings
        self.prefs_page = None
        self.leases_box = None
        self.leases_stack_page = None
        self.xml_box = None

        self.__build__()

        # Only follow the events interesting for this network
        self.network.registerCallback(self.onConnectionEvent)

    def __build__(self):
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.title_widget = Adw.WindowTitle(title=self.network.getDisplayName())
        self.start_btn = iconButton(
            "",
            "play-symbolic",
            self.__onStartClicked__,
            css_classes=["suggested-action"],
            tooltip_text="Start",
        )
        self.stop_btn = iconButton(
            "",
            "stop-symbolic",
            self.__onStopClicked__,
            css_classes=["destructive-action"],
            tooltip_text="Stop",
        )
        self.back_btn = iconButton(
            "",
            "left-symbolic",
            self.__onBackClicked__,
            visible=False,
            margin_end=16,
        )

        toolbar_view = Adw.ToolbarView(hexpand=True, vexpand=True)
        self.append(toolbar_view)

        self.stack = Adw.ViewStack(hexpand=True, vexpand=True)
        toolbar_view.set_content(self.stack)

        self.apply_row = ApplyRow(
            self.__onApplyClicked__,
            self.__onCancelClicked__,
            "Changes only available after restart",
        )
        toolbar_view.add_bottom_bar(self.apply_row)

        switcher = Adw.ViewSwitcherBar(reveal=True, stack=self.stack)
        toolbar_view.add_bottom_bar(switcher)

        self.navigation_view = Adw.NavigationView()
        self.stack.add_titled_with_icon(
            self.navigation_view, "settings", "Settings", "settings-symbolic"
        )
        self.navigation_view.connect(
            "popped",
            lambda *_: self.back_btn.set_visible(
                self.navigation_view.get_visible_page() != self.main_nav_page
            ),
        )

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
            False, self.window_ref.window, self.showApply, self.__onDeleteClicked__
        )
        self.prefs_page.add(self.general_prefs_group)

        # Group with links to more settings
        self.link_group = Adw.PreferencesGroup()
        self.prefs_page.add(self.link_group)

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

        # DHCP leases
        self.leases_box = NetLeasePage(self)
        self.leases_stack_page = self.stack.add_titled_with_icon(
            self.leases_box, "dhcp", "Clients", "tag-outline-symbolic"
        )

        # XML
        self.xml_box = XMLView(self.showApply)
        self.stack.add_titled_with_icon(
            self.xml_box, "xml", "XML", "folder-code-legacy-symbolic"
        )

        self.stack.connect("notify::visible-child-name", self.__onStackChanged__)

        self.__updateData__()
        self.__setStatus__()

    def __updateData__(self):
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

    def __setStatus__(self):
        """Update visible elements depending on status."""
        if self.network.isActive():
            self.start_btn.set_visible(False)
            self.stop_btn.set_visible(True)
            self.title_widget.set_subtitle("up")

            self.leases_stack_page.set_visible(True)

            self.apply_row.setShowWarning(True)
        else:
            self.start_btn.set_visible(True)
            self.stop_btn.set_visible(False)
            self.title_widget.set_subtitle("down")

            self.leases_stack_page.set_visible(False)

            self.apply_row.setShowWarning(False)

    def showApply(self):
        """Show the apply row."""
        self.apply_row.set_visible(True)

    def onSubsettingsSelected(self, page):
        """Callback from subsettings-row that it was activated."""
        self.navigation_view.push(page)
        self.back_btn.set_visible(True)

    def __onStackChanged__(self, stack, _):
        """Hide the back-btn when not the main page is shown."""
        visible_child_name = stack.get_visible_child_name()
        if visible_child_name == "settings":
            self.back_btn.set_visible(
                self.navigation_view.get_visible_page() != self.main_nav_page
            )
        else:
            self.back_btn.set_visible(False)

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id):
        if type_id == CALLBACK_TYPE_NETWORK_GENERIC:
            if event_id == NETWORK_EVENT_DELETED:
                self.window_ref.window.closeTab(self)
                return
        elif type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.window_ref.window.closeTab(self)
                return
        self.__setStatus__()

    def __onApplyClicked__(self, _):
        self.network.setAutostart(self.general_prefs_group.getAutostart())

        try:
            if self.stack.get_visible_child_name() == "xml":
                self.network.updateDefinition(self.xml_box.getText())
            else:
                self.network.update(self.xml_tree)
            self.__updateData__()
        except Exception as e:
            self.window_ref.window.pushToastText(str(e))

    def __onCancelClicked__(self, _):
        self.__updateData__()

    def __onStartClicked__(self, _):
        self.start_btn.set_sensitive(False)
        failableAsyncJob(
            self.network.start,
            [],
            lambda e: self.window_ref.window.pushToastText(str(e)),
            lambda r: self.start_btn.set_sensitive(True),
        )

    def __onStopClicked__(self, _):
        def onStopSelected():
            self.stop_btn.set_sensitive(False)
            failableAsyncJob(
                self.network.stop,
                [],
                lambda e: self.window_ref.window.pushToastText(str(e)),
                lambda r: self.stop_btn.set_sensitive(True),
            )

        dialog = selectDialog(
            "Stop network?",
            "",
            [
                ActionOption(
                    "Stop",
                    onStopSelected,
                    appearance=Adw.ResponseAppearance.DESTRUCTIVE,
                )
            ],
        )
        dialog.present(self.window_ref.window)

    def __onBackClicked__(self, _):
        self.navigation_view.pop()

    def __onDeleteClicked__(self, btn):
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
        """Implement BaseDetailsTab."""
        # Unsubscribe from events
        self.network.unregisterCallback(self.onConnectionEvent)

    def getUniqueIdentifier(self) -> str:
        """Implement BaseDetailsTab."""
        return self.network.getUUID()

    def setWindowHeader(self, window):
        """Implement BaseDetailsTab."""
        window.headerSetTitleWidget(self.title_widget)
        window.headerPackStart(self.back_btn)
        window.headerPackStart(self.start_btn)
        window.headerPackStart(self.stop_btn)

    def getWindow(self) -> Adw.ApplicationWindow:
        return self.window_ref.window
