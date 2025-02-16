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
from realms.ui.components.bindable_entries import (
    BindableComboRow,
    BindableEntryRow,
    BindableSwitchRow,
)

from .base_device_page import BaseDevicePage


class TPMPage(BaseDevicePage):
    def build(self):
        self.group = Adw.PreferencesGroup()
        self.prefs_page.add(self.group)

        self.model_row = BindableComboRow(
            ["tpm-tis", "tpm-crb", "tpm-spapr", "spapr-tpm-proxy"], title="TPM model"
        )
        self.group.add(self.model_row)

        self.backend_row = BindableComboRow(
            ["passthrough", "emulator"], title="Backend type"
        )
        self.group.add(self.backend_row)

        self.version_row = BindableComboRow(["1.2", "2.0"], "", title="TPM version")
        self.group.add(self.version_row)

        self.source_row = BindableEntryRow(title="Source device")
        self.group.add(self.source_row)

        self.persistent_state_row = BindableSwitchRow(
            "yes", "no", False, title="Persist swtpm state"
        )
        self.group.add(self.persistent_state_row.getWidget())

        self.secret_row = BindableEntryRow(title="Encryption-secret UUID")
        self.group.add(self.secret_row)

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

        backend = self.xml_tree.find("backend")
        if backend is None:
            backend = ET.SubElement(self.xml_tree, "backend")
        self.backend_row.bindAttr(backend, "type", self.onBackendChanged)

        self.bindBackend()

    def bindBackend(self):
        self.source_row.unbind()
        self.version_row.unbind()
        self.persistent_state_row.unbind()
        self.secret_row.unbind()

        backend = self.xml_tree.find("backend")
        if backend.get("type") == "passthrough":
            self.source_row.set_visible(True)
            device = backend.find("device")
            if device is None:
                device = ET.SubElement(backend, "device")
            self.source_row.bindAttr(device, "path", self.showApply)
            self.version_row.set_visible(False)
            self.persistent_state_row.getWidget().set_visible(False)
            self.secret_row.set_visible(False)
        else:
            self.source_row.set_visible(False)
            self.version_row.set_visible(True)
            self.version_row.bindAttr(backend, "version", self.showApply)
            self.persistent_state_row.getWidget().set_visible(True)
            self.persistent_state_row.bindAttr(
                backend, "persistent_state", self.showApply
            )
            self.secret_row.set_visible(True)
            encryption = backend.find("encryption")
            if encryption is None:
                encryption = ET.Element("encryption")
            self.secret_row.bindAttr(encryption, "secret", self.onSecretChanged)

    def onBackendChanged(self):
        backend = self.xml_tree.find("backend")
        backend.clear()
        backend.set("type", self.backend_row.getSelectedString())
        self.bindBackend()
        self.showApply()

    def onSecretChanged(self):
        backend = self.xml_tree.find("backend")
        encryption = backend.find("encryption")
        if encryption is None:
            encryption = ET.Element("encryption")
        secret = self.secret_row.getWidget().get_text()
        if secret == "":
            if encryption is not None:
                backend.remove(encryption)
        else:
            if encryption is None:
                backend.append(self.secret_row.elem)

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "TPM"

    def getDescription(self) -> str:
        return "Trusted Platform Module"

    def getIconName(self) -> str:
        return "key-login-symbolic"
