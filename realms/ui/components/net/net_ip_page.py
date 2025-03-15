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

from realms.helpers import ip_and_netmask_to_cidr
from realms.ui.components.bindable_entries import BindableEntry
from realms.ui.components.common import deleteRow, iconButton
from realms.ui.dialogs.dhcphosts_dialog import DHCPHostsDialog

from .net_base_settings_page import BaseNetSettingsPage


class IPRow(Adw.ExpanderRow):
    def __init__(self, xml_elem: ET.Element, parent: Adw.PreferencesGroup):
        super().__init__()

        # XML tree for a single IP element
        self.xml_elem = xml_elem
        self.parent = parent

        self.dhcp_label = None
        self.tftp_label = None

        self.ip_addr_row = None
        self.dhcp_row = None
        self.dhcp_switch = None
        self.range_start = None
        self.range_end = None
        self.bootp_file = None
        self.dhcphosts_row = None
        self.dhcphosts_dialog = None

        self.dhcp_content_box = None

        self.tftp_row = None
        self.tftp_switch = None
        self.serv_dir = None

        self.tftp_content_box = None

        self.cancel_btn = None

        self.build()

        self.onUpdateState()

    def build(self):
        prefix = self.getIPPrefix()

        self.set_title(prefix)

        self.dhcp_label = Gtk.Label(label="DHCP", css_classes=["dim-label", "caption"])
        self.add_suffix(self.dhcp_label)
        self.tftp_label = Gtk.Label(label="TFTP", css_classes=["dim-label", "caption"])
        self.add_suffix(self.tftp_label)

        self.ip_addr_row = Adw.EntryRow(title="Network address", text=prefix)
        self.ip_addr_row.connect("changed", self.onIPChanged)
        self.add_row(self.ip_addr_row)

        # DHCP
        self.dhcp_row = Adw.PreferencesRow()
        self.add_row(self.dhcp_row)

        dhcp_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=6,
            margin_top=12,
            margin_bottom=12,
            margin_start=12,
            margin_end=12,
        )
        self.dhcp_row.set_child(dhcp_box)

        box = Gtk.Box()
        dhcp_box.append(box)
        box.append(
            Gtk.Label(
                label="DHCP",
                hexpand=True,
                css_classes=["heading"],
                halign=Gtk.Align.START,
            )
        )
        self.dhcp_switch = Gtk.Switch()
        box.append(self.dhcp_switch)

        self.dhcp_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        dhcp_box.append(self.dhcp_content_box)

        box = Gtk.Box(spacing=6)
        self.dhcp_content_box.append(box)

        self.range_start = BindableEntry(
            placeholder_text="Range start",
            tooltip_text="DHCP range start",
            hexpand=True,
        )
        box.append(self.range_start)

        box.append(Gtk.Label(label="-"))

        self.range_end = BindableEntry(
            placeholder_text="Range end", tooltip_text="DHCP range end", hexpand=True
        )
        box.append(self.range_end)

        self.bootp_file = BindableEntry(
            placeholder_text="BootP file entry",
            tooltip_text="BootP file entry",
            hexpand=True,
        )
        self.dhcp_content_box.append(self.bootp_file)

        dhcp = self.xml_elem.find("dhcp")
        if dhcp is not None:
            self.dhcp_switch.set_active(True)
            self.range_start.set_text(dhcp.find("range").get("start", ""))
            self.range_end.set_text(dhcp.find("range").get("end", ""))

            bootp = dhcp.find("bootp")
            if bootp is not None:
                self.bootp_file.set_text(bootp.get("file", ""))

        # Row to open dhcphosts-dialog
        self.dhcphosts_row = Adw.ActionRow(
            title="Edit DHCP hosts",
            activatable=True,
            selectable=False,
        )
        self.add_row(self.dhcphosts_row)

        open_icon = Gtk.Image.new_from_icon_name("right-symbolic")
        self.dhcphosts_row.add_suffix(open_icon)

        self.dhcphosts_row.connect("activated", self.onDHCPHostsActivated)

        # TFTP
        self.tftp_row = Adw.PreferencesRow()
        self.add_row(self.tftp_row)

        tftp_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=6,
            margin_top=12,
            margin_bottom=12,
            margin_start=12,
            margin_end=12,
        )
        self.tftp_row.set_child(tftp_box)

        box = Gtk.Box()
        tftp_box.append(box)
        box.append(
            Gtk.Label(
                label="TFTP",
                hexpand=True,
                halign=Gtk.Align.START,
                css_classes=["heading"],
            )
        )

        self.tftp_switch = Gtk.Switch()
        box.append(self.tftp_switch)

        self.tftp_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        tftp_box.append(self.tftp_content_box)

        self.serv_dir = BindableEntry(
            placeholder_text="Serving directory",
            tooltip_text="Directory to serve over TFTP",
            hexpand=True,
        )
        self.tftp_content_box.append(self.serv_dir)

        tftp = self.xml_elem.find("tftp")
        if tftp is not None:
            self.tftp_switch.set_active(True)
            self.serv_dir.set_text(tftp.get("root", ""))

        # Lower action row
        self.add_row(deleteRow(self.onDeleteClicked))

        # Event handlers
        self.dhcp_switch.connect("notify::active", self.onUpdateState)
        self.tftp_switch.connect("notify::active", self.onUpdateState)

    def onIPChanged(self, *args):
        if "netmask" in self.xml_elem.attrib:
            del self.xml_elem.attrib["netmask"]

        try:
            data = self.ip_addr_row.get_text().split("/")
            self.xml_elem.set("address", data[0])
            self.xml_elem.set("prefix", data[1])
            self.xml_elem.set("family", "ipv4" if "." in data[0] else "ipv6")
            prefix = self.getIPPrefix()
            self.set_title(prefix)

            self.parent.show_apply_cb()
        except:
            self.ip_addr_row.set_css_classes(["error"])

    def onUpdateState(self, *args):
        if self.dhcp_switch.get_active():
            self.dhcp_label.set_visible(True)
            self.dhcphosts_row.set_visible(True)

            self.dhcp_content_box.set_visible(True)
            dhcp = self.xml_elem.find("dhcp")
            if dhcp is None:
                dhcp = ET.SubElement(self.xml_elem, "dhcp")

            r = dhcp.find("range")
            if r is None:
                r = ET.SubElement(dhcp, "range", attrib={"start": "", "end": ""})
            self.range_start.bindAttr(r, "start", self.parent.show_apply_cb)
            self.range_end.bindAttr(r, "end", self.parent.show_apply_cb)

            bootp = dhcp.find("bootp")
            if bootp is None:
                bootp = ET.Element("bootp", attrib={"file": ""})
            self.bootp_file.bindAttr(bootp, "file", self.onBootPChanged)
        else:
            self.dhcp_label.set_visible(False)
            self.dhcphosts_row.set_visible(False)

            self.dhcp_content_box.set_visible(False)
            dhcp = self.xml_elem.find("dhcp")
            if dhcp is not None:
                self.xml_elem.remove(dhcp)

            self.range_start.unbind()
            self.range_end.unbind()
            self.bootp_file.unbind()

        if self.tftp_switch.get_active():
            self.tftp_label.set_visible(True)
            self.tftp_content_box.set_visible(True)
            tftp = ET.SubElement(self.xml_elem, "tftp", attrib={"root": ""})
            self.serv_dir.bindAttr(tftp, "root", self.parent.show_apply_cb)
        else:
            self.tftp_label.set_visible(False)
            self.tftp_content_box.set_visible(False)
            tftp = self.xml_elem.find("tftp")
            if tftp is not None:
                self.xml_elem.remove(tftp)
            self.serv_dir.unbind()

        self.parent.show_apply_cb()

    def getIPPrefix(self) -> str:
        if "prefix" not in self.xml_elem.attrib:
            if "netmask" not in self.xml_elem.attrib:
                self.xml_elem.attrib["netmask"] = "255.255.255.255"
            prefix = ip_and_netmask_to_cidr(
                self.xml_elem.attrib["address"], self.xml_elem.attrib["netmask"]
            )
        else:
            prefix = (
                self.xml_elem.attrib["address"] + "/" + self.xml_elem.attrib["prefix"]
            )
        return prefix

    def onBootPChanged(self):
        dhcp = self.xml_elem.find("dhcp")
        bootp = dhcp.find("bootp")
        if self.bootp_file.get_text() == "":
            if bootp is not None:
                dhcp.remove(bootp)
        else:
            if bootp is None:
                dhcp.append(self.bootp_file.elem)
        self.parent.show_apply_cb()

    def onDeleteClicked(self, button):
        self.parent.delete(self)

    def onDHCPHostsActivated(self, *_):
        self.dhcphosts_dialog = DHCPHostsDialog(
            self.parent.parent.getWindow(),
            self.xml_elem,
            self.parent.show_apply_cb,
        )

    def end(self):
        # Make sure the dialog for editing dhcp host entries is closed.
        if self.dhcphosts_dialog is not None:
            self.dhcphosts_dialog.close()
            self.dhcphosts_dialog = None


class NetIPGroup(Adw.PreferencesGroup):
    def __init__(self, parent, show_apply_cb: callable):
        super().__init__()

        self.parent = parent

        self.ip_rows = []
        self.add_button = None

        self.xml_tree = None
        self.show_apply_cb = show_apply_cb

        self.build()

    def build(self):
        self.set_title(title="IP addresses")

        self.add_button = iconButton(
            "",
            "list-add-symbolic",
            self.onAddButtonClicked,
            css_classes=["flat"],
            tooltip_text="Add network IP address",
        )
        self.set_header_suffix(self.add_button)

    def updateData(self, xml_tree: ET.Element):
        self.xml_tree = xml_tree

        for row in self.ip_rows:
            row.end()
            self.remove(row)
        self.ip_rows.clear()

        ips = self.xml_tree.findall("ip")
        for ip_tree in ips:
            row = IPRow(ip_tree, self)
            self.add(row)
            self.ip_rows.append(row)

    def onAddButtonClicked(self, btn):
        ip_tree = ET.SubElement(
            self.xml_tree, "ip", attrib={"address": "0.0.0.0", "prefix": "32"}
        )
        row = IPRow(ip_tree, self)
        self.add(row)
        self.ip_rows.append(row)
        row.set_expanded(True)

        self.show_apply_cb()

    def delete(self, row):
        self.ip_rows.remove(row)
        self.remove(row)
        self.xml_tree.remove(row.xml_elem)
        self.show_apply_cb()


class NetIPPage(BaseNetSettingsPage):
    def __init__(self, parent, show_apply_cb: callable):
        super().__init__(parent)

        self.ip_rows = []
        self.add_button = None

        self.xml_tree = None
        self.show_apply_cb = show_apply_cb

        self.build()

    def build(self):
        self.prefs_group = NetIPGroup(self.parent, self.show_apply_cb)
        self.prefs_page.add(self.prefs_group)

    def updateData(self, xml_tree: ET.Element):
        self.xml_tree = xml_tree
        self.prefs_group.updateData(self.xml_tree)
