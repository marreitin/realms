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
from gi.repository import Adw, Gtk, Pango

from realms.libvirt_wrap import Network
from realms.libvirt_wrap.constants import *
from realms.ui.tabs import NetworkDetailsTab

from .base_row import BaseRow


class NetworkRow(BaseRow):
    def __init__(self, network: Network, window: Adw.ApplicationWindow):
        super().__init__()
        self.network = network
        self.window = window

        self.title = None
        self.subtitle = None

        self.build()

        self.network.register_callback_any(self.onConnectionEvent, None)

    def build(self):
        self.set_activatable(True)
        self.set_selectable(True)

        outer_box = Gtk.Box(margin_top=3, margin_bottom=3, spacing=6)
        self.set_child(outer_box)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer_box.append(box)

        self.title = Gtk.Label(
            label=self.network.getDisplayName(),
            halign=Gtk.Align.START,
            vexpand=True,
            css_classes=["caption-heading"],
            ellipsize=Pango.EllipsizeMode.END,
        )
        box.append(self.title)

        self.subtitle = Gtk.Label(label="eth0")
        box.append(self.subtitle)
        self.subtitle.set_halign(Gtk.Align.START)
        self.subtitle.set_css_classes(["caption", "dim-label"])

        self.set_status()

    def onActivate(self):
        uuid = self.network.getUUID()
        if not self.window.tabExists(uuid):
            tab_page_content = NetworkDetailsTab(self.network, self.window)
            self.window.addOrShowTab(
                tab_page_content,
                self.network.getDisplayName(),
                "network-wired-symbolic",
            )

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id, opaque):
        if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.network.unregister_callback(self.onConnectionEvent)
                return
        elif type_id == CALLBACK_TYPE_NETWORK_GENERIC:
            if event_id == NETWORK_EVENT_DELETED:
                self.network.unregister_callback(self.onConnectionEvent)
        self.set_status()

    def set_status(self):
        self.title.set_label(self.network.getDisplayName())
        if self.network.isActive():
            self.subtitle.set_text("up")
        else:
            self.subtitle.set_text("down")

    def getSortingTitle(self):
        return self.network.getDisplayName()
