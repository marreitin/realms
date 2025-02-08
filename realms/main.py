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
"""Entrypoint for realms"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("GtkSource", "5")
gi.require_version("LibvirtGLib", "1.0")
gi.require_version("GtkSource", "5")

from gi.repository import Adw, Gio, LibvirtGLib

from realms.ui.main_window import MainWindow

from .helpers.settings import Settings


class MainApp(Adw.Application):
    """Main app instance."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_windows = []
        self.connect("activate", self.onActivate)

    def onActivate(self, *_):
        """Handler when the app becomes active."""
        # Hook libvirt events into glib main loop
        LibvirtGLib.init(None)
        LibvirtGLib.event_register()

        self.addWindow(True)

        self.loadConnections()

    def addWindow(self, primary=False) -> MainWindow:
        """Add a window to self, and return it -> important when opening window from dropping tabs

        Args:
            primary (bool, optional): If this window is a primary window. Defaults to False.

        Returns:
            MainWindow: Window that has been opened
        """
        win = MainWindow(primary)
        win.set_application(self)
        win.present()
        self.app_windows.append(win)
        return win

    def onWindowClosed(self, win):
        """Is called when a window closes. If the primary window closes, close all other windows."""
        if win.is_primary:
            for w in self.app_windows:
                w.close()
                w.destroy()
            self.app_windows.clear()
        else:
            win.close()
            win.destroy()
            self.app_windows.remove(win)
        return True

    def loadConnections(self):
        conns = Settings.get("connections")
        if conns is not None:
            for conn in conns:
                self.app_windows[0].addConnection(conn)
        if conns is None or len(conns) == 0:
            self.app_windows[0].nav_view.set_show_sidebar(False)


def main(*_):
    """Main function for realms."""
    Settings.prepare()

    app = MainApp(
        application_id="com.github.marreitin.realms",
        flags=Gio.ApplicationFlags.NON_UNIQUE,
    )
    app.run()


if __name__ == "__main__":
    main()
