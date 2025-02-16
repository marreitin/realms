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


class GenericPreferencesRow(Adw.PreferencesRow):
    """Base class for a row that fits into Adw.PreferenceGroup,
    but offers a box to hold other widgets.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.outer_box = Gtk.Box(
            spacing=6,
            margin_top=12,
            margin_bottom=12,
            margin_start=12,
            margin_end=12,
            orientation=Gtk.Orientation.VERTICAL,
        )

        super().set_child(self.outer_box)

    def addChild(self, widget: Gtk.Widget) -> None:
        """Add a child to this row (vertical)."""
        self.outer_box.append(widget)

    def removeChild(self, widget: Gtk.Widget) -> None:
        """Remove the given child from this row."""
        self.outer_box.remove(widget)
