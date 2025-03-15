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

from realms.helpers import bytesToString, stringToBytes
from realms.ui.components.bindable_entries import (
    BindableComboRow,
    BindableEntryRow,
    BindableSpinRow,
    BindableSwitchRow,
)
from realms.ui.components.common import deleteRow
from realms.ui.components.domain.address_row import AddressRow

from .base_device_page import BaseDevicePage


class ResolutionRow(Adw.ExpanderRow):
    def __init__(self, show_apply_cb: callable, **kwargs):
        super().__init__(title="Default Resolution", show_enable_switch=True, **kwargs)

        self.show_apply_cb = show_apply_cb
        self.model_xml = None

        self.x_row = BindableSpinRow(
            lambda i: str(int(i)),
            title="Width",
            value=1,
            adjustment=Gtk.Adjustment(lower=0, step_increment=360, upper=36000),
        )
        self.add_row(self.x_row.spin_row)
        self.y_row = BindableSpinRow(
            lambda i: str(int(i)),
            title="Height",
            value=1,
            adjustment=Gtk.Adjustment(lower=0, step_increment=360, upper=36000),
        )
        self.add_row(self.y_row.spin_row)

        self.connect("notify::enable-expansion", self.onSwitchChanged)

    def onSwitchChanged(self, *args):
        res = self.model_xml.find("resolution")
        if self.get_enable_expansion():
            if res is None:
                res = ET.SubElement(
                    self.model_xml, "resolution", attrib={"x": "0", "y": "0"}
                )
            self.x_row.bindAttr(res, "x", self.show_apply_cb)
            self.y_row.bindAttr(res, "y", self.show_apply_cb)
        else:
            if res is not None:
                self.model_xml.remove(res)
            self.x_row.unbind()
            self.y_row.unbind()
        self.show_apply_cb()

    def setXML(self, model_xml: ET.Element):
        self.model_xml = model_xml
        res = self.model_xml.find("resolution")

        self.disconnect_by_func(self.onSwitchChanged)

        if res is None:
            self.set_enable_expansion(False)
            self.x_row.unbind()
            self.y_row.unbind()
        else:
            self.set_enable_expansion(True)
            self.x_row.bindAttr(res, "x", self.show_apply_cb)
            self.y_row.bindAttr(res, "y", self.show_apply_cb)
        self.connect("notify::enable-expansion", self.onSwitchChanged)


class VideoPage(BaseDevicePage):
    def build(self):
        self.group = Adw.PreferencesGroup()
        self.prefs_page.add(self.group)

        self.domain_caps = self.parent.domain.connection.getDomainCapabilities()

        self.model_row = BindableComboRow(
            self.domain_caps.devices["video"]["modelType"], title="Model"
        )
        self.group.add(self.model_row)

        self.vram_row = BindableEntryRow(title="VRam")
        self.group.add(self.vram_row)

        self.heads_row = BindableSpinRow(
            lambda i: str(int(i)),
            title="Heads",
            value=1,
            adjustment=Gtk.Adjustment(lower=1, step_increment=1, upper=32),
        )
        self.group.add(self.heads_row.spin_row)

        self.accel_row = BindableSwitchRow("yes", "no", title="OpenGL Support")
        self.group.add(self.accel_row.switch_row)

        self.res_row = ResolutionRow(self.showApply)
        self.group.add(self.res_row)

        self.address_row = AddressRow(self.xml_tree, self.showApply, ["pci"])
        self.group.add(self.address_row)

        if not self.use_for_adding:
            self.group.add(deleteRow(self.deleteDevice))

        self.updateData()

    def updateData(self):
        self.group.set_title(self.getTitle())
        self.group.set_description(self.getDescription())
        model = self.xml_tree.find("model")
        if model is None:
            model = ET.SubElement(self.xml_tree, "model")

        self.model_row.bindAttr(model, "type", self.onModelChanged)
        self.vram_row.bindAttr(
            model,
            "vram",
            self.showApply,
            lambda t: str(stringToBytes(t, "KiB")),
            lambda t: bytesToString(t, "KiB"),
        )
        self.heads_row.bindAttr(model, "heads", self.showApply)
        if model.get("type") in ["vga", "qxl", "bochs", "gop", "virtio"]:
            self.res_row.set_visible(True)
        else:
            self.res_row.set_visible(False)
        self.res_row.setXML(model)

        accel = model.find("acceleration")
        if accel is None:
            accel = ET.Element("acceleration")
        self.accel_row.bindAttr(accel, "accel3d", self.onAccelChanged)

        self.address_row.setXML(self.xml_tree)

    def onModelChanged(self, *args):
        self.xml_tree.clear()
        model = ET.SubElement(self.xml_tree, "model")
        model.set("type", self.model_row.getSelectedString())
        self.updateData()
        self.showApply()

    def onAccelChanged(self, *args):
        model = self.xml_tree.find("model")
        if self.accel_row.switch_row.get_active():
            model.append(self.accel_row.elem)
        else:
            model.remove(self.accel_row.elem)
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return self.xml_tree.find("model").get("type") + " Video"

    def getDescription(self) -> str:
        return "Virtual display adapter"

    def getIconName(self) -> str:
        return "brush-monitor-symbolic"
