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
    """Box containing the performance graphs of a domain."""

    def __init__(self, domain: Domain):
        REFRESH_SECONDS = 0.2
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        page = RealmsPreferencesPage()
        self.append(page)

        group = Adw.PreferencesGroup()
        page.add(group)

        # CPU graph
        row = GenericPreferencesRow()
        row.set_activatable(False)
        group.add(row)

        self.__cpu_data_series__ = DataSeries(
            [RelativeDataPoint(0, domain.getCPUTime())], 1, 600
        )

        def getCPUData():
            cpu_time_reading = domain.getCPUTime()
            display_val = 0
            if len(self.__cpu_data_series__) > 1:
                display_val = abs(
                    self.__cpu_data_series__.values[-2].last_reading - cpu_time_reading
                )
                display_val /= 2
            else:
                display_val = abs(
                    self.__cpu_data_series__.getLast().last_reading - cpu_time_reading
                )
            display_val /= domain.getVCPUs()
            display_val /= 1000000000 * REFRESH_SECONDS
            return RelativeDataPoint(display_val, cpu_time_reading)

        self.__cpu_data_series__.setWatchCallback(1000 * REFRESH_SECONDS, getCPUData)
        self.__cpu_graph__ = Graph([self.__cpu_data_series__], "CPU")
        row.addChild(self.__cpu_graph__)

        # Memory graph
        row = GenericPreferencesRow()
        row.set_activatable(False)
        group.add(row)

        self.__mem_data_series__ = DataSeries(
            [DataPoint(0)], domain.getMaxMemory(), 600
        )

        def getMemData():
            return DataPoint(domain.getMemoryUsage())

        self.__mem_data_series__.setWatchCallback(1000 * REFRESH_SECONDS, getMemData)
        self.__mem_graph__ = Graph([self.__mem_data_series__], "Memory")
        row.addChild(self.__mem_graph__)

    def end(self):
        """Stop collecting data and updating the graph."""
        self.__cpu_data_series__.stopWatchCallback()
        self.__mem_data_series__.stopWatchCallback()
