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

from realms.ui.components.common import hspacer

from .data_series import DataPoint, DataSeries


class InnerGraph(Gtk.Box):
    """A Gtk Frame that draws the actual graph. It is only the
    inner widget and not to be used directly."""

    def __init__(self, parent, data_series: list[DataSeries], value_text: callable):
        """Initialize InnerGraph with a data series

        Args:
            data_series (DataSeries): DataSeries to plot
        """
        super().__init__(height_request=200)

        self.parent = parent
        self.__data_series__ = data_series
        self.value_text = value_text

        colors = [
            Adw.AccentColor.BLUE,
            Adw.AccentColor.ORANGE,
            Adw.AccentColor.GREEN,
            Adw.AccentColor.PINK,
            Adw.AccentColor.PURPLE,
            Adw.AccentColor.RED,
            Adw.AccentColor.SLATE,
            Adw.AccentColor.TEAL,
            Adw.AccentColor.YELLOW,
        ]
        index = 0
        for ds in self.__data_series__:
            if ds.color is None:
                ds.color = colors[index]
                index += 1
            ds.registerRedrawCallback(self.__onRedraw__)

    def __onRedraw__(self):
        # Only redraw if the widget is visible
        if self.is_drawable():
            self.queue_draw()

    def __fitValue__(self, ds: DataSeries, p: DataPoint, width, height) -> float:
        """Calculate the y-coordinate of a given point"""
        value = height - height * (p.value / ds.getMaxValue())
        value = max(0, value)
        value = min(height, value)
        return value

    # pylint: disable-next=invalid-name
    def do_snapshot(self, snapshot, *_):
        """Main widget implementation, here the widget will be actually redrawn.

        Args:
            snapshot (Gtk.Snapshot): Snapshot object to draw to
        """

        # Build path
        for ds in self.__data_series__:
            self.__drawDataSeries__(snapshot, ds)

        self.parent.setValueLabel(self.value_text(self.__data_series__))

    def __drawDataSeries__(self, snapshot, ds: DataSeries):
        if len(ds) < 2:
            return  # A line needs at least two points

        width = self.get_width()
        height = self.get_height()

        color = ds.color.to_rgba()
        builder = Gsk.PathBuilder()
        move_width = width / (ds.max_size - 1)
        start_x = (ds.max_size - len(ds)) * move_width
        start_y = self.__fitValue__(ds, ds.getFirst(), width, height)
        builder.move_to(
            start_x,
            start_y,
        )
        for i, v in enumerate(ds.values):
            builder.line_to(
                start_x + i * move_width,
                self.__fitValue__(ds, v, width, height),
            )

        path = builder.to_path()

        snapshot.append_stroke(path, Gsk.Stroke(2), color)

        builder.add_path(path)
        builder.line_to(width, height)
        builder.line_to(start_x, height)
        builder.line_to(start_x, start_y)

        if ds.fill:
            snapshot.push_opacity(0.3)
            snapshot.append_fill(builder.to_path(), Gsk.FillRule.WINDING, color)
            snapshot.pop()


class Graph(Gtk.Box):
    """Simple and minimalist graph drawing a list of DataSeries."""

    def __init__(
        self, data_series: list[DataSeries], title: str, value_text: callable = None
    ):
        """Create Graph

        Args:
            data_series (DataSeries): Data series to draw
            title (str): Title for graph
            value_text (callable): Function to create the value text for this graph
        """
        super().__init__(
            hexpand=True, vexpand=True, orientation=Gtk.Orientation.VERTICAL
        )

        if value_text is None:
            value_text = lambda *_: ""

        title_box = Gtk.Box(spacing=12, margin_top=2, margin_bottom=2)
        self.append(title_box)
        title_box.append(
            Gtk.Label(label=title, halign=Gtk.Align.START, css_classes=["heading"])
        )

        title_box.append(hspacer())

        self.value_label = Gtk.Label(
            css_classes=["numeric", "dimmed"], halign=Gtk.Align.END
        )
        title_box.append(self.value_label)

        self.__frame__ = InnerGraph(self, data_series, value_text)
        self.append(self.__frame__)

    def setValueLabel(self, label: str):
        """Set the text of the value label."""
        self.value_label.set_label(label)
