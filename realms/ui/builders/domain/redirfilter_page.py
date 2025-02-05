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
from realms.ui.builders.bindable_entries import BindableEntryRow, BindableSwitchRow

from .base_device_page import BaseDevicePage


class FilterRow(Adw.ExpanderRow):
    def __init__(self, xml_tree: ET.Element, parent, index: int):
        super().__init__(title=f"Filter rule { index }", expanded=False)

        self.xml_tree = None

        self.allow_row = BindableSwitchRow("yes", "no", title="Allow device")
        self.add_row(self.allow_row.getWidget())
        self.allow_row.bindAttr(xml_tree, "allow", parent.showApply)

        self.class_row = BindableEntryRow(
            title="USB class code", tooltip_text="Use -1 to allow any"
        )
        self.add_row(self.class_row)
        self.class_row.bindAttr(xml_tree, "class", parent.showApply)

        self.vendor_row = BindableEntryRow(
            title="USB vendor code", tooltip_text="Use -1 to allow any"
        )
        self.add_row(self.vendor_row)
        self.vendor_row.bindAttr(xml_tree, "vendor", parent.showApply)

        self.product_row = BindableEntryRow(
            title="USB product code", tooltip_text="Use -1 to allow any"
        )
        self.add_row(self.product_row)
        self.product_row.bindAttr(xml_tree, "product", parent.showApply)

        self.version_row = BindableEntryRow(
            title="USB version code", tooltip_text="Use -1 to allow any"
        )
        self.add_row(self.version_row)
        self.version_row.bindAttr(xml_tree, "version", parent.showApply)

        delete_row = Adw.ActionRow()
        self.add_row(delete_row)
        self.delete_btn = iconButton(
            "Remove",
            "user-trash-symbolic",
            lambda b: parent.onRemoveClicked(self),
            css_classes=["flat"],
        )
        delete_row.add_prefix(self.delete_btn)


class RedirfilterPage(BaseDevicePage):
    def __init__(
        self, parent, xml_tree: ET.Element, use_for_adding=False, can_update=False
    ):
        super().__init__(parent, xml_tree, use_for_adding, can_update)

        self.rows = []

    def build(self):
        self.group = Adw.PreferencesGroup()
        self.prefs_page.add(self.group)

        add_btn = iconButton(
            "Add rule", "list-add-symbolic", self.onAddClicked, css_classes=["flat"]
        )
        self.group.set_header_suffix(add_btn)

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

        for row in self.rows:
            self.group.remove(row)
        self.rows.clear()

        for usbdev in self.xml_tree.findall("usbdev"):
            self.addRow(usbdev)

    def addRow(self, xml_tree):
        row = FilterRow(xml_tree, self, len(self.rows))
        self.group.add(row)
        self.rows.append(row)

    def onAddClicked(self, btn):
        self.addRow(ET.Element("usbdev"))
        self.showApply()

    def onRemoveClicked(self, row: FilterRow):
        self.group.remove(row)
        self.rows.remove(row)
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "Redirected device filter"

    def getDescription(self) -> str:
        return "Redirected USB device filter"

    def getIconName(self) -> str:
        return "computer-chip-symbolic"
