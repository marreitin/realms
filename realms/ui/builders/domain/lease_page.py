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

from realms.ui.builders import iconButton
from realms.ui.builders.bindable_entries import BindableEntryRow

from .base_device_page import BaseDevicePage


class LeasePage(BaseDevicePage):
    """Page for a lock."""

    def build(self):
        self.group = Adw.PreferencesGroup(title=self.getTitle())
        self.prefs_page.add(self.group)

        self.lockspace_row = BindableEntryRow(title="Lockspace")
        self.group.add(self.lockspace_row)

        self.key_row = BindableEntryRow(title="Lease key")
        self.group.add(self.key_row)

        self.target_path_row = BindableEntryRow(title="Target path")
        self.group.add(self.target_path_row)

        self.target_offset_row = BindableEntryRow(title="Target offset")
        self.group.add(self.target_offset_row)

        if not self.use_for_adding:
            delete_row = Adw.ActionRow()
            self.group.add(delete_row)
            self.delete_btn = iconButton(
                "Remove", "user-trash-symbolic", self.deleteDevice, css_classes=["flat"]
            )
            delete_row.add_prefix(self.delete_btn)

        self.updateData()

    def updateData(self):
        self.group.set_title(self.getTitle())

        lockspace = self.xml_tree.find("lockspace")
        if lockspace is None:
            lockspace = ET.SubElement(self.xml_tree, "lockspace")
        self.lockspace_row.bindText(lockspace, self.showApply)

        key = self.xml_tree.find("key")
        if key is None:
            key = ET.SubElement(self.xml_tree, "key")
        self.key_row.bindText(key, self.showApply)

        target = self.xml_tree.find("target")
        if target is None:
            target = ET.SubElement(self.xml_tree, "target")
        self.target_path_row.bindAttr(target, "path", self.showApply)
        self.target_offset_row.bindAttr(target, "offset", self.showApply)

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "Device lease"

    def getDescription(self) -> str:
        return "Lock manager lease"

    def getIconName(self) -> str:
        return "padlock2-open-symbolic"
