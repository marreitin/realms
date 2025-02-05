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

from realms.helpers import getETText
from realms.ui.builders import iconButton, propertyRow
from realms.ui.builders.bindable_entries import BindableComboRow, BindableEntryRow

from .base_device_page import BaseDevicePage

"""
Page for general domain settings
"""


class GeneralPage(BaseDevicePage):
    def __init__(
        self, parent, xml_tree: ET.Element, use_for_adding=False, can_update=False
    ):
        super().__init__(parent, xml_tree, use_for_adding, can_update)

    def build(self):
        self.general_group = Adw.PreferencesGroup(title="General")
        self.prefs_page.add(self.general_group)

        name = self.xml_tree.find("name")
        self.general_group.add(
            propertyRow("Name", self.parent.window_ref.window, subtitle=getETText(name))
        )

        uuid = self.xml_tree.find("uuid")
        self.general_group.add(
            propertyRow("UUID", self.parent.window_ref.window, subtitle=getETText(uuid))
        )
        self.title_row = BindableEntryRow(title="Title")
        self.general_group.add(self.title_row)

        self.description_row = BindableEntryRow(title="Description")
        self.general_group.add(self.description_row)

        self.autostart_row = Adw.SwitchRow(
            title="Autostart", subtitle="Start domain on host boot"
        )
        self.general_group.add(self.autostart_row)
        self.autostart_row.connect("notify::active", self.onAutostartChanged)

        action_row = Adw.ActionRow()
        self.general_group.add(action_row)
        self.delete_btn = iconButton(
            "Delete",
            "user-trash-symbolic",
            self.parent.onDeleteClicked,
            css_classes=["destructive-action"],
        )
        action_row.add_prefix(self.delete_btn)

        hypervisor_group = Adw.PreferencesGroup(
            title="General domain options",
            description="Available options depend on the host",
        )
        self.prefs_page.add(hypervisor_group)

        self.driver_caps = self.parent.domain.connection.getDriverCapabilities()

        self.type_row = BindableComboRow(
            self.driver_caps.os_types,
            title="OS Type",
            subtitle="How the domain is run, i.e. full virtualization",
        )
        hypervisor_group.add(self.type_row)

        os_type = self.xml_tree.find("os").find("type")
        available_archs = self.driver_caps.guest_types[os_type.text]
        self.arch_row = BindableComboRow(
            list(available_archs.keys()), title="Guest Architecture"
        )
        hypervisor_group.add(self.arch_row)

        if os_type.get("arch") in available_archs:
            self.domain_hypervisor = BindableComboRow(
                available_archs[os_type.get("arch")]["hypervisors"],
                title="Domain hypervisor",
            )

            self.machine_row = BindableComboRow(
                available_archs[os_type.get("arch")]["machines"], title="Machine type"
            )
        else:
            self.domain_hypervisor = BindableComboRow(
                [],
                title="Domain hypervisor",
            )

            self.machine_row = BindableComboRow([], title="Machine type")

        hypervisor_group.add(self.domain_hypervisor)
        hypervisor_group.add(self.machine_row)

        emulator = self.xml_tree.find("devices").find("emulator")
        self.emulator_row = propertyRow("Emulator", self.parent.window_ref.window)
        self.emulator_row.set_subtitle(getETText(emulator))
        hypervisor_group.add(self.emulator_row)

        events_group = Adw.PreferencesGroup(
            title="Events", description="Choose automatic action on domain event"
        )
        self.prefs_page.add(events_group)

        self.on_poweroff_row = BindableComboRow(
            ["destroy", "restart", "preserve", "rename-restart"], title="On poweroff"
        )
        events_group.add(self.on_poweroff_row)

        self.on_reboot_row = BindableComboRow(
            ["restart", "destroy", "preserve", "rename-restart"], title="On reboot"
        )
        events_group.add(self.on_reboot_row)

        self.on_crash_row = BindableComboRow(
            ["restart", "destroy", "preserve", "rename-restart"], title="On crash"
        )
        events_group.add(self.on_crash_row)
        self.on_lockfail_row = BindableComboRow(
            ["ignore", "poweroff", "restart", "pause"], title="On lock failure"
        )
        events_group.add(self.on_lockfail_row)

        self.updateData()

    def updateData(self):
        title = self.xml_tree.find("title")
        if title is None:
            title = ET.SubElement(self.xml_tree, "title")
        self.title_row.bindText(title, self.showApply)

        description = self.xml_tree.find("description")
        if description is None:
            description = ET.SubElement(self.xml_tree, "description")
        self.description_row.bindText(description, self.showApply)

        self.autostart_row.disconnect_by_func(self.onAutostartChanged)
        self.autostart_row.set_active(self.parent.domain.getAutostart())
        self.autostart_row.connect("notify::active", self.onAutostartChanged)

        os_type = self.xml_tree.find("os").find("type")
        self.type_row.bindText(os_type, self.onOSTypeChanged)
        self.arch_row.bindAttr(os_type, "arch", self.onArchChanged)

        self.domain_hypervisor.bindAttr(self.xml_tree, "type", self.showApply)
        self.machine_row.bindAttr(os_type, "machine", self.showApply)

        on_poweroff = self.xml_tree.find("on_poweroff")
        if on_poweroff is None:
            on_poweroff = ET.SubElement(self.xml_tree, "on_poweroff")
        self.on_poweroff_row.bindText(on_poweroff, self.showApply)

        on_reboot = self.xml_tree.find("on_reboot")
        if on_reboot is None:
            on_reboot = ET.SubElement(self.xml_tree, "on_reboot")
        self.on_reboot_row.bindText(on_reboot, self.showApply)

        on_crash = self.xml_tree.find("on_crash")
        if on_crash is None:
            on_crash = ET.SubElement(self.xml_tree, "on_crash")
        self.on_crash_row.bindText(on_crash, self.showApply)

        on_lockfail = self.xml_tree.find("on_lockfailure")
        if on_lockfail is None:
            on_lockfail = ET.SubElement(self.xml_tree, "on_lockfailure")
        self.on_lockfail_row.bindText(on_lockfail, self.showApply)

    def onOSTypeChanged(self):
        os_type = self.xml_tree.find("os").find("type")
        available_archs = self.driver_caps.guest_types[os_type.text]
        self.arch_row.setSelection(list(available_archs.keys()))
        self.arch_row.bindAttr(os_type, "arch")

        self.onArchChanged()

    def onArchChanged(self):
        os_type = self.xml_tree.find("os").find("type")
        available_archs = self.driver_caps.guest_types[os_type.text]

        self.domain_hypervisor.setSelection(
            available_archs[os_type.get("arch")]["hypervisors"]
        )
        self.machine_row.setSelection(available_archs[os_type.get("arch")]["machines"])

        emulator = self.xml_tree.find("devices").find("emulator")
        emulator.text = available_archs[os_type.get("arch")]["emulator"]
        self.emulator_row.set_subtitle(getETText(emulator))

        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "General"

    def getIconName(self) -> str:
        return "org.gnome.Settings-symbolic"

    def getDescription(self) -> str:
        return "General domain settings"

    def onAutostartChanged(self, *args):
        self.parent.autostart = self.autostart_row.get_active()
        self.showApply()
