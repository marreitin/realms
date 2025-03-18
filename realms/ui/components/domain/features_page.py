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

from realms.ui.components.bindable_entries import (
    ExistentialComboRow,
    ExistentialSwitchRow,
)

from .base_device_page import BaseDevicePage


class FeaturesPage(BaseDevicePage):
    def __init__(
        self, parent, xml_tree: ET.Element, use_for_adding=False, can_update=False
    ):
        super().__init__(parent, xml_tree, use_for_adding, can_update)

        self.basic_rows = []

    def build(self):
        self.general_group = Adw.PreferencesGroup(
            title="Hypervisor features",
            description="Features will use hypervisor default if unspecified",
        )
        self.prefs_page.add(self.general_group)

        self.basic_rows = [
            ExistentialSwitchRow("acpi", {}, title="ACPI"),
            ExistentialSwitchRow("apic", {}, title="APIC"),
            ExistentialComboRow(
                "ccf-assist",
                "state",
                ["on", "off"],
                "",
                title="Count cache flush assist",
            ),
            ExistentialComboRow(
                "cfpf",
                "value",
                ["broken", "workaround", "fixed"],
                "",
                title="Cache flush on privilege change",
            ),
            ExistentialSwitchRow("gic", {}, title="General interrupt controller"),
            ExistentialComboRow(
                "hap", "state", ["on", "off"], "", title="Hardware assisted paging"
            ),
            ExistentialComboRow(
                "hpt",
                "resizing",
                ["enabled", "disabled", "required"],
                "",
                title="Hash page table",
            ),
            ExistentialComboRow(
                "htm", "state", ["on", "off"], "", title="Hardware transactional memory"
            ),
            ExistentialComboRow(
                "ibs",
                "value",
                ["broken", "workaround", "fixed-ibs", "fixed-ccd", "fixed-na"],
                "",
                title="Indirect branch speculation",
            ),
            ExistentialComboRow(
                "ioapic", "driver", ["kvm", "qemu"], "", title="IO Apic"
            ),
            ExistentialComboRow(
                "msrs",
                "unknown",
                ["ignore", "fault"],
                "",
                title="Model specific registers",
            ),
            ExistentialComboRow(
                "nested-hv", "state", ["on", "off"], "", title="Nested virtualization"
            ),
            ExistentialSwitchRow("pae", {}, title="Physical address extension mode"),
            ExistentialSwitchRow(
                "privnet", {}, title="Create private network namespace"
            ),
            ExistentialComboRow(
                "pvspinlock", "state", ["on", "off"], "", title="Paravirtual spinlock"
            ),
            ExistentialComboRow(
                "pmu", "state", ["on", "off"], "", title="Performance monitoring unit"
            ),
            ExistentialComboRow(
                "ps2", "state", ["on", "off"], "", title="Emulate PS/2 controller"
            ),
            ExistentialComboRow(
                "async-teardown",
                "enabled",
                ["yes", "no"],
                "",
                title="QEMU asynchronous teardown",
            ),
            ExistentialComboRow(
                "vmcoreinfo", "state", ["on", "off"], "", title="QEMU vmcoreinfo"
            ),
            ExistentialComboRow(
                "ras", "enabled", ["yes", "no"], "", title="Report host memory errors"
            ),
            ExistentialComboRow(
                "sbbc",
                "value",
                ["broken", "workaround", "fixed"],
                "",
                title="Speculation barrier bounds checking",
            ),
            ExistentialComboRow(
                "smm", "state", ["on", "off"], "", title="System management mode"
            ),
            ExistentialSwitchRow("viridian", {}, title="Viridian"),
            ExistentialComboRow(
                "vmport", "state", ["on", "off"], "", title="VMware IO port emulation"
            ),
        ]

        self.basic_rows.sort(key=lambda r: r.getWidget().get_title().lower())

        for row in self.basic_rows:
            self.general_group.add(row.getWidget())

        self.updateData()

    def updateData(self):
        features = self.xml_tree.find("features")
        if features is None:
            features = ET.SubElement(self.xml_tree, "features")
        for row in self.basic_rows:
            row.bind(features, self.showApply)

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "Hypervisor features"

    def getDescription(self) -> str:
        return "Optional hypervisor features"

    def getIconName(self) -> str:
        return "wrench-wide-symbolic"
