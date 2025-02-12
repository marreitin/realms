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

from realms.libvirt_wrap.connection import Connection


class DomainPageHost:
    """Interface for widgets that contain a domain
    device page."""

    def getWindow(self) -> Adw.ApplicationWindow:
        """Get the current window."""
        raise NotImplementedError

    def getWindowRef(self) -> Adw.ApplicationWindow:
        """Get a reference to the current window."""
        raise NotImplementedError

    def getConnection(self) -> Connection:
        """Get the current connection."""
        raise NotImplementedError
