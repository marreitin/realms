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

from realms.libvirt_wrap.connection import Connection


class NetworkChooserRow(Adw.ComboRow):
    """A widget two pick a network on the given connection."""

    def __init__(self, connection: Connection, on_changed_cb: callable, **kwargs):
        super().__init__(sensitive=False, **kwargs)

        self.__connection__ = connection
        self.__on_changed_cb__ = on_changed_cb

        self.__networks__ = None

        self.__connection__.listNetworks(self.__setNetworks__)

    def __setNetworks__(self, vir_nets: list[libvirt.virNetwork]):
        vir_nets.sort(key=lambda e: e.name())
        network_names = [n.name() for n in vir_nets]
        self.set_model(Gtk.StringList(strings=network_names))
        self.set_sensitive(True)

        self.__networks__ = vir_nets

    def connectOnChanged(self, on_changed_cb: callable):
        """Add a callback to call when the selected volume changed."""
        self.__on_changed_cb__ = on_changed_cb

    def getNetwork(self) -> libvirt.virNetwork:
        """Get the currently selected network."""
        return self.__networks__[self.get_selected()]
