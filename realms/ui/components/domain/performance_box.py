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

from realms.libvirt_wrap.domain import Domain
from realms.ui.components.generic_preferences_row import GenericPreferencesRow
from realms.ui.components.graphs import DataPoint, DataSeries, Graph, RelativeDataPoint
from realms.ui.components.preference_widgets import RealmsPreferencesPage


class PerformanceBox(Gtk.Box):
    def __init__(self, domain: Domain):
        REFRESH_SECONDS = 1
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        page = RealmsPreferencesPage()
        self.append(page)

        group = Adw.PreferencesGroup()
        page.add(group)

        # CPU graph
        row = GenericPreferencesRow()
        group.add(row)

        self.cpu_data_series = DataSeries(
            [RelativeDataPoint(0, domain.getCPUTime())], 1, 120
        )

        def getCPUData():
            cpu_time_reading = domain.getCPUTime()
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
            display_val /= domain.getVCPUs()
            display_val /= 1000000000 * REFRESH_SECONDS
            return RelativeDataPoint(display_val, cpu_time_reading)

        self.cpu_data_series.setWatchCallback(1000 * REFRESH_SECONDS, getCPUData)
        self.cpu_graph = Graph(self.cpu_data_series, "CPU")
        row.addChild(self.cpu_graph)

        # Memory graph
        row = GenericPreferencesRow()
        group.add(row)

        self.mem_data_series = DataSeries([DataPoint(0)], domain.getMaxMemory(), 120)

        def getMemData():
            return DataPoint(domain.getMemoryUsage())

        self.mem_data_series.setWatchCallback(1000 * REFRESH_SECONDS, getMemData)
        self.mem_graph = Graph(self.mem_data_series, "Memory")
        row.addChild(self.mem_graph)

    def end(self):
        self.cpu_data_series.stopWatchCallback()
        self.mem_data_series.stopWatchCallback()
