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
    BindableDropDown,
    BindableEntry,
    BindableEntryRow,
)
from realms.ui.builders.domain.address_row import AddressRow
from realms.ui.builders.domain.boot_order_row import BootOrderRow
from realms.ui.builders.generic_preferences_row import GenericPreferencesRow

from .base_device_page import BaseDevicePage


class SourceRow(GenericPreferencesRow):
    """Row for disk source. Only really supports file and volumes.
    -> Any other sources should be added as pool anyways, prevents
    excessive code duplication."""

    def __init__(self, xml_tree: ET.Element, show_apply_cb, **kwargs):
        super().__init__(**kwargs)

        self.xml_tree = xml_tree
        self.show_apply_cb = show_apply_cb

        box = Gtk.Box(spacing=6, hexpand=True)
        self.addChild(box)

        box.append(Gtk.Label(label="Disk source", hexpand=True, halign=Gtk.Align.START))

        self.source_types = ["file", "volume", "block"]
        self.source_type = BindableDropDown(self.source_types)
        self.source_type.bindAttr(self.xml_tree, "type", self.__onSourceTypeChanged__)
        box.append(self.source_type)

        self.file_entry = BindableEntry(placeholder_text="Source file path")
        self.addChild(self.file_entry)

        self.dev_entry = BindableEntry(placeholder_text="Source device")
        self.addChild(self.dev_entry)

        box2 = Gtk.Box(spacing=6, homogeneous=True, hexpand=True)
        self.addChild(box2)

        self.pool_entry = BindableEntry(placeholder_text="Source pool")
        box2.append(self.pool_entry)

        self.volume_entry = BindableEntry(placeholder_text="Source volume")
        box2.append(self.volume_entry)

        self.__updateSourceRow__()

    def __updateSourceRow__(self):
        source = self.xml_tree.find("source")
        if source is None:
            source = ET.SubElement(self.xml_tree, "source")

        self.file_entry.set_visible(False)
        self.file_entry.unbind()
        self.dev_entry.set_visible(False)
        self.dev_entry.unbind()
        self.pool_entry.set_visible(False)
        self.pool_entry.unbind()
        self.volume_entry.set_visible(False)
        self.volume_entry.unbind()

        selected = self.source_type.getSelectedString()
        if selected == "file":
            self.file_entry.set_visible(True)
            self.file_entry.bindAttr(source, "file", self.show_apply_cb)
        elif selected == "volume":
            self.pool_entry.set_visible(True)
            self.pool_entry.bindAttr(source, "pool", self.show_apply_cb)
            self.volume_entry.set_visible(True)
            self.volume_entry.bindAttr(source, "volume", self.show_apply_cb)
        elif selected == "block":
            self.dev_entry.set_visible(True)
            self.dev_entry.bindAttr(source, "dev", self.show_apply_cb)
        else:  # Other, unsupported types
            self.file_entry.set_visible(False)
            self.file_entry.unbind()
            self.pool_entry.set_visible(False)
            self.pool_entry.unbind()
            self.volume_entry.set_visible(False)
            self.volume_entry.unbind()

    def setXML(self, xml_tree: ET.Element):
        self.xml_tree = xml_tree
        self.__updateSourceRow__()

    def __onSourceTypeChanged__(self, *_):
        source = self.xml_tree.find("source")
        if source is not None:
            source.clear()
        self.__updateSourceRow__()
        self.show_apply_cb()


class DiskPage(BaseDevicePage):
    """Page for disk device."""

    def build(self):
        self.group = Adw.PreferencesGroup(
            title=self.getTitle(), description="Virtual disk device"
        )
        self.prefs_page.add(self.group)

        self.domain_caps = self.parent.domain.connection.getDomainCapabilities()

        self.device_type_row = BindableComboRow(
            self.domain_caps.devices["disk"]["diskDevice"], title="Disk hardware type"
        )
        self.group.add(self.device_type_row)

        self.snapshot_row = BindableComboRow(
            ["internal", "external", "no", "manual"],
            title="Snapshot mode",
            subtitle="Set how this disk behaves when taking a snapshot",
        )
        self.group.add(self.snapshot_row)

        self.source_row = SourceRow(self.xml_tree, self.showApply)
        self.group.add(self.source_row)

        self.driver_row = BindableComboRow(
            ["tap", "tap2", "phy", "file", "raw", "bochs", "qcow2", "qed"],
            "",
            title="Driver type",
        )
        self.group.add(self.driver_row)

        self.readonly_switch_row = Adw.SwitchRow(
            title="Read-only", subtitle="Make disk read-only"
        )
        self.readonly_switch_row.connect("notify::active", self.onReadonlyChanged)
        self.group.add(self.readonly_switch_row)

        self.target_device_row = BindableEntryRow(title="Target device name")
        self.group.add(self.target_device_row)

        self.target_bus_name_row = BindableComboRow(
            self.domain_caps.devices["disk"]["bus"], "", title="Target bus"
        )
        self.group.add(self.target_bus_name_row)

        self.boot_order_row = BootOrderRow(self.xml_tree, self.showApply)
        self.group.add(self.boot_order_row)

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
        self.device_type_row.bindAttr(self.xml_tree, "device", self.showApply)
        self.snapshot_row.bindAttr(self.xml_tree, "snapshot", self.showApply)

        readonly = self.xml_tree.find("readonly")
        self.readonly_switch_row.disconnect_by_func(self.onReadonlyChanged)
        if readonly is not None:
            self.readonly_switch_row.set_active(True)
        else:
            self.readonly_switch_row.set_active(False)
        self.readonly_switch_row.connect("notify::active", self.onReadonlyChanged)

        target = self.xml_tree.find("target")
        if target is None:
            target = ET.SubElement(self.xml_tree, "target")
        self.target_device_row.bindAttr(target, "dev", self.showApply)
        self.target_bus_name_row.bindAttr(target, "bus", self.showApply)

        driver = self.xml_tree.find("driver")
        if driver is None:
            driver = ET.Element("driver")
        self.driver_row.bindAttr(driver, "type", self.onDriverChanged)

        self.source_row.setXML(self.xml_tree)
        self.boot_order_row.setXML(self.xml_tree)
        self.address_row.setXML(self.xml_tree)

    def onReadonlyChanged(self, row, *_):
        readonly = self.xml_tree.find("readonly")
        if row.get_active():
            if readonly is None:
                readonly = ET.SubElement(self.xml_tree, "readonly")
        else:
            if readonly is not None:
                self.xml_tree.remove(readonly)
        self.showApply()

    def onDriverChanged(self, *_):
        driver = self.xml_tree.find("driver")
        if self.driver_row.getSelectedString() == "":
            if driver is not None:
                self.xml_tree.remove(driver)
        else:
            if driver is None:
                self.xml_tree.append(self.driver_row.elem)
            if self.driver_row.getSelectedString() in ["raw", "bochs", "qcow2", "qed"]:
                driver.set("name", "qemu")
            else:
                driver.set("name", "aio")
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        t = self.xml_tree.get("device", "")
        if t == "disk":
            return "Harddisk"
        if t == "cdrom":
            return "CD-Rom"
        if t == "floppy":
            return "Floppy Disk"
        return t.capitalize()

    def getDescription(self) -> str:
        return "Disk device"

    def getIconName(self) -> str:
        t = self.xml_tree.get("device")
        if t == "disk":
            return "harddisk-symbolic"
        if t == "cdrom":
            return "cd-symbolic"
        if t == "floppy":
            return "floppy-symbolic"
        return "harddisk-symbolic"
