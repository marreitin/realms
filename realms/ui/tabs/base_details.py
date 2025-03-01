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
from gi.repository import Adw, Gtk

from realms.ui.window_reference import WindowReference


class BaseDetailsTab(Gtk.Box):
    """Base class for any tabs that are shown in the main window area."""

    def __init__(self, window: Adw.ApplicationWindow, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.window_ref = WindowReference(window)

    def setWindow(self, window: Adw.ApplicationWindow):
        """Change the window reference of the current tab's contents."""
        self.window_ref.window = window

    def end(self) -> None:
        """Will be called once a tab gets closed to release any resources."""
        raise NotImplementedError

    def setWindowHeader(self, window: Adw.ApplicationWindow):
        """Implement callback when this tab is presented. It is
        used to add control buttons to the main windows headerbar."""
        raise NotImplementedError

    def getUniqueIdentifier(self) -> str:
        """Return a unique identifier for this tab, used to prevent duplicate tabs
        inside a window.

        Returns:
            str: Unique identifier
        """
        raise NotImplementedError
