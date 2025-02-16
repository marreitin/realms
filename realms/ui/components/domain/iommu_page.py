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

from realms.ui.components.bindable_entries import BindableComboRow, BindableEntryRow
from realms.ui.components.common import iconButton

from .base_device_page import BaseDevicePage


class IOMMUPage(BaseDevicePage):
    def build(self):
        self.group = Adw.PreferencesGroup()
        self.prefs_page.add(self.group)

        self.model_row = BindableComboRow(["intel", "smmuv3", "virtio"], title="Model")
        self.group.add(self.model_row)

        self.intremap_row = BindableComboRow(
            ["on", "off"], "", title="Interrupt remapping"
        )
        self.group.add(self.intremap_row)

        self.caching_mode_row = BindableComboRow(
            ["on", "off"], "", title="VT-d caching mode"
        )
        self.group.add(self.caching_mode_row)

        self.eim_row = BindableComboRow(
            ["on", "off"], "", title="Extended interrupt mode"
        )
        self.group.add(self.eim_row)

        self.iotlb_row = BindableComboRow(["on", "off"], "", title="IOTLB")
        self.group.add(self.iotlb_row)

        self.aw_bits_row = BindableEntryRow(title="IOVA address bits")
        self.group.add(self.aw_bits_row)

        self.dma_translation_row = BindableComboRow(
            ["on", "off"], "", title="DMA translation"
        )
        self.group.add(self.dma_translation_row)

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

        driver = self.xml_tree.find("driver")
        if driver is None:
            driver = ET.SubElement(self.xml_tree, "driver")

        self.intremap_row.bindAttr(driver, "intremap", self.showApply)
        self.caching_mode_row.bindAttr(driver, "caching_mode", self.showApply)
        self.eim_row.bindAttr(driver, "eim", self.showApply)
        self.iotlb_row.bindAttr(driver, "iotlb", self.showApply)
        self.aw_bits_row.bindAttr(driver, "aw_bits", self.showApply)
        self.dma_translation_row.bindAttr(driver, "dma_translation", self.showApply)

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "IOMMU"

    def getDescription(self) -> str:
        return "IO Memory Management Unit"

    def getIconName(self) -> str:
        return "memory-symbolic"
