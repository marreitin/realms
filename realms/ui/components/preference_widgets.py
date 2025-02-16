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


def RealmsClamp() -> Adw.Clamp:
    return Adw.Clamp(
        tightening_threshold=400, maximum_size=750, margin_start=12, margin_end=12
    )


class RealmsPreferencesPage(Gtk.ScrolledWindow):
    def __init__(self, clamp: bool = True):
        super().__init__(
            hexpand=True,
            vexpand=True,
        )

        if clamp:
            self.__clamp__ = RealmsClamp()
            self.set_child(self.__clamp__)

            self.__box__ = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL,
                spacing=18,
                margin_start=0,
                margin_end=0,
                margin_top=6,
                margin_bottom=6,
            )
            self.__clamp__.set_child(self.__box__)
        else:
            self.__box__ = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL,
                spacing=18,
                margin_start=3,
                margin_end=3,
                margin_top=6,
                margin_bottom=6,
            )
            self.set_child(self.__box__)

        self.add = self.__box__.append
