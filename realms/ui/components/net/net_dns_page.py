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

from realms.ui.components.bindable_entries import (
    BindableDropDown,
    BindableEntry,
    BindableSpinButton,
    BindableSwitchRow,
)
from realms.ui.components.common import iconButton
from realms.ui.components.generic_preferences_row import GenericPreferencesRow

from .net_base_settings_page import BaseNetSettingsPage


class ForwarderRow(GenericPreferencesRow):
    def __init__(self, xml_elem: ET.Element, parent: Adw.PreferencesGroup):
        super().__init__()

        self.xml_elem = xml_elem
        self.parent = parent

        self.ip_entry = None
        self.domain_entry = None

        self.build()

    def build(self):
        box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=6,
        )
        self.addChild(box)

        self.domain_entry = BindableEntry(
            placeholder_text="Domain",
            tooltip_text="Match domain",
            hexpand=True,
        )
        self.domain_entry.bindAttr(self.xml_elem, "domain", self.parent.show_apply_cb)
        box.append(self.domain_entry)

        self.ip_entry = BindableEntry(
            placeholder_text="IP address",
            tooltip_text="Forwarder IP address",
            hexpand=True,
        )
        self.ip_entry.bindAttr(self.xml_elem, "addr", self.parent.show_apply_cb)
        box.append(self.ip_entry)

        delete_btn = iconButton(
            "",
            "user-trash-symbolic",
            self.onDeleteClicked,
            tooltip_text="Remove",
            css_classes=["flat"],
        )
        box.append(delete_btn)

    def onDeleteClicked(self, button):
        self.parent.deleteForwarderRow(self)


class HostRow(GenericPreferencesRow):
    def __init__(self, xml_elem: ET.Element, parent: Adw.PreferencesGroup):
        super().__init__()

        self.xml_elem = xml_elem
        self.parent = parent

        self.ip_entry = None
        self.name_entry = None

        self.build()

    def build(self):
        box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=6,
        )
        self.addChild(box)

        hostname = self.xml_elem.find("hostname")
        if hostname is None:
            hostname = ET.SubElement(self.xml_elem, "hostname")
            hostname.text = ""
        self.name_entry = BindableEntry(
            placeholder_text="Hostname",
            tooltip_text="Associated hostname",
            hexpand=True,
        )
        self.name_entry.bindText(hostname, self.parent.show_apply_cb)
        box.append(self.name_entry)

        self.ip_entry = BindableEntry(
            placeholder_text="IP address", tooltip_text="IP address", hexpand=True
        )
        self.ip_entry.bindAttr(self.xml_elem, "ip", self.parent.show_apply_cb)
        box.append(self.ip_entry)

        delete_btn = iconButton(
            "",
            "user-trash-symbolic",
            self.onDeleteClicked,
            tooltip_text="Remove",
            css_classes=["flat"],
        )
        box.append(delete_btn)

    def onDeleteClicked(self, button):
        self.parent.deleteHostRow(self)


class TXTRow(GenericPreferencesRow):
    def __init__(self, xml_elem: ET.Element, parent: Adw.PreferencesGroup):
        super().__init__()

        self.xml_elem = xml_elem
        self.parent = parent

        self.ip_entry = None
        self.name_entry = None

        self.build()

    def build(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.addChild(box)

        self.name_entry = BindableEntry(
            placeholder_text="Name", tooltip_text="Record name", hexpand=True
        )
        self.name_entry.bindAttr(self.xml_elem, "name", self.parent.show_apply_cb)
        box.append(self.name_entry)

        self.value_entry = BindableEntry(
            placeholder_text="TXT value",
            tooltip_text="Associated value",
            hexpand=True,
        )
        self.value_entry.bindAttr(self.xml_elem, "value", self.parent.show_apply_cb)
        box.append(self.value_entry)

        delete_btn = iconButton(
            "",
            "user-trash-symbolic",
            self.onDeleteClicked,
            tooltip_text="Remove",
            css_classes=["flat"],
        )
        box.append(delete_btn)

    def onDeleteClicked(self, button):
        self.parent.deleteTXTRow(self)


class SRVRow(GenericPreferencesRow):
    def __init__(self, xml_elem: ET.Element, parent: Adw.PreferencesGroup):
        super().__init__()

        self.xml_elem = xml_elem
        self.parent = parent

        self.ip_entry = None
        self.service_entry = None

        self.build()

    def build(self):
        box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=6,
        )
        self.addChild(box)

        self.service_entry = BindableEntry(
            placeholder_text="Service", tooltip_text="Service name", hexpand=True
        )
        self.service_entry.bindAttr(self.xml_elem, "service", self.parent.show_apply_cb)
        box.append(self.service_entry)

        self.protocol_combo = BindableDropDown(["tcp", "udp"], tooltip_text="Protocol")
        self.protocol_combo.bindAttr(
            self.xml_elem, "protocol", self.parent.show_apply_cb
        )
        box.append(self.protocol_combo)

        delete_btn = iconButton(
            "",
            "user-trash-symbolic",
            self.onDeleteClicked,
            tooltip_text="Remove",
            css_classes=["flat"],
        )
        box.append(delete_btn)

        box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=6,
        )
        self.addChild(box)

        self.domain_entry = BindableEntry(
            placeholder_text="Domain", tooltip_text="Domain", hexpand=True
        )
        self.domain_entry.bindAttr(self.xml_elem, "domain", self.parent.show_apply_cb)
        box.append(self.domain_entry)

        self.target_entry = BindableEntry(
            placeholder_text="Target", tooltip_text="Target", hexpand=True
        )
        self.target_entry.bindAttr(self.xml_elem, "target", self.parent.show_apply_cb)
        box.append(self.target_entry)

        box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=6,
        )
        self.addChild(box)

        self.port_spinner = BindableSpinButton(
            lambda x: str(int(x)),
            0,
            tooltip_text="Port",
            digits=0,
            adjustment=Gtk.Adjustment(lower=0, upper=65536, step_increment=1),
            hexpand=True,
        )
        self.port_spinner.bindAttr(self.xml_elem, "port", self.parent.show_apply_cb)
        box.append(self.port_spinner.getWidget())

        self.priority_entry = BindableEntry(
            placeholder_text="Priority", tooltip_text="Priority", hexpand=True
        )
        self.priority_entry.bindAttr(
            self.xml_elem, "priority", self.parent.show_apply_cb
        )
        box.append(self.priority_entry)

        self.weight_entry = BindableEntry(
            placeholder_text="Weight", tooltip_text="Weight", hexpand=True
        )
        self.weight_entry.bindAttr(self.xml_elem, "weight", self.parent.show_apply_cb)
        box.append(self.weight_entry)

    def onDeleteClicked(self, button):
        self.parent.deleteSRVRow(self)


class NetDNSPage(BaseNetSettingsPage):
    def __init__(self, parent, show_apply_cb: callable):
        super().__init__(parent)
        self.show_apply_cb = show_apply_cb

        self.prefs_group = None

        self.forwarder_rows = []
        self.forwarder_group = None
        self.add_forwarder_btn = None

        self.host_rows = []
        self.host_group = None
        self.add_host_btn = None

        self.txt_rows = []
        self.txt_group = None
        self.add_txt_btn = None

        self.srv_rows = []
        self.srv_group = None
        self.add_srv_btn = None

        self.xml_tree = None

        self.build()

    def build(self):
        self.prefs_group = Adw.PreferencesGroup()
        self.prefs_page.add(self.prefs_group)

        self.enable_row = BindableSwitchRow("yes", "no", True, title="Use DNS")
        self.prefs_group.add(self.enable_row.switch_row)

        self.forwarder_group = Adw.PreferencesGroup(title="DNS forwarders")
        self.prefs_page.add(self.forwarder_group)

        self.add_forwarder_btn = iconButton(
            "",
            "list-add-symbolic",
            self.onAddForwarderClicked,
            tooltip_text="Add forwarder",
            css_classes=["flat"],
        )
        self.forwarder_group.set_header_suffix(self.add_forwarder_btn)

        self.host_group = Adw.PreferencesGroup(title="Host records")
        self.prefs_page.add(self.host_group)

        self.add_host_btn = iconButton(
            "",
            "list-add-symbolic",
            self.onAddHostClicked,
            tooltip_text="Add host record",
            css_classes=["flat"],
        )
        self.host_group.set_header_suffix(self.add_host_btn)

        self.txt_group = Adw.PreferencesGroup(title="TXT records")
        self.prefs_page.add(self.txt_group)

        self.add_txt_btn = iconButton(
            "",
            "list-add-symbolic",
            self.onAddTXTClicked,
            tooltip_text="Add TXT record",
            css_classes=["flat"],
        )
        self.txt_group.set_header_suffix(self.add_txt_btn)

        self.srv_group = Adw.PreferencesGroup(title="SRV records")
        self.prefs_page.add(self.srv_group)

        self.add_srv_btn = iconButton(
            "",
            "list-add-symbolic",
            self.onAddSRVClicked,
            tooltip_text="Add SRV record",
            css_classes=["flat"],
        )
        self.srv_group.set_header_suffix(self.add_srv_btn)

    def updateData(self, xml_tree: ET.Element):
        self.xml_tree = xml_tree
        dns = self.xml_tree.find("dns")
        if dns is None:
            dns = ET.SubElement(self.xml_tree, "dns")

        self.enable_row.bindAttr(dns, "enable", self.onEnableChanged)

        self.forwarder_group.set_visible(self.enable_row.getWidget().get_active())
        self.host_group.set_visible(self.enable_row.getWidget().get_active())
        self.txt_group.set_visible(self.enable_row.getWidget().get_active())
        self.srv_group.set_visible(self.enable_row.getWidget().get_active())

        # Forwarders
        for row in self.forwarder_rows:
            self.forwarder_group.remove(row)
        self.forwarder_rows.clear()

        forwarders = dns.findall("forwarder")
        for f in forwarders:
            row = ForwarderRow(f, self)
            self.forwarder_group.add(row)
            self.forwarder_rows.append(row)

        # Hosts
        for row in self.host_rows:
            self.host_group.remove(row)
        self.host_rows.clear()

        hosts = dns.findall("host")
        for host in hosts:
            row = HostRow(host, self)
            self.host_group.add(row)
            self.host_rows.append(row)

        # TXT
        for row in self.txt_rows:
            self.txt_group.remove(row)
        self.txt_rows.clear()

        txt_records = dns.findall("txt")
        for txt in txt_records:
            row = TXTRow(txt, self)
            self.txt_group.add(row)
            self.txt_rows.append(row)

        # SRV
        for row in self.srv_rows:
            self.srv_group.remove(row)
        self.srv_rows.clear()

        srv_records = dns.findall("srv")
        for srv in srv_records:
            row = SRVRow(srv, self)
            self.srv_group.add(row)
            self.srv_rows.append(row)

    def onAddForwarderClicked(self, btn):
        forwarder = ET.SubElement(self.xml_tree.find("dns"), "forwarder")
        row = ForwarderRow(forwarder, self)
        self.forwarder_group.add(row)
        self.forwarder_rows.append(row)
        self.show_apply_cb()

    def onAddHostClicked(self, btn):
        host = ET.SubElement(
            self.xml_tree.find("dns"), "host", attrib={"ip": "0.0.0.0"}
        )
        row = HostRow(host, self)
        self.host_group.add(row)
        self.host_rows.append(row)
        self.show_apply_cb()

    def onAddTXTClicked(self, btn):
        record = ET.SubElement(self.xml_tree.find("dns"), "txt")
        row = TXTRow(record, self)
        self.txt_group.add(row)
        self.txt_rows.append(row)
        self.show_apply_cb()

    def onAddSRVClicked(self, btn):
        record = ET.SubElement(
            self.xml_tree.find("dns"), "srv", attrib={"service": "", "protocol": "tcp"}
        )
        row = SRVRow(record, self)
        self.srv_group.add(row)
        self.srv_rows.append(row)
        self.show_apply_cb()

    def onEnableChanged(self, *args):
        dns = self.xml_tree.find("dns")
        dns.clear()
        if self.enable_row.switch_row.get_active():
            dns.set("enable", "yes")
        else:
            dns.set("enable", "no")
        self.updateData(self.xml_tree)
        self.show_apply_cb()

    def deleteForwarderRow(self, row):
        self.forwarder_rows.remove(row)
        self.forwarder_group.remove(row)
        dns = self.xml_tree.find("dns")
        dns.remove(row.xml_elem)
        self.show_apply_cb()

    def deleteHostRow(self, row):
        self.host_rows.remove(row)
        self.host_group.remove(row)
        dns = self.xml_tree.find("dns")
        dns.remove(row.xml_elem)
        self.show_apply_cb()

    def deleteTXTRow(self, row):
        self.txt_rows.remove(row)
        self.txt_group.remove(row)
        dns = self.xml_tree.find("dns")
        dns.remove(row.xml_elem)
        self.show_apply_cb()

    def deleteSRVRow(self, row):
        self.srv_rows.remove(row)
        self.srv_group.remove(row)
        dns = self.xml_tree.find("dns")
        dns.remove(row.xml_elem)
        self.show_apply_cb()
