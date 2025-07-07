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
"""DataSeries provide a way of storing a set number of data-points, and
updating them regularly."""
from gi.repository import Adw, GLib

from realms.helpers import asyncJob


class DataPoint:
    """General point for a DataSeries"""

    def __init__(self, value: any):
        self.value = value


class RelativeDataPoint(DataPoint):
    """Extended DataPoint that can carry the plain measurement value of the
    last measurement, i.e. for plotting CPU usage when only CPU time values
    are accessible.
    """

    def __init__(self, value: any, last_reading):
        super().__init__(value)
        self.last_reading = last_reading


class DataSeries:
    """Main data class that is used by the graphs. It manages all it's points
    automatically, executes periodic data gathering operations and can notify
    graphs that a redraw is needed.
    """

    def __init__(
        self,
        initial_values: list[DataPoint],
        max_value: any,
        max_size: int,
        color: Adw.AccentColor = None,
        fill: bool = True,
    ):
        self.redraw_cb = None
        self.values = initial_values
        self.max_value = max_value
        self.max_size = max_size
        self.color = color
        self.fill = fill

        self.watch_cb = None

    def __len__(self) -> int:
        return len(self.values)

    def setWatchCallback(self, watch_timeout: int, watch_cb: callable) -> None:
        """Add a callback to go and get the next data point

        Args:
            watch_timeout (int): Interval in ms at which the cb is called
            watch_cb (callable): Callback, must return a single DataPoint
        """
        self.watch_cb = watch_cb

        def onTimeout(*_):
            if self.watch_cb is None:
                return False  # Cancel timeout
            asyncJob(self.watch_cb, [self], self.pushValue)
            return True

        GLib.timeout_add(watch_timeout, onTimeout)

    def stopWatchCallback(self) -> None:
        """Remove the watch callback, it will no longer be called"""
        self.watch_cb = None

    def registerRedrawCallback(self, redraw_cb: callable) -> None:
        """Register a callback for when redrawing is required, i.e.
        when a new point was added.

        Args:
            redraw_cb (callable): Callback scheduling a redraw
        """
        self.redraw_cb = redraw_cb

    def unregisterRedrawCallback(self) -> None:
        """Remove the redraw callback, it will no longer be called"""
        self.redraw_cb = None

    def triggerRedraw(self):
        if self.redraw_cb is not None and len(self.values) > 1:
            self.redraw_cb()

    def pushValue(self, value: DataPoint) -> None:
        """Add a DataPoint to this series. Will notify the graph to redraw.

        Args:
            value (DataPoint): DataPoint to add
        """
        self.values.append(value)
        while len(self.values) > self.max_size:
            self.values.pop(0)
        self.triggerRedraw()

    def setMaxSize(self, max_size: int) -> None:
        """Set a different maximum size. When the size is reduced,
        the oldest points will be discarded.

        Args:
            max_size (int): _description_
        """
        self.max_size = max_size
        while len(self.values) > self.max_size:
            self.values.pop(0)
        self.triggerRedraw()

    def setValues(self, values: list[DataPoint]):
        """Replace the series' values

        Args:
            values (list[DataPoint]): New data points, oldest points will be discarded
                until max size is reached
        """
        self.values = values
        while len(self.values) > self.max_size:
            self.values.pop(0)
        self.triggerRedraw()

    def getLast(self) -> DataPoint:
        """Get the last data point."""
        return self.values[-1]

    def getFirst(self) -> DataPoint:
        """Get the first data point."""
        return self.values[0]

    def getMaxValue(self) -> any:
        """Get the (current) maximum value of this data series."""
        if self.max_value is None:
            val = max([dp.value for dp in self.values])
            return val if val != 0 else 1
        return self.max_value
