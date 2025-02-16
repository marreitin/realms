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

from realms.ui.components.generic_preferences_row import GenericPreferencesRow
from realms.ui.components.graphs import DataPoint, DataSeries, Graph, RelativeDataPoint
from realms.ui.components.preference_widgets import RealmsPreferencesPage


class ConnectionPerformancePage(Gtk.Box):
    """Graphs showing some performance info for a hypervisor."""

    REFRESH_SECONDS = 1

    def __init__(self, parent):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.parent = parent
        self.is_started = False

        page = RealmsPreferencesPage()
        self.append(page)

        group = Adw.PreferencesGroup()
        page.add(group)

        # CPU graph
        row = GenericPreferencesRow()
        group.add(row)

        self.cpu_data_series = DataSeries([], 1, 120)
        self.cpu_graph = Graph(self.cpu_data_series, "CPU")
        row.addChild(self.cpu_graph)

        # Memory graph
        row = GenericPreferencesRow()
        group.add(row)

        self.mem_data_series = DataSeries([], 1, 120)
        self.mem_graph = Graph(self.mem_data_series, "Memory")
        row.addChild(self.mem_graph)

        # IOWait graph
        row = GenericPreferencesRow()
        group.add(row)

        self.iowait_data_series = DataSeries([], 1, 120)
        self.iowait_graph = Graph(self.iowait_data_series, "IO-Wait")
        row.addChild(self.iowait_graph)

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
        self.mem_data_series.setValues([DataPoint(0)])
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
