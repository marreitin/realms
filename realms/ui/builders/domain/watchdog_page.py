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
from realms.ui.builders.bindable_entries import BindableComboRow

from .base_device_page import BaseDevicePage


class WatchdogPage(BaseDevicePage):
    """Page for hardware watchdog."""

    def build(self):
        self.group = Adw.PreferencesGroup()
        self.prefs_page.add(self.group)

        self.model_row = BindableComboRow(
            ["itco", "i6300esb", "ib700", "diag288"], title="Model"
        )
        self.group.add(self.model_row)

        self.action_row = BindableComboRow(
            ["none", "reset", "shutdown", "poweroff", "pause", "dump", "inject-nmi"],
            "",
            title="Expiry action",
        )
        self.group.add(self.action_row)

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

        self.model_row.bindAttr(self.xml_tree, "model", self.showApply)
        self.action_row.bindAttr(self.xml_tree, "action", self.showApply)

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "Hardware Watchdog"

    def getDescription(self) -> str:
        return ""

    def getIconName(self) -> str:
        return "dog-symbolic"
