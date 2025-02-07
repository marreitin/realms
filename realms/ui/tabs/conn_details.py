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
from gi.repository import Adw

from realms.libvirt_wrap import Connection
from realms.libvirt_wrap.constants import *
from realms.ui.builders.conn import (
    ConnectionDetailsPage,
    ConnectionPerformancePage,
    SecretsPage,
)

from .base_details import *


class ConnectionDetailsTab(BaseDetailsTab):
    """Class providing an editing tab for a libvirt connection."""

    def __init__(self, connection: Connection, window: Adw.ApplicationWindow):
        super().__init__(window)

        self.connection = connection
        self.connection.register_callback_any(self.onConnectionEvent, None)

        self.stack = None
        self.stack_switcher = None

        self.conn_details_page = None
        self.secrets_page = None
        self.perf_page = None

        self.build()

    def build(self):
        self.set_hexpand(True)
        self.set_vexpand(True)

        toolbar_view = Adw.ToolbarView(hexpand=True, vexpand=True)
        self.append(toolbar_view)

        self.stack = Adw.ViewStack(hexpand=True, vexpand=True)
        toolbar_view.set_content(self.stack)

        self.stack_switcher = Adw.ViewSwitcherBar(reveal=True, stack=self.stack)
        toolbar_view.add_bottom_bar(self.stack_switcher)

        self.conn_details_page = ConnectionDetailsPage(self)
        self.stack.add_titled_with_icon(
            self.conn_details_page,
            "settings",
            "Settings",
            "settings-symbolic",
        )

        if self.connection.supports_secrets:
            self.secrets_page = SecretsPage(self)
            self.stack.add_titled_with_icon(
                self.secrets_page, "secrets", "Secrets", "padlock2-symbolic"
            )

        self.perf_page = ConnectionPerformancePage(self)
        self.stack.add_titled_with_icon(
            self.perf_page, "performance", "Performance", "speedometer5-symbolic"
        )

        self.setStatus()

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id, opaque):
        if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id == CONNECTION_EVENT_SETTINGS_CHANGED:
                self.conn_details_page.loadSettings()
            elif event_id == CONNECTION_EVENT_DELETED:
                self.window_ref.window.closeTab(self)
        self.setStatus()

    def setStatus(self):
        state = self.connection.getState()
        if state == CONNECTION_STATE_CONNECTED:
            self.stack_switcher.set_reveal(True)

            self.perf_page.start()
        elif state == CONNECTION_STATE_CONNECTING:
            self.stack_switcher.set_reveal(False)
        else:
            self.stack_switcher.set_reveal(False)
            # Important to not be stuck on secrets page upon disconnection
            self.stack.set_visible_child_name("settings")

            self.perf_page.end()

        self.conn_details_page.setStatus()

    def end(self):
        # Unsubscribe from events
        self.connection.unregister_callback(self.onConnectionEvent)

        # Stop pages
        self.perf_page.end()

    def getUniqueIdentifier(self) -> str:
        return self.connection.url
