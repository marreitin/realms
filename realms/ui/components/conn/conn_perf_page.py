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
from gi.repository import Gtk

from realms.ui.components.graphs import DataPoint, DataSeries, Graph, RelativeDataPoint


class ConnectionPerformancePage(Gtk.Box):
    """Graphs showing some performance info for a hypervisor."""

    REFRESH_SECONDS = 1

    def __init__(self, parent):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.parent = parent
        self.is_started = False

        self.build()

    def build(self):
        """Build self."""
        # CPU graph
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.append(box)
        box.append(
            Gtk.Label(
                label="CPU",
                css_classes=["heading"],
                halign=Gtk.Align.START,
                margin_start=12,
            )
        )

        self.cpu_data_series = DataSeries([], 1, 120)
        self.cpu_graph = Graph(self.cpu_data_series)
        box.append(self.cpu_graph)

        # Second row
        hbox = Gtk.Box(spacing=6)
        self.append(hbox)

        # IOWait graph
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        hbox.append(box)
        box.append(
            Gtk.Label(
                label="I/O-wait",
                css_classes=["heading"],
                halign=Gtk.Align.START,
                margin_start=12,
            )
        )

        self.iowait_data_series = DataSeries([], 1, 60)
        self.iowait_graph = Graph(self.iowait_data_series)
        box.append(self.iowait_graph)

        # Memory graph
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        hbox.append(box)
        box.append(
            Gtk.Label(
                label="Memory",
                css_classes=["heading"],
                halign=Gtk.Align.START,
                margin_start=12,
            )
        )
        self.mem_data_series = DataSeries([], 1, 60)
        self.mem_graph = Graph(self.mem_data_series)
        box.append(self.mem_graph)

    def start(self):
        """Start collecting information."""
        if self.is_started:
            return

        self.is_started = True

        self.cpu_data_series.setValues(
            [RelativeDataPoint(0, self.parent.connection.getHostCPUTime())]
        )

        def getCPUData():
            cpu_time_reading = self.parent.connection.getHostCPUTime()
            display_val = 0
            if len(self.cpu_data_series) > 1:
                display_val = abs(
                    self.cpu_data_series.values[-2].last_reading - cpu_time_reading
                )
                display_val /= 2
            else:
                display_val = abs(
                    self.cpu_data_series.getLast().last_reading - cpu_time_reading
                )
            display_val /= 1000000000 * self.REFRESH_SECONDS
            return RelativeDataPoint(display_val, cpu_time_reading)

        self.cpu_data_series.setWatchCallback(1000 * self.REFRESH_SECONDS, getCPUData)

        self.iowait_data_series.setValues(
            [RelativeDataPoint(0, self.parent.connection.getHostIOWait())]
        )

        def getIOwaitData():
            iowait_time_reading = self.parent.connection.getHostIOWait()
            display_val = 0
            if len(self.iowait_data_series) > 1:
                display_val = abs(
                    self.iowait_data_series.values[-2].last_reading
                    - iowait_time_reading
                )
                display_val /= 2
            else:
                display_val = abs(
                    self.iowait_data_series.getLast().last_reading - iowait_time_reading
                )
            display_val /= 1000000000 * self.REFRESH_SECONDS
            return RelativeDataPoint(display_val, iowait_time_reading)

        self.iowait_data_series.setWatchCallback(
            1000 * self.REFRESH_SECONDS, getIOwaitData
        )
        self.mem_data_series.setValues([])
        self.mem_data_series.max_value = self.parent.connection.maxMemory()

        def getMemData():
            return DataPoint(self.parent.connection.getHostMemoryUsage() * 1024)

        self.mem_data_series.setWatchCallback(1000 * self.REFRESH_SECONDS, getMemData)

    def end(self):
        """Stop gathering information."""
        self.cpu_data_series.stopWatchCallback()
        self.iowait_data_series.stopWatchCallback()
        self.mem_data_series.stopWatchCallback()
        self.is_started = False
