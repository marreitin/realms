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
"""Implementation of a graph that will automatically plot
with a given DataSeries."""
from gi.repository import Adw, Gsk, Gtk

from .data_series import DataPoint, DataSeries


class InnerGraph(Gtk.Frame):
    """A Gtk Frame that draws the actual graph."""

    def __init__(self, data_series: DataSeries):
        """Initialize InnerGraph with a data series

        Args:
            data_series (DataSeries): DataSeries to plot
        """
        super().__init__(height_request=200)

        self.__vpadding__ = 1
        self.__data_series__ = data_series
        self.__data_series__.registerRedrawCallback(self.__onRedraw__)

        style_manager = Adw.StyleManager.get_default()
        self.__line_color__ = style_manager.get_accent_color_rgba()

    def __onRedraw__(self):
        # Only redraw if the widget is visible
        if self.is_drawable():
            self.queue_draw()

    def __fitValue__(self, p: DataPoint) -> float:
        """Calculate the y-coordinate of a given point"""
        value = (
            self.__vpadding__
            + (self.get_height() - 2 * self.__vpadding__)
            - (self.get_height() - self.__vpadding__)
            * (p.value / self.__data_series__.max_value)
        )
        value = max(self.__vpadding__, value)
        value = min(self.get_height() - self.__vpadding__, value)
        return value

    # pylint: disable-next=invalid-name
    def do_snapshot(self, snapshot, *_):
        """Main widget implementation, here the widget will be actually redrawn.

        Args:
            snapshot (Gtk.Snapshot): Snapshot object to draw to
        """

        # Build path
        if len(self.__data_series__) < 2:
            return  # A line needs at least two points

        builder = Gsk.PathBuilder()
        move_width = self.get_width() / (self.__data_series__.max_size - 1)
        start_x = (
            self.__data_series__.max_size - len(self.__data_series__)
        ) * move_width
        builder.move_to(
            start_x,
            self.__fitValue__(self.__data_series__.getFirst()),
        )
        for i, v in enumerate(self.__data_series__.values):
            builder.line_to(
                start_x + i * move_width,
                self.__fitValue__(v),
            )

        path = builder.to_path()

        snapshot.append_stroke(path, Gsk.Stroke(3), self.__line_color__)

        builder.add_path(path)
        builder.line_to(self.get_width(), self.get_height())
        builder.line_to(start_x, self.get_height())
        builder.line_to(start_x, self.__fitValue__(self.__data_series__.getFirst()))

        snapshot.push_opacity(0.2)
        snapshot.append_fill(
            builder.to_path(), Gsk.FillRule.WINDING, self.__line_color__
        )
        snapshot.pop()


class Graph(Gtk.Box):
    """Simple and minimalist graph drawing a DataSeries."""

    def __init__(self, data_series: DataSeries, title: str):
        """Create Graph

        Args:
            data_series (DataSeries): Data series to draw
            title (str): Title for graph
        """
        super().__init__(
            hexpand=True, vexpand=True, orientation=Gtk.Orientation.VERTICAL
        )

        title_box = Gtk.Box(spacing=12, margin_top=3, margin_bottom=3)
        self.append(title_box)
        title_box.append(
            Gtk.Label(label=title, halign=Gtk.Align.START, css_classes=["heading"])
        )

        self.__frame__ = InnerGraph(data_series)
        self.append(self.__frame__)
