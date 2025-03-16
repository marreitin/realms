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

from realms.helpers import RepeatJob
from realms.libvirt_wrap import Pool
from realms.libvirt_wrap.constants import *
from realms.ui.tabs import PoolDetailsTab

from .base_row import BaseRow


class PoolRow(BaseRow):
    """Sidebar Row for storage pools."""

    def __init__(self, pool: Pool, window: Adw.ApplicationWindow):
        super().__init__()
        self.pool = pool
        self.window = window

        self.usage_task = None

        self.title = None
        self.subtitle = None
        self.status_label = None

        self.__build__()

        self.pool.registerCallback(self.__onConnectionEvent__)

    def __build__(self):
        hbox = Gtk.Box(spacing=6)
        self.set_child(hbox)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        hbox.append(vbox)

        self.title = Gtk.Label(
            label=self.pool.getDisplayName(),
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

        self.status_label = Gtk.Label(label="50%", justify=Gtk.Justification.RIGHT)
        hbox.append(self.status_label)

        self.__setStatus__()

    def __setStatus__(self):
        self.status_label.set_css_classes([])

        def gatherUsage():
            filled = self.pool.getAllocation() / self.pool.getCapacity() * 100
            return filled

        def showUsage(filled):
            self.status_label.set_label(str(int(filled)) + "%")

            if filled > 90:
                self.status_label.set_css_classes(["numeric", "error"])
            elif filled > 70:
                self.status_label.set_css_classes(["numeric", "warning"])
            else:
                self.status_label.set_css_classes(["numeric"])

        if self.usage_task is None:
            self.usage_task = RepeatJob(gatherUsage, [], showUsage, 30)

        if self.pool.isActive():
            self.subtitle.set_label("active")
        else:
            self.subtitle.set_label("inactive")

    def __onConnectionEvent__(self, conn, obj, type_id, event_id, detail_id):
        if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.usage_task.stopTask()
                self.pool.unregisterCallback(self.__onConnectionEvent__)
                return
        elif type_id == CALLBACK_TYPE_POOL_GENERIC:
            if event_id == POOL_EVENT_DELETED:
                self.usage_task.stopTask()
                self.pool.unregisterCallback(self.__onConnectionEvent__)

        self.__setStatus__()

    # Implement BaseRow
    def onActivate(self):
        uuid = self.pool.getUUID()
        if not self.window.tabExists(uuid):
            tab_page_content = PoolDetailsTab(self.pool, self.window)
            self.window.addOrShowTab(
                tab_page_content, self.pool.getDisplayName(), "drive-multidisk-symbolic"
            )

    # Implement BaseRow
    def getSortingTitle(self):
        return self.pool.getDisplayName()
