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
    BindableEntryRow,
    BindablePasswordRow,
    BindableSpinRow,
    BindableSwitchRow,
)

from .base_device_page import BaseDevicePage


class GLRow(Adw.ExpanderRow):
    def __init__(self):
        super().__init__(title="OpenGL Support", show_enable_switch=True)

        self.xml_tree = None
        self.show_apply_cb = lambda: None

        self.rendernode_row = BindableEntryRow(
            tooltip_text="GL Rendernode",
            title="GL Rendernode",
        )
        self.add_row(self.rendernode_row)

        self.connect("notify::enable-expansion", self.__onEnableChanged__)

    def bind(self, xml_tree: ET.Element, show_apply_cb: callable):
        self.xml_tree = None

        gl = xml_tree.find("gl")
        if gl is not None:
            self.set_enable_expansion(gl.get("enable", "yes") == "yes")
        else:
            self.set_enable_expansion(False)

        self.xml_tree = xml_tree
        self.show_apply_cb = show_apply_cb

        self.__updateBind__()

    def __updateBind__(self):
        gl = self.xml_tree.find("gl")
        if gl is not None:
            enabled = gl.get("enable", "yes") == "yes"
            if enabled:
                self.rendernode_row.bindAttr(gl, "rendernode", self.show_apply_cb)
            else:
                self.rendernode_row.unbind()

    def __onEnableChanged__(self, switch, *_):
        if self.xml_tree is None:
            return
        gl = self.xml_tree.find("gl")
        if gl is None:
            gl = ET.SubElement(self.xml_tree, "gl", attrib={"enable": "yes"})

        if self.get_enable_expansion():
            gl.set("enable", "yes")

        else:
            gl.set("enable", "no")
            if "rendernode" in gl.attrib:
                del gl.attrib["rendernode"]
        self.__updateBind__()
        self.show_apply_cb()


class ListenRow(Adw.ExpanderRow):
    def __init__(self, window: Adw.ApplicationWindow):
        super().__init__(title="Listen Type")

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

        self.socket_row = BindableEntryRow(title="Socket Path")
        self.add_row(self.socket_row)

        self.autoport_row = BindableSwitchRow(
            "yes", "no", title="Automatically Choose Port"
        )
        self.add_row(self.autoport_row.getWidget())

        self.tcp_row = BindableSpinRow(
            lambda x: str(int(x)),
            title="TCP Port",
            unset_val=-1,
            adjustment=Gtk.Adjustment(lower=-1, step_increment=1, upper=65535),
        )
        self.add_row(self.tcp_row.getWidget())

        self.tls_row = BindableSpinRow(
            lambda x: str(int(x)),
            title="TLS Port",
            unset_val=-1,
            adjustment=Gtk.Adjustment(lower=-1, step_increment=1, upper=65535),
        )
        self.add_row(self.tls_row.getWidget())

    def bind(self, xml_tree: ET.Element, show_apply_cb: callable):
        self.xml_tree = xml_tree

        if self.xml_tree.get("type") in ["spice", "vnc"]:
            self.type_combo.setSelection(["none", "address", "network", "socket"])
        else:
            self.type_combo.setSelection(["none", "address", "network"])

        listen = self.xml_tree.find("listen")
        if listen is None:
            listen = ET.SubElement(self.xml_tree, "listen")
        self.type_combo.bindAttr(listen, "type", self.__onTypeChanged__)

        self.show_apply_cb = show_apply_cb

        self.updateData()

    def updateData(self):
        """Update the rows given the current graphics device
        tree."""
        self.set_expanded(True)
        self.set_enable_expansion(True)
        listen_type = self.type_combo.getSelectedString()

        self.address_row.set_visible(False)
        self.address_row.unbind()
        self.network_row.set_visible(False)
        self.network_row.unbind()
        self.address_prop_row.set_visible(False)
        self.socket_row.set_visible(False)
        self.socket_row.unbind()
        self.autoport_row.unbind()

        listen = self.xml_tree.find("listen")

        if listen_type == "address":
            self.address_row.set_visible(True)
            self.address_row.bindAttr(listen, "address", self.show_apply_cb)
            self.autoport_row.bindAttr(
                self.xml_tree, "autoport", self.__onAutoportChanged__
            )
        elif listen_type == "network":
            self.network_row.set_visible(True)
            self.network_row.bindAttr(listen, "network", self.show_apply_cb)
            self.address_prop_row.set_visible(True)
            self.address_prop_row.set_subtitle(listen.get("address", ""))
        elif listen_type == "socket":
            self.socket_row.set_visible(True)
            self.socket_row.bindAttr(listen, "socket", self.show_apply_cb)
        elif listen_type == "none":
            self.set_enable_expansion(False)
            self.set_expanded(False)

        self.__setPortVisibility__()

    def __setPortVisibility__(self):
        """Set visibility of autoport, port and tlsPort rows."""
        listen_type = self.type_combo.getSelectedString()
        graphics_type = self.xml_tree.get("type")

        if listen_type == "address":
            self.autoport_row.set_visible(True)
            autoport = self.autoport_row.getWidget().get_active()

            self.tls_row.set_visible(graphics_type == "spice" and not autoport)
            self.tcp_row.set_visible(not autoport)

            if autoport:
                self.tcp_row.unbind()
                self.tls_row.unbind()
                if "port" in self.xml_tree.attrib:
                    del self.xml_tree.attrib["port"]
                if "tlsPort" in self.xml_tree.attrib:
                    del self.xml_tree.attrib["tlsPort"]
            else:
                self.tcp_row.bindAttr(self.xml_tree, "port", self.show_apply_cb)
                self.tls_row.bindAttr(self.xml_tree, "tlsPort", self.show_apply_cb)
        else:
            self.autoport_row.set_visible(False)
            self.tls_row.set_visible(False)
            self.tcp_row.set_visible(False)
            self.tcp_row.unbind()
            self.tls_row.unbind()
            if "autoport" in self.xml_tree.attrib:
                del self.xml_tree.attrib["autoport"]
            if "port" in self.xml_tree.attrib:
                del self.xml_tree.attrib["port"]
            if "tlsPort" in self.xml_tree.attrib:
                del self.xml_tree.attrib["tlsPort"]

    def __onTypeChanged__(self):
        if self.xml_tree is None:
            return

        listen = self.xml_tree.find("listen")
        listen.clear()
        listen.set("type", self.type_combo.getSelectedString())

        self.updateData()
        self.show_apply_cb()

    def __onAutoportChanged__(self):
        if self.xml_tree is None:
            return

        self.__setPortVisibility__()
        self.show_apply_cb()


class GraphicsPage(BaseDevicePage):
    rows_per_type = {
        "sdl": [],  # Unsupported
        "vnc": [
            "passwd",
            "keymap",
            "sharePolicy",
            "audio",
            "listen",
        ],
        "spice": [
            "passwd",
            "keymap",
            "clipboard",
            "mouse",
            "filetransfer",
            "gl",
            "listen",
        ],
        "rdp": ["multiUser", "replaceUser", "listen"],
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

        self.rows["listen"] = ListenRow(self.parent.getWindow())
        self.group.add(self.rows["listen"])

        self.rows["passwd"] = BindablePasswordRow(title="Connection Password")
        self.group.add(self.rows["passwd"].widget)

        self.rows["keymap"] = BindableEntryRow(title="Keymap")
        self.group.add(self.rows["keymap"])

        self.rows["sharePolicy"] = BindableComboRow(
            ["allow-exclusive", "force-shared", "ignore"], title="Share Policy"
        )
        self.group.add(self.rows["sharePolicy"])

        self.rows["audio"] = BindableEntryRow(title="Audio Device ID Mapping")
        self.group.add(self.rows["audio"])

        self.rows["clipboard"] = BindableSwitchRow(
            "yes", "no", True, title="Allow Copy/Paste"
        )
        self.group.add(self.rows["clipboard"].switch_row)

        self.rows["mouse"] = BindableComboRow(["client", "server"], title="Mouse Mode")
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
            title="Replace User",
            subtitle="Drop connection when new user connects",
        )
        self.group.add(self.rows["replaceUser"].switch_row)

        self.rows["p2p"] = BindableSwitchRow(
            "on", "off", title="Enable peer-to-peer connections"
        )
        self.group.add(self.rows["p2p"].switch_row)

        self.rows["address"] = BindableEntryRow(title="DBus Address")
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
        self.type_row.bindAttr(self.xml_tree, "type", self.__onTypeChanged__)

        t = self.type_row.getSelectedString()

        for row_name in self.rows_per_type[t]:
            self.rows[row_name].set_visible(True)
            row = self.rows[row_name]
            if row_name in [
                "display",
                "fullscreen",
                "passwd",
                "keymap",
                "sharePolicy",
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
                row.bindAttr(audio, "id", self.__onAudioChanged__)
            elif row_name in ["gl", "listen"]:
                row.bind(self.xml_tree, self.showApply)

    def __onTypeChanged__(self):
        self.xml_tree.clear()
        self.xml_tree.set("type", self.type_row.getSelectedString())
        self.updateData()
        self.showApply()

    def __onAudioChanged__(self):
        row = self.rows["audio"]
        if row.get_text() == "":
            self.xml_tree.remove(row.elem)
        else:
            self.xml_tree.append(row.elem)
        self.showApply()

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return self.xml_tree.get("type", "").upper() + " Graphics "

    def getDescription(self) -> str:
        return "Graphical Framebuffer"

    def getIconName(self) -> str:
        return "waves-and-screen-symbolic"
