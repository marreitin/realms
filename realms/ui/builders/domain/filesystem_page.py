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

from realms.ui.builders import iconButton
from realms.ui.builders.bindable_entries import (
    BindableComboRow,
    BindableEntryRow,
    ExistentialComboRow,
    ExistentialSwitchRow,
)

from .base_device_page import BaseDevicePage

"""
type
    mount,file
source
    dir for mount
    file for file
target
    always dir
readonly
"""


class FilesystemPage(BaseDevicePage):
    def build(self):
        group = Adw.PreferencesGroup(
            title=self.getTitle(),
            description="Export a host volume or directory to the domain",
        )
        self.prefs_page.add(group)

        self.type_row = BindableComboRow(["mount", "file"], title="Filesystem type")
        group.add(self.type_row)

        self.driver_type_row = ExistentialComboRow(
            "driver",
            "type",
            ["loop", "path", "handle", "ploop", "virtiofs"],
            "",
            title="Driver type",
        )
        group.add(self.driver_type_row)

        self.source_row = BindableEntryRow(title="Source")
        group.add(self.source_row)

        if self.parent.domain.connection.is_local:
            browse_btn = iconButton(
                "",
                "inode-directory-symbolic",
                self.onBrowseClicked,
                css_classes=["flat"],
                tooltip_text="Browse local paths",
            )
            self.source_row.add_suffix(browse_btn)

        self.target_row = BindableEntryRow(title="Target")
        group.add(self.target_row)

        self.readonly_switch_row = ExistentialSwitchRow(
            "readonly", {}, title="Readonly"
        )
        group.add(self.readonly_switch_row.getWidget())

        if not self.use_for_adding:
            delete_row = Adw.ActionRow()
            group.add(delete_row)
            self.delete_btn = iconButton(
                "Remove", "user-trash-symbolic", self.deleteDevice, css_classes=["flat"]
            )
            delete_row.add_prefix(self.delete_btn)

        self.updateData()

    def updateData(self):
        self.type_row.bindAttr(self.xml_tree, "type", self.onTypeChanged)
        self.driver_type_row.bind(self.xml_tree, self.showApply)

        target = self.xml_tree.find("target")
        if target is None:
            target = ET.SubElement(self.xml_tree, "target")
        self.target_row.bindAttr(target, "dir", self.showApply)

        self.readonly_switch_row.bind(self.xml_tree, self.showApply)

        self.updateSource()

    def updateSource(self):
        source = self.xml_tree.find("source")
        if source is None:
            source = ET.SubElement(self.xml_tree, "source")
        t = self.type_row.getSelectedString()
        self.source_row.set_visible(True)
        if t == "mount":
            self.source_row.bindAttr(source, "dir", self.showApply)
        elif t == "file":
            self.source_row.bindAttr(source, "file", self.showApply)
        else:
            self.source_row.set_visible(False)

    def onBrowseClicked(self, btn):
        t = self.type_row.getSelectedString()
        if t == "file":
            open_dialog = Gtk.FileDialog(title="Pick source file")
            open_dialog.open(None, None, self.onFileDialogCB)
        elif t == "mount":
            open_dialog = Gtk.FileDialog(title="Pick source directory")
            open_dialog.select_folder(None, None, self.onFileDialogCB)

    def onFileDialogCB(self, dialog, result):
        try:
            t = self.type_row.getSelectedString()
            if t == "file":
                file = dialog.open_finish(result)
                if file is not None:
                    self.source_row.set_text(file.get_path())
            elif t == "mount":
                file = dialog.select_folder_finish(result)
                if file is not None:
                    self.source_row.set_text(file.get_path())
            self.showApply()
        except:
            pass

    def onTypeChanged(self, *args):
        source = self.xml_tree.find("source")
        source.clear()
        self.updateSource()
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return f"{ self.xml_tree.get('type', '').capitalize() } filesystem"

    def getDescription(self) -> str:
        return "Filesystem exported into the domain"

    def getIconName(self) -> str:
        return "file-manager-symbolic"
