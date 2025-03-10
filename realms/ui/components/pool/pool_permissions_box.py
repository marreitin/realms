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

from gi.repository import Gtk

from realms.ui.components.bindable_entries import BindableEntry


class PoolPermissionsBox(Gtk.Box):
    def __init__(self, show_apply_cb: callable, **kwargs):
        super().__init__(spacing=6, orientation=Gtk.Orientation.VERTICAL, **kwargs)

        self.show_apply_cb = show_apply_cb

        box = Gtk.Box(spacing=6)
        self.append(box)

        self.owner_entry = BindableEntry(
            placeholder_text="Owner ID",
            input_purpose=Gtk.InputPurpose.DIGITS,
            tooltip_text="Owner ID",
            hexpand=True,
        )
        box.append(self.owner_entry)

        self.group_entry = BindableEntry(
            placeholder_text="Group ID",
            input_purpose=Gtk.InputPurpose.DIGITS,
            tooltip_text="Group ID",
            hexpand=True,
        )
        box.append(self.group_entry)

        self.perm_label = BindableEntry(
            placeholder_text="Mode",
            input_purpose=Gtk.InputPurpose.DIGITS,
            tooltip_text="UNIX Permissions Mode Octet",
            hexpand=True,
        )
        box.append(self.perm_label)

        self.se_label_entry = BindableEntry(
            placeholder_text="SE Label", tooltip_text="SE-Linux label", hexpand=True
        )
        self.append(self.se_label_entry)

    def connectData(self, xml_tree: ET.Element) -> None:
        owner = xml_tree.find("owner")
        if owner is None:
            owner = ET.SubElement(xml_tree, "owner")

        self.owner_entry.bindText(owner, self.show_apply_cb)

        group = xml_tree.find("group")
        if group is None:
            group = ET.SubElement(xml_tree, "group")

        self.group_entry.bindText(group, self.show_apply_cb)

        mode = xml_tree.find("mode")
        if mode is None:
            mode = ET.SubElement(xml_tree, "mode")

        self.perm_label.bindText(mode, self.show_apply_cb)

        label = xml_tree.find("label")
        if label is None:
            label = ET.SubElement(xml_tree, "label")

        self.se_label_entry.bindText(label, self.show_apply_cb)
