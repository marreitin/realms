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
)

from .base_device_page import BaseDevicePage


class IORow:
    def __init__(self, t: type, **kwargs):
        in_kwargs = kwargs.copy()
        out_kwargs = kwargs.copy()
        if "title" in kwargs:
            in_kwargs["title"] += " (In)"
            out_kwargs["title"] += " (Out)"
        self.in_row = t(**in_kwargs)
        self.out_row = t(**out_kwargs)

    def unbind(self):
        self.in_row.unbind()
        self.out_row.unbind()

    def getInRowWidget(self):
        return self.in_row.getWidget()

    def getOutRowWidget(self):
        return self.out_row.getWidget()

    def bind(self, xml_tree: ET.Element, attr: str, show_apply_cb: callable):
        input_elem = xml_tree.find("input")
        if input_elem is None:
            input_elem = ET.SubElement(xml_tree, "input")

        output_elem = xml_tree.find("output")
        if output_elem is None:
            output_elem = ET.SubElement(xml_tree, "output")

        self.in_row.bindAttr(input_elem, attr, show_apply_cb)
        self.out_row.bindAttr(input_elem, attr, show_apply_cb)


class AudioPage(BaseDevicePage):
    """Page for host-side audio connection."""

    io_rows_per_type = {
        "none": [],
        "alsa": ["dev"],
        "coreaudio": ["bufferCount"],
        "dbus": [],
        "jack": ["serverName", "clientName", "connectPorts", "exactName"],
        "oss": ["dev", "bufferCount", "tryPoll"],
        "pipewire": ["name", "streamName", "latency"],
        "pulseaudio": ["name", "streamName", "latency"],
        "sdl": ["bufferCount"],
        "spice": [],
        "file": [],
    }

    rows_per_type = {
        "none": [],
        "alsa": [],
        "coreaudio": [],
        "dbus": [],
        "jack": [],
        "oss": [],
        "pipewire": [],
        "pulseaudio": ["serverName"],
        "sdl": ["driver"],
        "spice": [],
        "file": ["path"],
    }

    def __init__(
        self, parent, xml_tree: ET.Element, use_for_adding=False, can_update=False
    ):
        super().__init__(parent, xml_tree, use_for_adding, can_update)

        self.rows = {}
        self.io_rows = {}

    def build(self):
        """Build self."""
        self.group = Adw.PreferencesGroup()
        self.prefs_page.add(self.group)

        self.type_row = BindableComboRow(
            [
                "none",
                "alsa",
                "coreaudio",
                "dbus",
                "jack",
                "oss",
                "pipewire",
                "pulseaudio",
                "sdl",
                "spice",
                "file",
            ],
            title="Audio backend type",
        )
        self.group.add(self.type_row)

        self.id_row = BindableSpinRow(
            lambda i: str(int(i)),
            title="Audio backend ID",
            adjustment=Gtk.Adjustment(lower=1, step_increment=1, upper=32),
        )
        self.group.add(self.id_row.spin_row)

        # Type dependent rows
        self.rows["serverName"] = BindableEntryRow(title="Server name")
        self.rows["driver"] = BindableComboRow(
            ["esd", "alsa", "arts", "pulseaudio"], title="SDL audio driver"
        )
        self.rows["path"] = BindableEntryRow(title="File name")

        for row in self.rows.values():
            self.group.add(row)

        # IO Rows
        self.io_rows["dev"] = IORow(BindableEntryRow, title="Device")

        self.io_rows["bufferCount"] = IORow(BindableEntryRow, title="Buffer count")
        self.io_rows["serverName"] = IORow(BindableEntryRow, title="Server name")
        self.io_rows["clientName"] = IORow(
            BindableEntryRow,
            title="Client name",
        )
        self.io_rows["connectPorts"] = IORow(BindableEntryRow, title="Connection ports")
        self.io_rows["exactName"] = IORow(
            BindableComboRow, selection=["yes", "no"], title="Force exact name"
        )
        self.io_rows["tryPoll"] = IORow(
            BindableComboRow,
            selection=["yes", "no"],
            title="Attempt to use polling mode",
        )
        self.io_rows["name"] = IORow(BindableEntryRow, title="Name")
        self.io_rows["streamName"] = IORow(BindableEntryRow, title="Stream name")
        self.io_rows["latency"] = IORow(
            BindableSpinRow,
            out_format=lambda i: str(int(i)),
            title="Latency (µs)",
            adjustment=Gtk.Adjustment(lower=0, step_increment=1, upper=10000),
            digits=0,
        )

        for row in self.io_rows.values():
            self.group.add(row.getInRowWidget())
            self.group.add(row.getOutRowWidget())

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

        self.type_row.bindAttr(self.xml_tree, "type", self.__onTypeChanged__)
        self.id_row.bindAttr(self.xml_tree, "id", self.__onTypeChanged__)

        for row in self.rows.values():
            row.unbind()
            row.getWidget().set_visible(False)

        if self.type_row.getSelectedString() in self.rows_per_type:
            for row_name in self.rows_per_type[self.type_row.getSelectedString()]:
                row = self.rows[row_name]
                row.bindAttr(self.xml_tree, row_name, self.showApply)
                row.set_visible(True)

        for row in self.io_rows.values():
            row.unbind()
            row.getInRowWidget().set_visible(False)
            row.getOutRowWidget().set_visible(False)

        if self.type_row.getSelectedString() in self.io_rows_per_type:
            for row_name in self.io_rows_per_type[self.type_row.getSelectedString()]:
                row = self.io_rows[row_name]
                row.getInRowWidget().set_visible(True)
                row.getOutRowWidget().set_visible(True)

                row.bind(self.xml_tree, row_name, self.showApply)

    def __onTypeChanged__(self):
        """The type of device was changed."""
        self.xml_tree.clear()
        self.xml_tree.set("type", self.type_row.getSelectedString())
        self.xml_tree.set("id", self.id_row.getValue())
        self.updateData()
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "Audio Backend"

    def getDescription(self) -> str:
        return "Host side audio backend"

    def getIconName(self) -> str:
        return "speaker-symbolic"
