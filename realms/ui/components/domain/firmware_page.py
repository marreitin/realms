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

from realms.libvirt_wrap.domain_capabilities import DomainCapabilities
from realms.ui.components import GenericPreferencesRow, warningLabelRow
from realms.ui.components.bindable_entries import (
    BindableComboRow,
    BindableDropDown,
    BindableSwitchRow,
)

from .base_device_page import BaseDevicePage


class LoaderRow(GenericPreferencesRow):
    def __init__(
        self,
        xml_tree,
        domain_caps: DomainCapabilities,
        show_apply_cb: callable,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.xml_tree = xml_tree
        self.domain_caps = domain_caps
        self.show_apply_cb = show_apply_cb

        box = Gtk.Box(spacing=6)
        self.addChild(box)

        box.append(
            Gtk.Label(label="Firmware loader", hexpand=True, halign=Gtk.Align.START)
        )

        self.enable_switch = Gtk.Switch()
        loader = self.xml_tree.find("os").find("loader")
        if loader is not None:
            self.enable_switch.set_active(True)
        self.enable_switch.connect("notify::active", self.onEnableChanged)
        box.append(self.enable_switch)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.addChild(self.content_box)

        box = Gtk.Box(spacing=12)
        self.content_box.append(box)

        inner_box = Gtk.Box(spacing=6, hexpand=True)
        box.append(inner_box)
        inner_box.append(Gtk.Label(label="Readonly", halign=Gtk.Align.START))
        self.readonly = BindableDropDown(
            self.domain_caps.os["loader"]["readonly"], "", hexpand=True
        )
        inner_box.append(self.readonly)

        inner_box = Gtk.Box(spacing=6, hexpand=True)
        box.append(inner_box)
        inner_box.append(Gtk.Label(label="Secure", halign=Gtk.Align.START))
        self.secure = BindableDropDown(
            self.domain_caps.os["loader"]["secure"], "", hexpand=True
        )
        inner_box.append(self.secure)

        inner_box = Gtk.Box(spacing=6, hexpand=True)
        box.append(inner_box)
        inner_box.append(Gtk.Label(label="Type", halign=Gtk.Align.START))
        self.type = BindableDropDown(
            self.domain_caps.os["loader"]["type"], "", hexpand=True
        )
        inner_box.append(self.type)

        self.loader_source = BindableDropDown(
            self.domain_caps.os["loader"]["values"], "", hexpand=True
        )
        self.content_box.append(self.loader_source)

        self.updateData()

    def updateData(self):
        loader = self.xml_tree.find("os").find("loader")
        if loader is not None:
            self.enable_switch.set_active(True)
            self.content_box.set_visible(True)

            self.readonly.bindAttr(loader, "readonly", self.show_apply_cb)
            self.secure.bindAttr(loader, "secure", self.show_apply_cb)
            self.type.bindAttr(loader, "type", self.show_apply_cb)
            self.loader_source.bindText(loader, self.show_apply_cb)
        else:
            self.enable_switch.set_active(False)
            self.content_box.set_visible(False)
            self.readonly.unbind()
            self.secure.unbind()
            self.type.unbind()
            self.loader_source.unbind()

    def onEnableChanged(self, switch, *args):
        loader = self.xml_tree.find("os").find("loader")
        if switch.get_active():
            if loader is None:
                loader = ET.SubElement(self.xml_tree.find("os"), "loader")
        else:
            if loader is not None:
                self.xml_tree.remove(loader)

        self.updateData()
        self.show_apply_cb()


class FirmwarePage(BaseDevicePage):
    def build(self):

        prefs_group = Adw.PreferencesGroup(title="Firmware")
        self.prefs_page.add(prefs_group)

        domain_caps = self.parent.domain.connection.getDomainCapabilities()

        self.firmware_row = BindableComboRow(
            domain_caps.os["firmware"],
            "",
            title="Firmware template",
            subtitle="Select firmware template to use",
        )
        os = self.xml_tree.find("os")
        prefs_group.add(self.firmware_row)

        self.loader_row = LoaderRow(
            self.xml_tree,
            domain_caps,
            self.showApply,
        )
        prefs_group.add(self.loader_row)

        if len(os.findall("boot")) != 0:
            prefs_group.add(
                warningLabelRow(
                    "There are legacy boot entries in the OS-section. Per-device boot entries will not work",
                    "warning",
                    margin=12,
                )
            )

        if self.xml_tree.find(".//boot") is None:
            prefs_group.add(
                warningLabelRow(
                    "You have not defined any bootable devices", "error", margin=12
                )
            )

        self.features_group = Adw.PreferencesGroup(title="Firmware features")
        self.prefs_page.add(self.features_group)
        if os.get("firmware") != "efi":
            self.features_group.set_visible(False)

        self.secure_boot_row = BindableSwitchRow(
            "yes", "no", title="Secure boot enabled"
        )
        self.features_group.add(self.secure_boot_row.switch_row)

        self.enrolled_keys_row = BindableSwitchRow(
            "yes", "no", title="Enroll default certificates"
        )
        self.features_group.add(self.enrolled_keys_row.switch_row)

        self.updateData()

    def updateData(self):
        os = self.xml_tree.find("os")
        firmware = os.find("firmware")

        self.firmware_row.bindAttr(os, "firmware", self.onFirmwareTypeChanged)

        self.loader_row.xml_tree = self.xml_tree
        self.loader_row.updateData()

        if self.firmware_row.getSelectedString() == "efi":
            self.features_group.set_visible(True)

            if firmware is None:
                firmware = ET.SubElement(os, "firmware")

            secure_boot = None
            enrolled_keys = None

            for f in firmware.findall("feature"):
                if f.get("name") == "secure-boot":
                    secure_boot = f
                elif f.get("name") == "enrolled-keys":
                    enrolled_keys = f

            if secure_boot is None:
                secure_boot = ET.SubElement(
                    firmware, "feature", attrib={"name": "secure-boot"}
                )
            if enrolled_keys is None:
                enrolled_keys = ET.SubElement(
                    firmware, "feature", attrib={"name": "enabled-keys"}
                )
            self.secure_boot_row.bindAttr(secure_boot, "enabled", self.showApply)
            self.enrolled_keys_row.bindAttr(enrolled_keys, "enabled", self.showApply)
        else:
            self.features_group.set_visible(False)
            self.secure_boot_row.unbind()
            self.enrolled_keys_row.unbind()

    def onFirmwareTypeChanged(self):
        self.updateData()
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "Firmware"

    def getDescription(self) -> str:
        return "Firmware settings"

    def getIconName(self) -> str:
        return "application-x-firmware-symbolic"
