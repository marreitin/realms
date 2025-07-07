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

from realms.libvirt_wrap.constants import *
from realms.libvirt_wrap.domain import Domain
from realms.ui.components.generic_preferences_row import GenericPreferencesRow
from realms.ui.components.graphs import DataPoint, DataSeries, Graph, RelativeDataPoint
from realms.ui.components.preference_widgets import RealmsPreferencesPage


class PerformanceBox(Gtk.Box):
    """Box containing the performance graphs of a domain."""

    def __init__(self, domain: Domain):
        self.REFRESH_SECONDS = 0.2
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.domain = domain
        self.domain.registerCallback(self.__onConnectionEvent__)

        self.page = RealmsPreferencesPage()
        self.append(self.page)

        self.group = Adw.PreferencesGroup()
        self.page.add(self.group)

        # CPU graph
        row = GenericPreferencesRow()
        row.set_activatable(False)
        self.group.add(row)

        self.__cpu_data_series__ = DataSeries(
            [RelativeDataPoint(0, domain.getCPUTime())], 1, 600
        )

        def getCPUData(ds):
            cpu_time_reading = domain.getCPUTime()
            display_val = 0
            if len(self.__cpu_data_series__) > 1:
                display_val = abs(ds.values[-2].last_reading - cpu_time_reading)
                display_val /= 2
            else:
                display_val = abs(ds.getLast().last_reading - cpu_time_reading)
            display_val /= domain.getVCPUs()
            display_val /= 1000000000 * self.REFRESH_SECONDS
            return RelativeDataPoint(display_val, cpu_time_reading)

        self.__cpu_data_series__.setWatchCallback(
            1000 * self.REFRESH_SECONDS, getCPUData
        )
        self.__cpu_graph__ = Graph(
            [self.__cpu_data_series__],
            "CPU",
            lambda series: f"{ int(series[0].getLastAvg(5) * 100) }%",
        )
        row.addChild(self.__cpu_graph__)

        # Memory graph
        row = GenericPreferencesRow()
        row.set_activatable(False)
        self.group.add(row)

        self.__mem_data_series__ = DataSeries(
            [DataPoint(0)], domain.getMaxMemory(), 600
        )

        def getMemData(*_):
            return DataPoint(domain.getMemoryUsage())

        self.__mem_data_series__.setWatchCallback(
            1000 * self.REFRESH_SECONDS, getMemData
        )
        self.__mem_graph__ = Graph([self.__mem_data_series__], "Memory")
        row.addChild(self.__mem_graph__)

        # Network Graphs
        self.net_rows = dict()

        self.__updateNetworkRow__()

    def __updateNetworkRow__(self):
        def getRXNICStats(ds: DataSeries, nic: str):
            rx = self.domain.getNICStats(nic)[0]
            value = rx - ds.getLast().last_reading
            return RelativeDataPoint(value, rx)

        def getTXNICStats(ds: DataSeries, nic: str):
            tx = self.domain.getNICStats(nic)[1]
            value = tx - ds.getLast().last_reading
            return RelativeDataPoint(value, tx)

        # Remove existing rows.
        for row, rx_ds, tx_ds in self.net_rows.values():
            self.group.remove(row)
            rx_ds.stopWatchCallback()
            tx_ds.stopWatchCallback()
        self.net_rows.clear()

        if self.domain.isActive():
            nics = self.domain.getNICs()

            for nic in nics:
                rx_ds = DataSeries(
                    [RelativeDataPoint(0, self.domain.getNICStats(nic)[0])],
                    None,
                    600,
                    fill=False,
                )
                rx_ds.setWatchCallback(
                    1000 * self.REFRESH_SECONDS,
                    lambda ds, nic=nic: getRXNICStats(ds, nic),
                )
                tx_ds = DataSeries(
                    [RelativeDataPoint(0, self.domain.getNICStats(nic)[1])],
                    None,
                    600,
                    fill=False,
                )
                tx_ds.setWatchCallback(
                    1000 * self.REFRESH_SECONDS,
                    lambda ds, nic=nic: getTXNICStats(ds, nic),
                )

                graph = Graph(
                    [rx_ds, tx_ds],
                    nic.upper(),
                    lambda series: f"↓{ series[0].getLastAvg(5) } ↑{ series[1].getLastAvg(5) }",
                )

                row = GenericPreferencesRow()
                row.set_activatable(False)
                self.group.add(row)
                row.addChild(graph)
                self.net_rows[nic] = (row, rx_ds, tx_ds)

    def __onConnectionEvent__(self, conn, obj, type_id, event_id, detail_id):
        if type_id == CALLBACK_TYPE_DOMAIN_LIFECYCLE:
            self.__updateNetworkRow__()

    def end(self):
        """Stop collecting data and updating the graph."""
        self.__cpu_data_series__.stopWatchCallback()
        self.__mem_data_series__.stopWatchCallback()
        for row, rx_ds, tx_ds in self.net_rows.values():
            rx_ds.stopWatchCallback()
            tx_ds.stopWatchCallback()
