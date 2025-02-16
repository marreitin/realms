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
import xml.etree.ElementTree as ET

from gi.repository import Adw

from realms.ui.components.bindable_entries import BindableEntryRow

from .net_base_settings_page import BaseNetSettingsPage


class NetQOSPage(BaseNetSettingsPage):
    def __init__(self, parent, show_apply_cb: callable):
        super().__init__(parent)

        self.show_apply_cb = show_apply_cb

        self.xml_tree = None

        self.build()

    def build(self):
        # Inbound
        self.in_prefs_group = Adw.PreferencesGroup(title="Inbound quality of service")
        self.prefs_page.add(self.in_prefs_group)

        self.in_average_row = BindableEntryRow(title="Average [KiB/s]")
        self.in_prefs_group.add(self.in_average_row)

        self.in_peak_row = BindableEntryRow(title="Peak [KiB/s]")
        self.in_prefs_group.add(self.in_peak_row)

        self.in_burst_row = BindableEntryRow(title="Burst [KiB]")
        self.in_prefs_group.add(self.in_burst_row)

        # Outbound
        self.out_prefs_group = Adw.PreferencesGroup(title="Outbound quality of service")
        self.prefs_page.add(self.out_prefs_group)

        self.out_average_row = BindableEntryRow(title="Average [KiB/s]")
        self.out_prefs_group.add(self.out_average_row)

    def updateData(self, xml_tree: ET.Element):
        self.xml_tree = xml_tree

        bandwidth = self.xml_tree.find("bandwidth")
        if bandwidth is None:
            bandwidth = ET.SubElement(self.xml_tree, "bandwidth")

        inbound = bandwidth.find("inbound")
        if inbound is None:
            inbound = ET.Element("inbound")

        self.in_average_row.bindAttr(inbound, "average", self.onInboundChanged)
        self.in_peak_row.bindAttr(inbound, "peak", self.onInboundChanged)
        self.in_burst_row.bindAttr(inbound, "burst", self.onInboundChanged)

        outbound = bandwidth.find("outbound")
        if outbound is None:
            outbound = ET.Element("outbound")

        self.out_average_row.bindAttr(outbound, "average", self.onOutboundChanged)

    def onInboundChanged(self):
        bandwidth = self.xml_tree.find("bandwidth")
        inbound = bandwidth.find("inbound")
        if self.in_average_row.get_text() == "":
            if inbound is not None:
                bandwidth.remove(inbound)
        else:
            if bandwidth is None:
                bandwidth.append(self.in_average_row.elem)

    def onOutboundChanged(self):
        bandwidth = self.xml_tree.find("bandwidth")
        outbound = bandwidth.find("outbound")
        if self.out_average_row.get_text() == "":
            if outbound is not None:
                bandwidth.remove(outbound)
        else:
            if bandwidth is None:
                bandwidth.append(self.out_average_row.elem)
