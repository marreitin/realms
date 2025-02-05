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

from realms.ui.builders.bindable_entries import BindableEntryRow
from realms.ui.builders.common import iconButton


class DHCPHostRow(Adw.ExpanderRow):
    """A row representing a single predefined lease."""

    def __init__(self, parent, xml_elem: ET.Element, **kwargs):
        super().__init__(**kwargs)

        self.parent = parent
        self.xml_elem = xml_elem

        self.build()

    def build(self):
        self.generateTitle()

        delete_btn = iconButton(
            "",
            "user-trash-symbolic",
            lambda *_: self.parent.onHostRemoved(self),
            css_classes=["flat"],
        )
        self.add_suffix(delete_btn)

        self.name_row = BindableEntryRow(title="Name")
        self.name_row.bindAttr(self.xml_elem, "name", self.onChanged)
        self.add_row(self.name_row)

        self.mac_row = BindableEntryRow(title="MAC")
        self.mac_row.bindAttr(self.xml_elem, "mac", self.onChanged)
        self.add_row(self.mac_row)

        self.ip_row = BindableEntryRow(title="IP")
        self.ip_row.bindAttr(self.xml_elem, "ip", self.onChanged)
        self.add_row(self.ip_row)

    def generateTitle(self):
        name = self.xml_elem.get("name", "")
        if not name:
            name = self.xml_elem.get("ip", "")
        self.set_title(name)

    def onChanged(self):
        self.generateTitle()
        self.parent.show_apply_cb()


class DHCPHostsDialog:
    """Dialog to edit predefined DHCP leases."""

    def __init__(
        self,
        window: Adw.ApplicationWindow,
        xml_elem: ET.Element,
        show_apply_cb: callable,
    ):
        self.window = window
        self.xml_elem = xml_elem  # IP element
        self.show_apply_cb = show_apply_cb

        self.rows = []

        # Create a Builder
        self.builder = Gtk.Builder.new_from_resource(
            "/com/github/marreitin/realms/gtk/dhcphosts.ui"
        )

        # Obtain and show the main window
        self.dialog = self.obj("main-dialog")
        self.dialog.present(self.window)

        self.add_btn = self.obj("add-host")
        self.add_btn.connect("clicked", self.onAddClicked)
        self.hosts_group = self.obj("main-group")

        dhcp = self.xml_elem.find("dhcp")
        if dhcp is not None:
            for host in dhcp.findall("host"):
                row = DHCPHostRow(self, host)
                self.rows.append(row)
                self.hosts_group.add(row)

    def onAddClicked(self, btn):
        dhcp = self.xml_elem.find("dhcp")
        if dhcp is None:
            dhcp = ET.SubElement(self.xml_elem, "dhcp")

        row = DHCPHostRow(
            self,
            ET.SubElement(dhcp, "host", attrib={"ip": "", "mac": ""}),
            expanded=True,
        )
        self.rows.append(row)
        self.hosts_group.add(row)
        self.show_apply_cb()

    def onHostRemoved(self, row: DHCPHostRow):
        self.rows.remove(row)
        self.hosts_group.remove(row)

        dhcp = self.xml_elem.find("dhcp")
        dhcp.remove(row.xml_elem)
        self.show_apply_cb()

    def obj(self, name: str):
        o = self.builder.get_object(name)
        if o is None:
            raise NotImplementedError(f"Object { name } could not be found!")
        return o

    def close(self):
        self.dialog.close()
