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

from realms.helpers import asyncJob, bytesToString, stringToBytes
from realms.ui.builders.bindable_entries import (
    BindableComboRow,
    BindableEntryRow,
    BindableSpinRow,
)

from .base_device_page import BaseDevicePage

"""
# Considerations
 - Set how the CPU is getting configured
 - For manual configuration set CPU model
 - Set libvirt checking how vCPUs actually appear in the domain
"""


class GeneralHardwarePage(BaseDevicePage):
    def build(self):
        prefs_group = Adw.PreferencesGroup(title="Hardware")
        self.prefs_page.add(prefs_group)

        self.vcpus_row = BindableSpinRow(
            lambda i: str(int(i)),
            title="VCPUs",
            snap_to_ticks=True,
            numeric=True,
            digits=0,
        )
        self.vcpus_row.spin_row.get_adjustment().set_step_increment(1)
        self.vcpus_row.spin_row.set_sensitive(False)
        prefs_group.add(self.vcpus_row.spin_row)

        self.memory_row = BindableEntryRow(title="Memory")
        prefs_group.add(self.memory_row)

        self.domain_caps = self.parent.domain.connection.getDomainCapabilities()

        self.config_row = BindableComboRow(
            self.domain_caps.cpu_modes,
            "",
            title="CPU configuration",
            subtitle="How the virtual CPU is configured",
        )
        prefs_group.add(self.config_row)

        self.cpu_model_row = BindableComboRow(
            self.domain_caps.custom_cpu_models, title="CPU model"
        )
        prefs_group.add(self.cpu_model_row)

        self.match_row = BindableComboRow(
            ["minimum", "exact", "strict"],
            "",
            title="CPU match",
            subtitle="How well vCPUs have to match requirements",
        )
        prefs_group.add(self.match_row)

        self.check_row = BindableComboRow(
            ["partial", "full"],
            "",
            title="CPU match checking",
            subtitle="If libvirt checks how vCPUs match requirements (if at all)",
        )
        prefs_group.add(self.check_row)

        self.topology_row = Adw.ExpanderRow(
            title="Explicit CPU topology", show_enable_switch=True
        )
        self.topology_row.connect("notify::enable-expansion", self.onTopologyEnabled)

        self.sockets_row = BindableSpinRow(
            lambda i: str(int(i)),
            title="CPU sockets",
            digits=0,
            adjustment=Gtk.Adjustment(step_increment=1),
        )
        self.topology_row.add_row(self.sockets_row.getWidget())
        self.cores_row = BindableSpinRow(
            lambda i: str(int(i)),
            title="CPU cores",
            digits=0,
            adjustment=Gtk.Adjustment(step_increment=1),
        )
        self.topology_row.add_row(self.cores_row.getWidget())
        self.threads_row = BindableSpinRow(
            lambda i: str(int(i)),
            title="CPU threads",
            numeric=True,
            digits=0,
            adjustment=Gtk.Adjustment(step_increment=1),
        )
        self.topology_row.add_row(self.threads_row.getWidget())

        prefs_group.add(self.topology_row)

        self.updateData()

    def updateData(self):
        # Bind vcpus
        def setVCPUsRange(m):
            self.vcpus_row.getWidget().set_range(1, m)
            self.vcpus_row.bindText(self.xml_tree.find("vcpu"), self.showApply)
            self.vcpus_row.spin_row.set_sensitive(True)

        asyncJob(self.parent.domain.connection.maxVCPUs, [], setVCPUsRange)

        mem = self.xml_tree.find("memory")
        self.memory_row.bindText(
            mem,
            self.onMemoryChanged,
            lambda t: str(stringToBytes(t, "KiB")),
            lambda t: bytesToString(t, "KiB"),
        )

        cpu = self.xml_tree.find("cpu")
        if cpu is None:
            cpu = ET.SubElement(self.xml_tree, "cpu")

        self.config_row.bindAttr(cpu, "mode", self.onCPUConfChanged)
        self.match_row.bindAttr(cpu, "match", self.showApply)
        self.check_row.bindAttr(cpu, "check", self.showApply)

        self.updateModelRow()
        self.updateTopology()

    def updateModelRow(self):
        cpu = self.xml_tree.find("cpu")
        config = self.config_row.get_model().get_string(self.config_row.get_selected())
        model = cpu.find("model")
        if config == "custom":
            if model is None:
                model = ET.SubElement(cpu, "model")
            self.cpu_model_row.bindText(model, self.showApply)
            self.cpu_model_row.set_visible(True)
        else:
            if model is not None:
                cpu.remove(model)
            self.cpu_model_row.unbind()
            self.cpu_model_row.set_visible(False)

    def onCPUConfChanged(self, *args):
        self.updateModelRow()
        self.showApply()

    def onMemoryChanged(self):
        # Remove these two attributes the prevent any weird outcomes.
        max_mem = self.xml_tree.find("maxMemory")
        if max_mem is not None:
            self.xml_tree.remove(max_mem)
        cur_mem = self.xml_tree.find("currentMemory")
        if cur_mem is not None:
            self.xml_tree.remove(cur_mem)
        self.showApply()

    def updateTopology(self):
        self.topology_row.disconnect_by_func(self.onTopologyEnabled)
        cpu = self.xml_tree.find("cpu")
        topology = cpu.find("topology")

        def setVCPUsRange(m):
            self.sockets_row.getWidget().set_range(1, m)
            self.cores_row.getWidget().set_range(1, m)
            self.threads_row.getWidget().set_range(1, m)

            self.sockets_row.bindAttr(topology, "sockets", self.showApply)
            self.cores_row.bindAttr(topology, "cores", self.showApply)
            self.threads_row.bindAttr(topology, "threads", self.showApply)

            self.sockets_row.getWidget().set_sensitive(True)
            self.cores_row.getWidget().set_sensitive(True)
            self.threads_row.getWidget().set_sensitive(True)

        if topology is None:
            self.topology_row.set_enable_expansion(False)
        else:
            self.sockets_row.getWidget().set_sensitive(False)
            self.cores_row.getWidget().set_sensitive(False)
            self.threads_row.getWidget().set_sensitive(False)
            asyncJob(self.parent.domain.connection.maxVCPUs, [], setVCPUsRange)

            self.topology_row.set_enable_expansion(True)

        self.topology_row.connect("notify::enable-expansion", self.onTopologyEnabled)

    def onTopologyEnabled(self, *args):
        cpu = self.xml_tree.find("cpu")
        topology = cpu.find("topology")
        if self.topology_row.get_enable_expansion():
            if topology is None:
                topology = ET.SubElement(cpu, "topology")
        else:
            if topology is not None:
                cpu.remove(topology)
        self.updateTopology()
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "Hardware"

    def getDescription(self) -> str:
        return "Common hardware settings"

    def getIconName(self) -> str:
        return "processor-symbolic"
