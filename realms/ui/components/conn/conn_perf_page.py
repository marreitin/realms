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
        self.__is_started__ = False

        page = RealmsPreferencesPage()
        self.append(page)

        group = Adw.PreferencesGroup()
        page.add(group)

        # CPU graph
        row = GenericPreferencesRow()
        group.add(row)

        self.__cpu_data_series__ = DataSeries([], 1, 120)
        self.__cpu_graph__ = Graph(self.__cpu_data_series__, "CPU")
        row.addChild(self.__cpu_graph__)

        # Memory graph
        row = GenericPreferencesRow()
        group.add(row)

        self.__mem_data_series__ = DataSeries([], 1, 120)
        self.__mem_graph__ = Graph(self.__mem_data_series__, "Memory")
        row.addChild(self.__mem_graph__)

        # IOWait graph
        row = GenericPreferencesRow()
        group.add(row)

        self.__iowait_data_series__ = DataSeries([], 1, 120)
        self.__iowait_graph__ = Graph(self.__iowait_data_series__, "IO-Wait")
        row.addChild(self.__iowait_graph__)

    def start(self):
        """Start collecting information."""
        if self.__is_started__:
            return

        self.__is_started__ = True

        self.__cpu_data_series__.setValues(
            [RelativeDataPoint(0, self.parent.connection.getHostCPUTime())]
        )

        def getCPUData():
            cpu_time_reading = self.parent.connection.getHostCPUTime()
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
            display_val /= 1000000000 * self.REFRESH_SECONDS
            return RelativeDataPoint(display_val, cpu_time_reading)

        self.__cpu_data_series__.setWatchCallback(
            1000 * self.REFRESH_SECONDS, getCPUData
        )

        self.__iowait_data_series__.setValues(
            [RelativeDataPoint(0, self.parent.connection.getHostIOWait())]
        )

        def getIOwaitData():
            iowait_time_reading = self.parent.connection.getHostIOWait()
            display_val = 0
            if len(self.__iowait_data_series__) > 1:
                display_val = abs(
                    self.__iowait_data_series__.values[-2].last_reading
                    - iowait_time_reading
                )
                display_val /= 2
            else:
                display_val = abs(
                    self.__iowait_data_series__.getLast().last_reading
                    - iowait_time_reading
                )
            display_val /= 1000000000 * self.REFRESH_SECONDS
            return RelativeDataPoint(display_val, iowait_time_reading)

        self.__iowait_data_series__.setWatchCallback(
            1000 * self.REFRESH_SECONDS, getIOwaitData
        )
        self.__mem_data_series__.setValues([DataPoint(0)])
        self.__mem_data_series__.max_value = self.parent.connection.maxMemory()

        def getMemData():
            return DataPoint(self.parent.connection.getHostMemoryUsage() * 1024)

        self.__mem_data_series__.setWatchCallback(
            1000 * self.REFRESH_SECONDS, getMemData
        )

    def end(self):
        """Stop gathering information."""
        self.__cpu_data_series__.stopWatchCallback()
        self.__iowait_data_series__.stopWatchCallback()
        self.__mem_data_series__.stopWatchCallback()
        self.__is_started__ = False
