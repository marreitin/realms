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
from realms.ui.builders.bindable_entries import BindableComboRow, BindableSpinRow
from realms.ui.builders.domain.address_row import AddressRow

from .base_device_page import BaseDevicePage


class SoundPage(BaseDevicePage):
    def build(self):
        self.domain_caps = self.parent.domain.connection.getDomainCapabilities()

        self.group = Adw.PreferencesGroup()
        self.prefs_page.add(self.group)

        self.model_row = BindableComboRow(
            [
                "sb16",
                "es1370",
                "pcsbk",
                "ac97",
                "ich6",
                "ich9",
                "usb",
                "ich7",
                "virtio",
            ],
            title="Sound device model",
        )
        self.group.add(self.model_row)

        self.codec_row = BindableComboRow(
            ["", "duplex", "micro", "output"], title="Codec"
        )
        self.group.add(self.codec_row)

        self.audio_row = BindableSpinRow(
            lambda i: str(int(i)),
            title="Audio backend ID",
            subtitle="0 if unspecified",
            adjustment=Gtk.Adjustment(lower=0, step_increment=1, upper=32),
        )
        self.group.add(self.audio_row.spin_row)

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

        self.model_row.bindAttr(self.xml_tree, "model", self.onModelChanged)

        codec = self.xml_tree.find("codec")
        if codec is None:
            codec = ET.Element("coded")
        self.codec_row.bindAttr(codec, "type", self.onCodecChanged)
        if self.model_row.getSelectedString() in ["ich6", "ich9"]:
            self.codec_row.set_visible(True)
        else:
            self.codec_row.set_visible(False)

        audio = self.xml_tree.find("audio")
        if audio is None:
            audio = ET.Element("audio", attrib={"id": "0"})
        self.audio_row.bindAttr(audio, "id", self.onAudioChanged)

        self.address_row.setXML(self.xml_tree)

    def onModelChanged(self):
        if self.model_row.getSelectedString() in ["ich6", "ich9"]:
            self.codec_row.set_visible(True)
        else:
            self.codec_row.set_visible(False)
        self.showApply()

    def onCodecChanged(self):
        codec = self.xml_tree.find("codec")
        if self.codec_row.getSelectedString() == "":
            if codec is not None:
                self.xml_tree.remove(self.codec_row.elem)
        else:
            if codec is None:
                self.xml_tree.append(self.codec_row.elem)
        self.showApply()

    def onAudioChanged(self):
        audio = self.xml_tree.find("audio")
        if self.audio_row.getValue() == 0:
            if audio is not None:
                self.xml_tree.remove(self.audio_row.elem)
        else:
            if audio is None:
                self.xml_tree.append(self.audio_row.elem)
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return self.xml_tree.get("model", "") + " Sound Card"

    def getDescription(self) -> str:
        return "Sound card"

    def getIconName(self) -> str:
        return "soundcard-symbolic"
