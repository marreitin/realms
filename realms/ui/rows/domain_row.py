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
import libvirt
from gi.repository import Adw, Gtk

from realms.libvirt_wrap import Domain
from realms.libvirt_wrap.constants import *
from realms.ui.tabs import DomainDetailsTab

from .base_row import BaseRow


class DomainRow(BaseRow):
    def __init__(self, domain: Domain, window: Adw.ApplicationWindow):
        super().__init__()
        self.domain = domain
        self.window = window

        self.title = None
        self.subtitle = None
        self.status_icon = None

        self.build()

        self.domain.register_callback_any(self.onConnectionEvent, None)

    def build(self):
        hbox = Gtk.Box(spacing=6)
        self.set_child(hbox)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        hbox.append(vbox)

        self.title = Gtk.Label(
            label=self.domain.getDisplayName(), halign=Gtk.Align.START, vexpand=True
        )
        self.title.set_css_classes(["caption-heading"])
        vbox.append(self.title)

        self.subtitle = Gtk.Label(label="unknown state", halign=Gtk.Align.START)
        self.subtitle.set_css_classes(["caption", "dim-label"])
        vbox.append(self.subtitle)

        self.status_icon = Gtk.Image.new_from_icon_name("computer-symbolic")
        self.status_icon.set_size_request(32, -1)
        hbox.append(self.status_icon)

        self.setStatus()

    def setStatus(self):
        self.status_icon.set_css_classes([])

        self.title.set_label(self.domain.getDisplayName())
        self.subtitle.set_label(self.domain.getStateText())
        state = self.domain.getStateID()
        if state == libvirt.VIR_DOMAIN_NOSTATE:
            self.status_icon.set_from_icon_name("computer-grey")
        elif state == libvirt.VIR_DOMAIN_RUNNING:
            self.status_icon.set_from_icon_name("computer")
        elif state == libvirt.VIR_DOMAIN_BLOCKED:
            self.status_icon.set_from_icon_name("computer-grey")
        elif state == libvirt.VIR_DOMAIN_PAUSED:
            self.status_icon.set_from_icon_name("computer-grey")
        elif state == libvirt.VIR_DOMAIN_SHUTDOWN:
            self.status_icon.set_from_icon_name("computer")
        elif state == libvirt.VIR_DOMAIN_SHUTOFF:
            self.status_icon.set_from_icon_name("computer-grey")
        elif state == libvirt.VIR_DOMAIN_CRASHED:
            self.status_icon.set_from_icon_name("computer-red")
        elif state == libvirt.VIR_DOMAIN_PMSUSPENDED:
            self.status_icon.set_from_icon_name("computer-grey")

    def onActivate(self):
        uuid = self.domain.getUUID()
        if not self.window.tabExists(uuid):
            tab_page_content = DomainDetailsTab(self.domain, self.window)
            self.window.addOrShowTab(
                tab_page_content, self.domain.getDisplayName(), "computer-symbolic"
            )

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id, opaque):
        if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.domain.unregister_callback(self.onConnectionEvent)
                return
        elif type_id == CALLBACK_TYPE_DOMAIN_GENERIC:
            if event_id == DOMAIN_EVENT_DELETED:
                self.domain.unregister_callback(self.onConnectionEvent)
                return

        self.setStatus()

    def getSortingTitle(self):
        return self.domain.getDisplayName()
