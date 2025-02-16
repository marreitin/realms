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

from realms.ui.components.bindable_entries import BindableEntry

from .pool_permissions_box import PoolPermissionsBox


class PoolTargetRow(Adw.PreferencesRow):
    def __init__(self, show_apply_cb):
        super().__init__()

        self.show_apply_cb = show_apply_cb
        self.target_tree = None

        self.path_entry = None

        self.perms_box = None
        self.perms_enabled = None
        self.perm_label = None
        self.owner_entry = None
        self.group_entry = None
        self.se_label_entry = None

        self.build()

    def build(self):
        outer_box = Gtk.Box(
            spacing=6,
            margin_top=12,
            margin_bottom=12,
            margin_start=12,
            margin_end=12,
            orientation=Gtk.Orientation.VERTICAL,
        )
        self.set_child(outer_box)

        label = Gtk.Label(
            label="Storage target",
            css_classes=["heading"],
            hexpand=True,
            halign=Gtk.Align.START,
        )
        outer_box.append(label)

        self.path_entry = BindableEntry(placeholder_text="Path")
        outer_box.append(self.path_entry)

        box = Gtk.Box(spacing=6)
        outer_box.append(box)

        label = Gtk.Label(
            label="Manual Permissions",
            hexpand=True,
            halign=Gtk.Align.START,
            tooltip_text="Control permissions manually",
        )
        box.append(label)

        self.perms_enabled = Gtk.Switch(valign=Gtk.Align.BASELINE_CENTER)
        self.perms_enabled.connect("notify::active", self.onPermsEnabledChanged)
        box.append(self.perms_enabled)

        self.perms_box = PoolPermissionsBox(self.show_apply_cb)
        outer_box.append(self.perms_box)

    def loadTree(self, target_tree: ET.Element):
        self.target_tree = target_tree

    def onPermsEnabledChanged(self, *args):
        self.perms_box.set_visible(self.perms_enabled.get_active())

        permissions = self.target_tree.find("permissions")
        if self.perms_enabled.get_active():
            if permissions is None:
                ET.SubElement(self.target_tree, "permissions")
        else:
            if permissions is not None:
                self.target_tree.remove(permissions)

        self.show_apply_cb()
        self.updatePermsBox()

    def reload(self, pool_type: str):
        path = self.target_tree.find("path")
        if path is None:
            path = ET.SubElement(self.target_tree, "path")

        self.path_entry.bindText(path, self.show_apply_cb)

        self.updatePermsBox()

    def updatePermsBox(self):
        permissions = self.target_tree.find("permissions")
        if permissions is None:
            self.perms_enabled.set_active(False)
            self.perms_box.set_visible(False)
        else:
            self.perms_enabled.set_active(True)
            self.perms_box.set_visible(True)

            self.perms_box.connectData(permissions)
