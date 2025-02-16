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

from realms.ui.components import iconButton
from realms.ui.components.bindable_entries import BindableComboRow, BindableEntryRow
from realms.ui.components.domain.address_row import AddressRow

from .base_device_page import BaseDevicePage


class SmartcardPage(BaseDevicePage):
    def __init__(
        self, parent, xml_tree: ET.Element, use_for_adding=False, can_update=False
    ):
        super().__init__(parent, xml_tree, use_for_adding, can_update)

    def build(self):
        self.group = Adw.PreferencesGroup()
        self.prefs_page.add(self.group)

        self.mode_row = BindableComboRow(
            ["host", "host-certificates", "passthrough"], title="Smartcard mode"
        )
        self.group.add(self.mode_row)

        self.host_cert_rows = []
        self.host_cert_rows.append(BindableEntryRow(title="Host certificate 1"))
        self.host_cert_rows.append(BindableEntryRow(title="Host certificate 2"))
        self.host_cert_rows.append(BindableEntryRow(title="Host certificate 3"))

        for row in self.host_cert_rows:
            self.group.add(row)

        self.database_row = BindableEntryRow(title="Alternate database directory")
        self.group.add(self.database_row)

        self.address_row = AddressRow(self.xml_tree, self.showApply)
        self.group.add(self.address_row)

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

        self.mode_row.bindAttr(self.xml_tree, "mode", self.onModeChanged)

        for row in self.host_cert_rows:
            row.set_visible(False)
        self.database_row.set_visible(False)

        mode = self.mode_row.getSelectedString()
        if mode == "host-certificates":
            certs = self.xml_tree.findall("certificate")
            for _ in range(3 - len(certs)):
                certs.append(ET.SubElement(self.xml_tree, "certificate"))
            for cert, row in zip(certs, self.host_cert_rows):
                row.bindText(cert, self.showApply)
                row.set_visible(True)

            db = self.xml_tree.find("database")
            if db is None:
                db = ET.Element("database")
            self.database_row.bindText(db, self.onDatabaseChanged)
            self.database_row.set_visible(True)
        elif mode == "passthrough":
            pass

    def onModeChanged(self):
        self.xml_tree.clear()
        self.xml_tree.set("mode", self.mode_row.getSelectedString())
        self.updateData()
        self.showApply()

    def onDatabaseChanged(self):
        db = self.xml_tree.find("database")
        if self.database_row.get_text() == "":
            if db is not None:
                self.xml_tree.remove(db)
        else:
            if db is None:
                self.xml_tree.add(self.database_row.elem)
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "Smartcard"

    def getDescription(self) -> str:
        return "Smartcard reader"

    def getIconName(self) -> str:
        return "smartcard-symbolic"
