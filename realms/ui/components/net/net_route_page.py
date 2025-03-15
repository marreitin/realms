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

from gi.repository import Adw, Gtk

from realms.ui.components.bindable_entries import BindableEntryRow
from realms.ui.components.common import deleteRow, iconButton

from .net_base_settings_page import BaseNetSettingsPage


class RouteRow(Adw.ExpanderRow):
    def __init__(self, xml_elem: ET.Element, parent: Adw.PreferencesGroup):
        super().__init__()

        self.xml_elem = xml_elem
        self.parent = parent

        self.address_row = None
        self.gateway_row = None
        self.metric_row = None
        self.metric_spinner = None
        self.metric_switch = None

        self.build()

    def build(self):
        self.set_title(self.xml_elem.get("address"))

        self.address_row = Adw.EntryRow(title="Destination network address")
        self.add_row(self.address_row)
        self.address_row.set_text(
            f"{ self.xml_elem.get('address') }/{ self.xml_elem.get('prefix') }"
        )
        self.address_row.connect("changed", self.onAddressChanged)

        self.gateway_row = BindableEntryRow(title="Gateway address")
        self.gateway_row.bindAttr(self.xml_elem, "gateway", self.parent.show_apply_cb)
        self.add_row(self.gateway_row)

        self.metric_row = Adw.ActionRow(
            title="Metric", subtitle="Routes with lower metrics are preferred"
        )
        self.add_row(self.metric_row)

        self.metric_spinner = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(lower=1, upper=64, step_increment=1, value=1),
            digits=0,
            css_classes=["flat"],
            tooltip_text="Lower values are preferred",
        )
        self.metric_row.add_suffix(self.metric_spinner)

        self.metric_switch = Gtk.Switch(vexpand=False, valign=Gtk.Align.BASELINE_CENTER)
        self.metric_row.add_suffix(self.metric_switch)

        if "metric" in self.xml_elem.attrib:
            self.metric_spinner.set_value(int(self.xml_elem.get("metric", "1")))
            self.metric_spinner.set_sensitive(True)
            self.metric_switch.set_active(True)
        else:
            self.metric_spinner.set_sensitive(False)
            self.metric_switch.set_active(False)

        self.metric_spinner.connect("value-changed", self.onMetricSpinnerChanged)
        self.metric_switch.connect("notify::active", self.onMetricSwitchChanged)

        # Lower action row
        self.add_row(deleteRow(self.onDeleteClicked))

    def onAddressChanged(self, row, *args):
        self.address_row.set_css_classes([])
        try:
            a = self.address_row.get_text()
            address = a.split("/")[0]
            prefix = a.split("/")[1]
            self.xml_elem.set("address", address)
            self.xml_elem.set("prefix", prefix)
            if "." in address:
                self.xml_elem.set("family", "ipv4")
            else:
                self.xml_elem.set("family", "ipv6")
            self.set_title(address)
        except:
            self.address_row.set_css_classes(["error"])
        self.parent.show_apply_cb()

    def onMetricSpinnerChanged(self, spinner, *args):
        self.xml_elem.set("metric", str(int(self.metric_spinner.get_value())))
        self.parent.show_apply_cb()

    def onMetricSwitchChanged(self, switch, *args):
        if switch.get_active():
            self.xml_elem.set("metric", str(self.metric_spinner.get_value()))
            self.metric_spinner.set_sensitive(True)
        else:
            self.metric_spinner.set_sensitive(False)
            if "metric" in self.xml_elem.attrib:
                del self.xml_elem.attrib["metric"]
        self.parent.show_apply_cb()

    def onDeleteClicked(self, button):
        self.parent.delete(self)


class NetRoutePage(BaseNetSettingsPage):
    def __init__(self, parent, show_apply_cb: callable):
        super().__init__(parent)

        self.route_rows = []
        self.add_button = None
        self.show_apply_cb = show_apply_cb

        self.xml_tree = None

        self.build()

    def build(self):
        self.prefs_group = Adw.PreferencesGroup(title="Static routes")
        self.prefs_page.add(self.prefs_group)

        suffix_box = Gtk.Box(spacing=6)
        self.prefs_group.set_header_suffix(suffix_box)

        self.add_button = iconButton(
            "",
            "list-add-symbolic",
            self.onAddButtonClicked,
            css_classes=["flat"],
            tooltip_text="Add static route",
        )
        suffix_box.append(self.add_button)

    def updateData(self, xml_tree: ET.Element):
        self.xml_tree = xml_tree
        for row in self.route_rows:
            self.prefs_group.remove(row)
        self.route_rows.clear()

        routes = self.xml_tree.findall("route")

        for route in routes:
            row = RouteRow(route, self)
            self.prefs_group.add(row)
            self.route_rows.append(row)

    def onAddButtonClicked(self, btn):
        route = ET.SubElement(
            self.xml_tree, "route", attrib={"address": "0.0.0.0", "prefix": "0"}
        )
        row = RouteRow(route, self)
        self.prefs_group.add(row)
        self.route_rows.append(row)
        self.show_apply_cb()

    def delete(self, row):
        self.route_rows.remove(row)
        self.prefs_group.remove(row)
        self.xml_tree.remove(row.xml_elem)
        self.show_apply_cb()
