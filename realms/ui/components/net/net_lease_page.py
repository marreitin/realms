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

from realms.libvirt_wrap import prettyTime
from realms.ui.components.common import iconButton, propertyRow

from .net_base_settings_page import BaseNetSettingsPage


class LeaseRow(Adw.ExpanderRow):
    def __init__(self, lease: dict, window: Adw.ApplicationWindow):
        title = f"{ lease['ipaddr'] }/{ lease['prefix'] }"
        if "hostname" in lease and lease["hostname"] is not None:
            title += f" ({ lease['hostname'] })"
        super().__init__(title=title)

        if "hostname" in lease and lease["hostname"] is not None:
            self.add_row(propertyRow("Hostname", subtitle=lease["hostname"]))
        self.add_row(propertyRow("Interface", subtitle=lease["iface"]))
        self.add_row(propertyRow("MAC-address", subtitle=lease["mac"]))
        if "clientid" in lease and lease["clientid"] is not None:
            self.add_row(propertyRow("Client ID", subtitle=lease["clientid"]))
        self.add_row(propertyRow("Expires", subtitle=prettyTime(lease["expirytime"])))


class NetLeasePage(BaseNetSettingsPage):
    def __init__(self, parent):
        super().__init__(parent)

        self.network = parent.network

        self.lease_rows = []

        self.prefs_group = None
        self.refresh_btn = None

        self.build()

    def listLeases(self, vir_leases):
        if vir_leases is None:
            self.prefs_group.set_description(
                "This action is not supported by the driver"
            )
            return

        self.prefs_group.set_description("")
        for lease in vir_leases:
            row = LeaseRow(lease, self.parent.window_ref.window)
            self.lease_rows.append(row)
            self.prefs_group.add(row)

    def build(self):
        self.prefs_group = Adw.PreferencesGroup(title="DHCP leases")
        self.prefs_page.add(self.prefs_group)

        self.refresh_btn = iconButton(
            "",
            "update-symbolic",
            self.onRefresh,
            tooltip_text="Refresh",
            css_classes=["flat"],
        )
        self.prefs_group.set_header_suffix(self.refresh_btn)

        self.onRefresh()

    def onRefresh(self, *args):
        for row in self.lease_rows:
            self.prefs_group.remove(row)
        self.lease_rows.clear()
        self.network.getDHCPLeases(self.listLeases)
