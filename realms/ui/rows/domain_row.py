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
from gi.repository import Adw, Gio, Gtk, Pango

from realms.helpers.async_jobs import failableAsyncJob
from realms.helpers.show_domain_video import show
from realms.libvirt_wrap import Domain
from realms.libvirt_wrap.constants import *
from realms.ui.tabs import DomainDetailsTab

from .base_row import BaseRow


def __onContextStartClicked__(domainRow: any, *_):
    failableAsyncJob(
        domainRow.domain.start,
        [],
        lambda e: domainRow.window.pushToastText(str(e)),
        lambda r_: None,
    )


def __onContextStopClicked__(domainRow: any, *_):
    failableAsyncJob(
        domainRow.domain.shutdown,
        [],
        lambda e: domainRow.window.pushToastText(str(e)),
        lambda r_: None,
    )


def __onContextOpenClicked__(domainRow: any, *_):
    show(domainRow.domain, domainRow.window)


class DomainRow(BaseRow):
    def __init__(self, domain: Domain, window: Adw.ApplicationWindow):
        super().__init__()
        self.domain = domain
        self.window = window

        self.title = None
        self.subtitle = None
        self.status_icon = None

        self.popover = None

        self.__build__()

        self.domain.registerCallback(self.__onConnectionEvent__)

    def __build__(self):
        hbox = Gtk.Box(spacing=6)
        self.set_child(hbox)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        hbox.append(vbox)

        self.title = Gtk.Label(
            label=self.domain.getDisplayName(),
            halign=Gtk.Align.START,
            vexpand=True,
            css_classes=["caption-heading"],
            ellipsize=Pango.EllipsizeMode.END,
        )
        vbox.append(self.title)

        self.subtitle = Gtk.Label(
            label="unknown state",
            halign=Gtk.Align.START,
            css_classes=["caption", "dim-label"],
        )
        vbox.append(self.subtitle)

        self.status_icon = Gtk.Image.new_from_icon_name("computer-symbolic")
        self.status_icon.set_size_request(32, -1)
        hbox.append(self.status_icon)

        self.__buildContextMenu__()

        self.__setStatus__()

    def __buildContextMenu__(self):
        def openPopover(*_):
            menu = Gio.Menu()
            if self.domain.isActive():
                menu.append("Open", "domain.open")
                menu.append("Stop", "domain.stop")
            else:
                menu.append("Start", "domain.start")

            self.popover.set_menu_model(menu)
            self.popover.popup()

        self.install_action("domain.start", None, __onContextStartClicked__)
        self.install_action("domain.open", None, __onContextOpenClicked__)
        self.install_action("domain.stop", None, __onContextStopClicked__)

        self.popover = Gtk.PopoverMenu(has_arrow=False)
        self.popover.set_parent(self)

        gesture = Gtk.GestureClick(button=3)
        gesture.connect("pressed", openPopover)
        self.add_controller(gesture)

    def __setStatus__(self):
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

    def __onConnectionEvent__(self, conn, obj, type_id, event_id, detail_id):
        if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.domain.unregisterCallback(self.__onConnectionEvent__)
                return
        elif type_id == CALLBACK_TYPE_DOMAIN_GENERIC:
            if event_id == DOMAIN_EVENT_DELETED:
                self.domain.unregisterCallback(self.__onConnectionEvent__)
                return

        self.__setStatus__()

    def getSortingTitle(self):
        return self.domain.getDisplayName()
