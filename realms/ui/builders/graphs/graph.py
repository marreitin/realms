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
from gi.repository import Adw, Gsk, Gtk

from .data_series import DataPoint, DataSeries


class Graph(Gtk.Frame):
    """Simple and minimalist graph drawing a DataSeries."""

    def __init__(self, data_series: DataSeries):
        super().__init__(
            hexpand=True,
            vexpand=True,
            margin_top=12,
            margin_end=12,
            margin_bottom=12,
            margin_start=12,
        )
        self.set_margin_top(3)
        self.vpadding = 3
        self.data_series = data_series
        self.data_series.registerRedrawCallback(self.onRedraw)

    def onRedraw(self):
        # Only redraw if the widget is visible
        if self.is_drawable():
            self.queue_draw()

    def fitValue(self, p: DataPoint) -> float:
        """Calculate the y-coordinate of a given point"""
        value = (
            self.vpadding
            + (self.get_height() - 2 * self.vpadding)
            - (self.get_height() - self.vpadding)
            * (p.value / self.data_series.max_value)
        )
        value = max(self.vpadding, value)
        value = min(self.get_height() - self.vpadding, value)
        return value

    def do_snapshot(self, snapshot, *_):
        """Main widget implementation, here the widget will be actually redrawn.

        Args:
            snapshot (Gtk.Snapshot): Snapshot object to draw to
        """
        style_manager = Adw.StyleManager.get_default()
        line_color = style_manager.get_accent_color_rgba()

        # Build path
        if len(self.data_series) < 2:
            return  # A line needs at least two points

        builder = Gsk.PathBuilder()
        move_width = self.get_width() / (self.data_series.max_size - 1)
        start_x = (self.data_series.max_size - len(self.data_series)) * move_width
        builder.move_to(
            start_x,
            self.fitValue(self.data_series.getFirst()),
        )
        for i, v in enumerate(self.data_series.values):
            builder.line_to(
                start_x + i * move_width,
                self.fitValue(v),
            )

        path = builder.to_path()

        snapshot.append_stroke(path, Gsk.Stroke(3), line_color)

        builder.add_path(path)
        builder.line_to(self.get_width(), self.get_height())
        builder.line_to(start_x, self.get_height())
        builder.line_to(start_x, self.fitValue(self.data_series.getFirst()))

        snapshot.push_opacity(0.2)
        snapshot.append_fill(builder.to_path(), Gsk.FillRule.WINDING, line_color)
        snapshot.pop()
