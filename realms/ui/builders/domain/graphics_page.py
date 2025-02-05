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

from realms.ui.builders import iconButton, propertyRow
from realms.ui.builders.bindable_entries import (
    BindableComboRow,
    BindableDropDown,
    BindableEntry,
    BindableEntryRow,
    BindablePasswordRow,
    BindableSpinRow,
    BindableSwitchRow,
)

from .base_device_page import BaseDevicePage


class GLRow(Adw.ActionRow):
    def __init__(self):
        super().__init__(title="OpenGL support")

        self.xml_tree = None
        self.show_apply_cb = None

        self.rendernode = BindableEntry(
            hexpand=True,
            vexpand=False,
            valign=Gtk.Align.CENTER,
            tooltip_text="GL rendernode",
            placeholder_text="GL rendernode",
        )
        self.add_suffix(self.rendernode)

        self.enable_switch = Gtk.Switch(
            vexpand=False, valign=Gtk.Align.CENTER, tooltip_text="Enable GL support"
        )
        self.add_suffix(self.enable_switch)

        self.enable_switch.connect("notify::active", self.onEnableChanged)

    def bind(self, xml_tree: ET.Element, show_apply_cb: callable):
        self.xml_tree = None

        gl = xml_tree.find("gl")
        if gl is not None:
            self.enable_switch.set_active(gl.get("enable", "yes") == "yes")
        else:
            self.enable_switch.set_active(False)

        self.xml_tree = xml_tree
        self.show_apply_cb = show_apply_cb

        self.updateBind()

    def updateBind(self):
        gl = self.xml_tree.find("gl")
        if gl is not None:
            enabled = gl.get("enable", "yes") == "yes"
            if enabled:
                self.rendernode.set_visible(True)
                self.rendernode.bindAttr(gl, "rendernode", self.show_apply_cb)
            else:
                self.rendernode.set_visible(False)
                self.rendernode.unbind()

    def onEnableChanged(self, switch, *args):
        if self.xml_tree is None:
            return
        gl = self.xml_tree.find("gl")
        if gl is None:
            gl = ET.SubElement(self.xml_tree, "gl", attrib={"enable": "yes"})
        gl.set("enable", "yes" if self.enable_switch.get_active() else "no")
        self.updateBind()
        self.show_apply_cb()


class ListenRow(Adw.ExpanderRow):
    def __init__(self, window: Adw.ApplicationWindow):
        super().__init__(title="Listen type")

        self.xml_tree = None
        self.show_apply_cb = None

        self.type_combo = BindableDropDown(
            ["none", "address", "network"],
            vexpand=False,
            valign=Gtk.Align.CENTER,
        )
        self.add_suffix(self.type_combo)

        self.address_row = BindableEntryRow(title="Address")
        self.add_row(self.address_row)

        self.network_row = BindableEntryRow(title="Network")
        self.add_row(self.network_row)

        self.address_prop_row = propertyRow("Address", window)
        self.add_row(self.address_prop_row)

        self.socket_row = BindableEntryRow(title="Socket address")
        self.add_row(self.socket_row)

    def bind(self, xml_tree: ET.Element, show_apply_cb: callable):
        self.xml_tree = xml_tree

        if xml_tree.get("type") in ["spice", "vnc"]:
            self.type_combo.setSelection(["none", "address", "network", "socket"])
        else:
            self.type_combo.setSelection(["none", "address", "network"])

        listen = xml_tree.find("listen")
        if listen is None:
            listen = ET.SubElement(self.xml_tree, "listen")
        self.type_combo.bindAttr(listen, "type", self.onTypeChanged)

        self.xml_tree = xml_tree
        self.show_apply_cb = show_apply_cb

        self.updateData()

    def updateData(self):
        self.set_expanded(True)
        t = self.type_combo.getSelectedString()

        self.address_row.set_visible(False)
        self.address_row.unbind()
        self.network_row.set_visible(False)
        self.network_row.unbind()
        self.address_prop_row.set_visible(False)
        self.socket_row.set_visible(False)
        self.socket_row.unbind()

        listen = self.xml_tree.find("listen")

        if t == "address":
            self.address_row.set_visible(True)
            self.address_row.bindAttr(listen, "address", self.show_apply_cb)
        elif t == "network":
            self.network_row.set_visible(True)
            self.network_row.bindAttr(listen, "network", self.show_apply_cb)
            self.address_prop_row.set_visible(True)
            self.address_prop_row.set_subtitle(listen.get("address", ""))
        elif t == "socket":
            self.socket_row.set_visible(True)
            self.socket_row.bindAttr(listen, "socket", self.show_apply_cb)
        elif t == "none":
            pass

    def onTypeChanged(self):
        if self.xml_tree is None:
            return
        self.updateData()
        self.show_apply_cb()


class GraphicsPage(BaseDevicePage):
    rows_per_type = {
        "sdl": [],  # Unsupported
        "vnc": [
            "autoport",
            "port",
            "passwd",
            "keymap",
            "sharePolicy",
            "audio",
            "listen",
        ],
        "spice": [
            "autoport",
            "port",
            "tlsPort",
            "passwd",
            "keymap",
            "clipboard",
            "mouse",
            "filetransfer",
            "gl",
            "listen",
        ],
        "rdp": ["autoport", "port", "multiUser", "replaceUser", "listen"],
        "desktop": ["display", "fullscreen"],
        "egl-headless": ["gl"],
        "dbus": ["p2p", "address", "gl", "audio"],
    }

    def __init__(
        self, parent, xml_tree: ET.Element, use_for_adding=False, can_update=False
    ):
        super().__init__(parent, xml_tree, use_for_adding, can_update)

        self.rows = {}

    def build(self):
        self.group = Adw.PreferencesGroup(
            title=self.getTitle(),
            description="Graphical framebuffer",
        )
        self.prefs_page.add(self.group)

        self.domain_caps = self.parent.domain.connection.getDomainCapabilities()

        self.type_row = BindableComboRow(
            self.domain_caps.devices["graphics"]["type"],
            title="Graphics type",
        )
        self.group.add(self.type_row)

        self.rows["display"] = BindableEntryRow(title="Display")
        self.group.add(self.rows["display"])

        self.rows["fullscreen"] = BindableComboRow(["yes", "no"], title="Fullscreen")
        self.group.add(self.rows["fullscreen"])

        self.rows["gl"] = GLRow()
        self.group.add(self.rows["gl"])

        self.rows["autoport"] = BindableSwitchRow(
            "yes", "no", title="Automatically choose port"
        )
        self.group.add(self.rows["autoport"].switch_row)

        self.rows["port"] = BindableSpinRow(
            lambda x: str(int(x)),
            title="TCP port",
            unset_val=-1,
            adjustment=Gtk.Adjustment(lower=-1, step_increment=1, upper=65535),
        )
        self.group.add(self.rows["port"].getWidget())

        self.rows["tlsPort"] = BindableSpinRow(
            lambda x: str(int(x)),
            title="TLS port",
            unset_val=-1,
            adjustment=Gtk.Adjustment(lower=-1, step_increment=1, upper=65535),
        )
        self.group.add(self.rows["tlsPort"].getWidget())

        if hasattr(self.parent, "window_ref"):
            self.rows["listen"] = ListenRow(self.parent.window_ref.window)
        else:
            self.rows["listen"] = ListenRow(self.parent.window)
        self.group.add(self.rows["listen"])

        self.rows["passwd"] = BindablePasswordRow(title="Connection password")
        self.group.add(self.rows["passwd"].widget)

        self.rows["keymap"] = BindableEntryRow(title="Keymap")
        self.group.add(self.rows["keymap"])

        self.rows["sharePolicy"] = BindableComboRow(
            ["allow-exclusive", "force-shared", "ignore"], title="Share policy"
        )
        self.group.add(self.rows["sharePolicy"])

        self.rows["audio"] = BindableEntryRow(title="Audio device ID mapping")
        self.group.add(self.rows["audio"])

        self.rows["clipboard"] = BindableSwitchRow(
            "yes", "no", True, title="Allow Copy/Paste"
        )
        self.group.add(self.rows["clipboard"].switch_row)

        self.rows["mouse"] = BindableComboRow(["client", "server"], title="Mouse mode")
        self.group.add(self.rows["mouse"])

        self.rows["filetransfer"] = BindableSwitchRow(
            "yes", "no", True, title="Allow file transfer"
        )
        self.group.add(self.rows["filetransfer"].switch_row)

        self.rows["multiUser"] = BindableSwitchRow(
            "yes", "no", title="Allow simultanious connections"
        )
        self.group.add(self.rows["multiUser"].switch_row)

        self.rows["replaceUser"] = BindableSwitchRow(
            "yes",
            "no",
            title="Replace user",
            subtitle="Drop connection when new user connects",
        )
        self.group.add(self.rows["replaceUser"].switch_row)

        self.rows["p2p"] = BindableSwitchRow(
            "on", "off", title="Enable peer-to-peer connections"
        )
        self.group.add(self.rows["p2p"].switch_row)

        self.rows["address"] = BindableEntryRow(title="DBus address")
        self.group.add(self.rows["address"])

        if not self.use_for_adding:
            delete_row = Adw.ActionRow()
            self.group.add(delete_row)
            self.delete_btn = iconButton(
                "Remove", "user-trash-symbolic", self.deleteDevice, css_classes=["flat"]
            )
            delete_row.add_prefix(self.delete_btn)

        self.updateData()

    def updateData(self):
        for row in self.rows.values():
            row.set_visible(False)

        self.group.set_title(self.getTitle())
        self.type_row.bindAttr(self.xml_tree, "type", self.onTypeChanged)

        t = self.type_row.getSelectedString()

        for row_name in self.rows_per_type[t]:
            self.rows[row_name].set_visible(True)
            row = self.rows[row_name]
            if row_name in [
                "display",
                "fullscreen",
                "port",
                "autoport",
                "passwd",
                "keymap",
                "sharePolicy",
                "tlsPort",
                "multiUser",
                "replaceUser",
                "p2p",
                "address",
            ]:
                row.bindAttr(self.xml_tree, row_name, self.showApply)
            elif row_name in ["streaming", "clipboard", "mouse", "filetransfer"]:
                elem = self.xml_tree.find(row_name)
                attr_names = {
                    "clipboard": "copypaste",
                    "mouse": "mode",
                    "filetransfer": "enable",
                }
                if elem is None:
                    elem = ET.SubElement(self.xml_tree, row_name)
                row.bindAttr(elem, attr_names[row_name], self.showApply)
            elif row_name == "audio":
                audio = self.xml_tree.find("audio")
                if audio is None:
                    audio = ET.Element("audio")
                row.bindAttr(audio, "id", self.onAudioChanged)
            elif row_name in ["gl", "listen"]:
                row.bind(self.xml_tree, self.showApply)

    def onTypeChanged(self):
        self.xml_tree.clear()
        self.xml_tree.set("type", self.type_row.getSelectedString())
        self.updateData()
        self.showApply()

    def onAudioChanged(self):
        row = self.rows["audio"]
        if row.get_text() == "":
            self.xml_tree.remove(row.elem)
        else:
            self.xml_tree.append(row.elem)
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return self.xml_tree.get("type", "").upper() + " graphics "

    def getDescription(self) -> str:
        return "Graphical framebuffer"

    def getIconName(self) -> str:
        return "waves-and-screen-symbolic"
