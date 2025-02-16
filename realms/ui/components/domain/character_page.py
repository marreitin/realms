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

from realms.ui.components import iconButton
from realms.ui.components.bindable_entries import (
    BindableComboRow,
    BindableEntryRow,
    BindableSpinRow,
    BindableSwitchRow,
)
from realms.ui.components.domain.address_row import AddressRow

from .base_device_page import BaseDevicePage


class CharacterPage(BaseDevicePage):
    """Page for character devices."""

    def __init__(
        self, parent, xml_tree: ET.Element, use_for_adding=False, can_update=False
    ):
        super().__init__(parent, xml_tree, use_for_adding, can_update)

        self.rows = []

    def build(self):
        self.group = Adw.PreferencesGroup()
        self.prefs_page.add(self.group)

        self.log_file_row = BindableEntryRow(title="Log file path")
        self.group.add(self.log_file_row)

        self.log_file_append_row = BindableSwitchRow(
            "on", "off", False, title="Append to log file"
        )
        self.group.add(self.log_file_append_row.getWidget())

        self.address_row = AddressRow(self.xml_tree, self.showApply)
        self.group.add(self.address_row)

        if not self.use_for_adding:
            delete_row = Adw.ActionRow()
            self.group.add(delete_row)
            self.delete_btn = iconButton(
                "Remove", "user-trash-symbolic", self.deleteDevice, css_classes=["flat"]
            )
            delete_row.add_prefix(self.delete_btn)

        # Client stuff
        self.client_group = Adw.PreferencesGroup(title="Client side")
        self.prefs_page.add(self.client_group)

        self.device_type_row = BindableComboRow(
            ["channel", "console", "parallel", "serial"], title="Device type"
        )
        self.client_group.add(self.device_type_row)

        self.channel_type_row = BindableComboRow(
            ["guestfwd", "virtio", "xen", "spicevmc", "qemu-vdagent"],
            title="Channel type",
        )
        self.client_group.add(self.channel_type_row)
        self.rows.append(self.channel_type_row)

        # I have no idea what the maximum index is.
        self.target_port_row = BindableSpinRow(
            lambda x: str(int(x)),
            title="Target port",
            adjustment=Gtk.Adjustment(lower=0, step_increment=1, upper=8),
        )
        self.client_group.add(self.target_port_row.getWidget())
        self.rows.append(self.target_port_row)

        self.serial_target_type_row = BindableComboRow(
            [
                "isa-serial",
                "usb-serial",
                "pci-serial",
                "spapr-vio-serial",
                "system-serial",
                "sclp-serial",
                "isa-debug",
            ],
            "",
            title="Target type",
        )
        self.client_group.add(self.serial_target_type_row)
        self.rows.append(self.serial_target_type_row)

        self.console_target_type_row = BindableComboRow(
            [
                "serial",
                "virtio",
                "xen",
                "lxc",
                "openvz",
                "sclp",
                "sclplm",
                "sclpconsole",
                "clcplmconsole",
            ],
            "",
            title="Target type",
        )
        self.client_group.add(self.console_target_type_row)
        self.rows.append(self.console_target_type_row)

        self.target_model_row = BindableComboRow(
            [
                "isa-serial",
                "usb-serial",
                "pci-serial",
                "spapr-vty",
                "pl011",
                "16550a",
                "sclpconsole",
                "sclplmconsole",
                "isa-debugcon",
            ],
            "",
            title="Target model",
        )
        self.client_group.add(self.target_model_row)
        self.rows.append(self.target_model_row)

        self.channel_address_row = BindableEntryRow(title="Channel target IP address")
        self.client_group.add(self.channel_address_row)
        self.rows.append(self.channel_address_row)

        self.channel_port_row = BindableSpinRow(
            lambda x: str(int(x)),
            title="Channel target port",
            adjustment=Gtk.Adjustment(lower=1, step_increment=1, upper=65536),
        )
        self.client_group.add(self.channel_port_row.getWidget())
        self.rows.append(self.channel_port_row)

        self.channel_name_row = BindableEntryRow(title="Channel name")
        self.client_group.add(self.channel_name_row.getWidget())
        self.rows.append(self.channel_name_row)

        # Host stuff
        self.host_group = Adw.PreferencesGroup(title="Host side")
        self.prefs_page.add(self.host_group)

        self.host_type_row = BindableComboRow(
            [
                "stdio",
                "file",
                "vc",
                "null",
                "pty",
                "dev",
                "pipe",
                "tcp",
                "udp",
                "unix",
                "spiceport",
            ],
            title="Host interface type",
        )
        self.host_group.add(self.host_type_row)

        self.source_path_row = BindableEntryRow(title="Source path")
        self.host_group.add(self.source_path_row)
        self.rows.append(self.source_path_row)

        self.source_mode_row = BindableComboRow(
            [
                "connect",
                "bind",
            ],
            title="Source mode",
        )
        self.host_group.add(self.source_mode_row)
        self.rows.append(self.source_mode_row)

        self.source_host_row = BindableEntryRow(title="Source host IP")
        self.host_group.add(self.source_host_row)
        self.rows.append(self.source_host_row)

        self.source_service_row = BindableSpinRow(
            lambda x: str(int(x)),
            title="Source service",
            adjustment=Gtk.Adjustment(lower=1, step_increment=1, upper=65536),
        )
        self.host_group.add(self.source_service_row.getWidget())
        self.rows.append(self.source_service_row)

        self.source_protocol_row = BindableComboRow(
            ["raw", "telnet"], title="Source protocol"
        )
        self.host_group.add(self.source_protocol_row)
        self.rows.append(self.source_protocol_row)

        self.source_channel_row = BindableEntryRow(title="Source channel name")
        self.host_group.add(self.source_channel_row)
        self.rows.append(self.source_channel_row)

        self.updateData()

    def updateData(self):
        self.group.set_title(self.getTitle())

        log = self.xml_tree.find("log")
        if log is None:
            log = ET.Element("log")
            self.log_file_append_row.set_visible(False)
        else:
            self.log_file_append_row.set_visible(True)
        self.log_file_row.bindAttr(log, "file", self.__onLogFileChanged__)
        self.log_file_append_row.bindAttr(log, "append", self.showApply)

        tag = self.xml_tree.tag
        self.device_type_row.bindAttr(
            ET.Element("tag", attrib={"tag": tag}), "tag", self.__onTagChanged__
        )

        # Hide all rows
        for row in self.rows:
            row.set_visible(False)

        # Client rows
        target = self.xml_tree.find("target")
        if target is None:
            target = ET.SubElement(self.xml_tree, "target")

        if tag == "parallel":
            self.target_port_row.set_visible(True)
            self.target_port_row.bindAttr(target, "port", self.showApply)
        elif tag == "serial":
            self.target_port_row.set_visible(True)
            self.target_port_row.bindAttr(target, "port", self.showApply)

            self.serial_target_type_row.set_visible(True)
            self.serial_target_type_row.bindAttr(target, "type", self.showApply)

            model = target.find("model")
            if model is None:
                model = ET.Element("model")
            self.target_model_row.set_visible(True)
            self.target_model_row.bindAttr(model, "name", self.__onTargetModelChanged__)
        elif tag == "console":
            self.target_port_row.set_visible(True)
            self.target_port_row.bindAttr(target, "port", self.showApply)

            self.console_target_type_row.set_visible(True)
        elif tag == "channel":
            self.channel_type_row.set_visible(True)
            self.channel_type_row.bindAttr(
                target, "type", self.__onChannelTypeChanged__
            )
            self.__refreshChannelType__()
        else:
            raise NotImplementedError

        # Host rows
        self.host_type_row.bindAttr(self.xml_tree, "type", self.__onHostTypeChanged__)
        self.__refreshHostType__()

    def __onTagChanged__(self):
        tag = self.device_type_row.getSelectedString()
        self.xml_tree.clear()
        self.xml_tree.tag = tag
        self.updateData()
        self.showApply()

    def __refreshChannelType__(self):
        target = self.xml_tree.find("target")

        self.channel_address_row.set_visible(False)
        self.channel_port_row.set_visible(False)
        self.channel_name_row.set_visible(False)

        channel_type = self.channel_type_row.getSelectedString()
        if channel_type == "guestfwd":
            self.channel_address_row.set_visible(True)
            self.channel_address_row.bindAttr(target, "address", self.showApply)
            self.channel_port_row.set_visible(True)
            self.channel_port_row.bindAttr(target, "port", self.showApply)
        elif channel_type == "virtio":
            self.channel_name_row.set_visible(True)
            self.channel_name_row.bindAttr(target, "name", self.showApply)

    def __onChannelTypeChanged__(self):
        self.__refreshChannelType__()
        self.showApply()

    def __refreshHostType__(self):
        host_type = self.host_type_row.getSelectedString()

        source = self.xml_tree.find("source")
        if source is None:
            source = ET.SubElement(self.xml_tree, "source")

        if host_type == "stdio":
            pass
        elif host_type == "file":
            self.source_path_row.set_visible(True)
            self.source_path_row.bindAttr(source, "path", self.showApply)
        elif host_type == "vc":
            pass
        elif host_type == "null":
            pass
        elif host_type == "pty":
            self.source_path_row.set_visible(True)
            self.source_path_row.bindAttr(source, "path", self.showApply)
        elif host_type == "dev":
            self.source_path_row.set_visible(True)
            self.source_path_row.bindAttr(source, "path", self.showApply)
        elif host_type == "pipe":
            self.source_path_row.set_visible(True)
            self.source_path_row.bindAttr(source, "path", self.showApply)
        elif host_type == "tcp":
            self.source_mode_row.set_visible(True)
            self.source_mode_row.bindAttr(source, "mode", self.showApply)

            self.source_host_row.set_visible(True)
            self.source_host_row.bindAttr(source, "host", self.showApply)

            self.source_service_row.set_visible(True)
            self.source_service_row.bindAttr(source, "service", self.showApply)

            protocol = source.find("protocol")
            if protocol is None:
                protocol = ET.SubElement(source, "protocol")

            self.source_protocol_row.set_visible(True)
            self.source_protocol_row.bindAttr(protocol, "type", self.showApply)
        elif host_type == "udp":
            self.source_mode_row.set_visible(True)
            self.source_mode_row.bindAttr(source, "mode", self.showApply)

            self.source_host_row.set_visible(True)
            self.source_host_row.bindAttr(source, "host", self.showApply)

            self.source_service_row.set_visible(True)
            self.source_service_row.bindAttr(source, "service", self.showApply)
        elif host_type == "unix":
            self.source_mode_row.set_visible(True)
            self.source_mode_row.bindAttr(source, "mode", self.showApply)

            self.source_path_row.set_visible(True)
            self.source_path_row.bindAttr(source, "path", self.showApply)
        elif host_type == "spiceport":
            self.source_channel_row.set_visible(True)
            self.source_channel_row.bindAttr(source, "channel", self.showApply)

    def __onHostTypeChanged__(self):
        source = self.xml_tree.find("source")
        source.clear()
        self.updateData()
        self.showApply()

    def __onLogFileChanged__(self):
        file = self.log_file_row.getWidget().get_text()
        log = self.xml_tree.find("log")
        if file == "":
            if log is not None:
                self.xml_tree.remove(log)
            self.log_file_append_row.set_visible(False)
        else:
            if log is None:
                self.xml_tree.append(self.log_file_row.elem)
            self.log_file_append_row.set_visible(True)
        self.showApply()

    def __onTargetModelChanged__(self):
        m = self.target_model_row.getSelectedString()
        model = self.xml_tree.find("target").find("model")
        if m == "":
            if model is not None:
                self.xml_tree.find("target").remove(model)
        else:
            if model is None:
                self.xml_tree.find("target").append(self.target_model_row.elem)
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return self.xml_tree.tag.capitalize()

    def getDescription(self) -> str:
        return "Generic character device"

    def getIconName(self) -> str:
        if self.xml_tree.tag == "console":
            return "terminal-symbolic"
        return "horizontal-arrows-symbolic"
