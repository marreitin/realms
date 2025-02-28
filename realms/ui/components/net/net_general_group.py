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
from realms.ui.components.bindable_entries import BindableComboRow, BindableEntryRow
from realms.ui.components.common import iconButton, propertyRow


class NetGeneralGroup(Adw.PreferencesGroup):
    """This part of the network settings group is a bit different,
    because it's reused in the AddNetworkDialog, and hence must be
    a bit more flexible.
    """

    network_forward_modes = [
        "none",
        "nat",
        "route",
        "open",
        "bridge",
        "private",
        "vepa",
        "passthrough",
        "hostdev",
    ]

    def __init__(
        self,
        allow_name_edit: bool,
        window: Adw.ApplicationWindow,
        show_apply_cb: callable,
        delete_cb: callable,
    ):
        super().__init__()

        self.allow_name_edit = allow_name_edit
        self.window = window
        self.show_apply_cb = show_apply_cb
        self.delete_cb = delete_cb

        self.xml_tree = None

        self.general_group = None
        self.name_row = None
        self.uuid_row = None
        self.title_row = None
        self.desc_row = None
        self.net_dns_name_row = None
        self.autostart_row = None
        self.forward_mode_row = None
        self.forward_device_row = None
        self.domain_row = None

        self.build()

    def build(self):
        if not self.allow_name_edit:
            self.name_row = propertyRow("Name")
            self.add(self.name_row)

            self.uuid_row = propertyRow("UUID")
            self.add(self.uuid_row)
        else:
            self.name_row = BindableEntryRow(title="Name")
            self.add(self.name_row)

        self.title_row = BindableEntryRow(title="Title")
        self.add(self.title_row)

        self.desc_row = BindableEntryRow(title="Description")
        self.add(self.desc_row)

        self.autostart_row = Adw.SwitchRow(
            title="Autostart", subtitle="Start network on boot"
        )
        self.autostart_row.set_active(True)
        self.autostart_row.connect("notify::active", self.show_apply_cb)
        self.add(self.autostart_row)

        self.forward_mode_row = BindableComboRow(
            self.network_forward_modes, title="Network forward mode"
        )
        self.add(self.forward_mode_row)

        self.forward_device_row = BindableEntryRow(title="Network forward device")
        self.add(self.forward_device_row)

        self.bridge_row = BindableEntryRow(
            title="Network bridge",
            tooltip_text="Bridge name for this network will be generated if omitted",
        )
        self.add(self.bridge_row)

        self.domain_row = BindableEntryRow(title="DHCP Domain")
        self.add(self.domain_row)

        if self.delete_cb is not None:
            delete_row = Adw.ActionRow()
            self.add(delete_row)
            self.delete_btn = iconButton(
                "",
                "user-trash-symbolic",
                cb=self.delete_cb,
                css_classes=["destructive-action"],
            )
            delete_row.add_prefix(self.delete_btn)

    def updateData(self, xml_tree: ET.Element, autostart: bool):
        self.xml_tree = xml_tree

        name = self.xml_tree.find("name")
        uuid = self.xml_tree.find("uuid")
        if not self.allow_name_edit:
            self.name_row.set_subtitle(getETText(name))
            self.uuid_row.set_subtitle(getETText(uuid))
        else:
            if name is None:
                name = ET.SubElement(self.xml_tree, "name")
            self.name_row.bindText(name, self.show_apply_cb)
            self.set_title("")

        title = self.xml_tree.find("title")
        if title is None:
            title = ET.SubElement(self.xml_tree, "title")
        self.title_row.bindText(title, self.show_apply_cb)

        desc = self.xml_tree.find("description")
        if desc is None:
            desc = ET.SubElement(self.xml_tree, "description")
        self.desc_row.bindText(desc, self.show_apply_cb)

        self.autostart_row.set_active(autostart)

        forward = self.xml_tree.find("forward")
        if forward is None:
            forward = ET.SubElement(self.xml_tree, "forward", attrib={"mode": "none"})
        self.forward_mode_row.bindAttr(forward, "mode", self.onForwardModeChanged)
        self.forward_device_row.bindAttr(forward, "dev", self.show_apply_cb)

        bridge = self.xml_tree.find("bridge")
        if bridge is None:
            bridge = ET.Element("bridge")
        self.bridge_row.bindAttr(bridge, "name", self.onBridgeChanged)

        domain = self.xml_tree.find("domain")
        if domain is None:
            domain = ET.SubElement(self.xml_tree, "domain", attrib={"name": ""})

        self.domain_row.bindAttr(domain, "name", self.show_apply_cb)

        self.onForwardModeChanged()

    def onForwardModeChanged(self, *args):
        """Change visible rows depending on the newly selected forwarding mode."""
        selected = self.forward_mode_row.getSelectedString()
        forward = self.xml_tree.find("forward")

        if selected in ["nat", "route", "passthrough", "hostdev"]:
            self.forward_device_row.set_visible(True)
        else:
            self.forward_device_row.set_visible(False)
            if "dev" in forward.attrib:
                del forward.attrib["dev"]

        domain = self.xml_tree.find("domain")
        if selected in ["nat", "route", "private"]:
            if domain is None:
                domain = ET.SubElement(self.xml_tree, "domain", attrib={"name": ""})
            self.domain_row.set_visible(True)
            self.domain_row.bindAttr(domain, "name", self.show_apply_cb)
        else:
            if domain is not None:
                self.xml_tree.remove(domain)
            self.domain_row.set_visible(False)
            self.domain_row.unbind()

        bridge = self.xml_tree.find("bridge")
        if selected not in ["none", "private", "vepa"]:
            if bridge is None:
                bridge = ET.SubElement(self.xml_tree, "bridge", attrib={"name": ""})
            self.bridge_row.set_visible(True)
            self.bridge_row.bindAttr(bridge, "name", self.show_apply_cb)
        else:
            if bridge is not None:
                self.xml_tree.remove(bridge)
            self.bridge_row.set_visible(False)
            self.bridge_row.unbind()

        self.show_apply_cb()

    def onBridgeChanged(self):
        bridge = self.xml_tree.find("bridge")
        if self.bridge_row.get_text() == "":
            if bridge is not None:
                self.xml_tree.remove(bridge)
        else:
            if bridge is None:
                self.xml_tree.append(self.bridge_row.elem)
        self.show_apply_cb()

    def getAutostart(self) -> bool:
        return self.autostart_row.get_active()
