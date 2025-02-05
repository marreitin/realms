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

from realms.libvirt_wrap import PoolCapabilities
from realms.ui.builders.bindable_entries import BindableEntry
from realms.ui.builders.common import iconButton


class DeviceRow(Gtk.Box):
    def __init__(self, xml_elem: ET.Element, parent):
        super().__init__(css_classes=["linked"])

        self.parent = parent
        self.xml_elem = xml_elem

        self.entry = BindableEntry(placeholder_text="Device", hexpand=True)
        self.entry.bindAttr(xml_elem, "path", parent.show_apply_cb)
        self.append(self.entry)

        remove_btn = iconButton(
            "",
            "list-remove-symbolic",
            self.onRemoveClicked,
            tooltip_text="Remove this device",
        )
        self.append(remove_btn)

    def onRemoveClicked(self, btn):
        self.parent.removeDeviceRow(self)


class HostRow(Gtk.Box):
    def __init__(self, xml_elem: ET.Element, parent):
        super().__init__(css_classes=["linked"])

        self.parent = parent
        self.xml_elem = xml_elem

        self.name_entry = BindableEntry(
            placeholder_text="Remote host address", hexpand=True
        )
        self.name_entry.bindAttr(xml_elem, "name", parent.show_apply_cb)
        self.append(self.name_entry)

        self.port_entry = BindableEntry(
            placeholder_text="Port", input_purpose=Gtk.InputPurpose.DIGITS
        )
        self.port_entry.bindText(xml_elem, "port", parent.show_apply_cb)
        self.append(self.port_entry)

        remove_btn = iconButton(
            "",
            "list-remove-symbolic",
            self.onRemoveClicked,
            tooltip_text="Remove this host",
        )
        self.append(remove_btn)

    def onRemoveClicked(self, btn):
        self.parent.removeHostRow(self)


class AuthBox(Gtk.Box):
    def __init__(self, pool_capabilities: PoolCapabilities, show_apply_cb: callable):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.xml_elem = None
        self.pool_capabilities = pool_capabilities
        self.show_apply_cb = show_apply_cb
        self.pool_type = None

        box = Gtk.Box(spacing=6)
        self.append(box)
        box.append(
            Gtk.Label(
                label="Authentication",
                hexpand=True,
                halign=Gtk.Align.START,
            )
        )

        self.auth_switch = Gtk.Switch()
        self.auth_switch.connect("notify::active", self.onAuthSwitchChanged)
        box.append(self.auth_switch)

        self.inner_box = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
        self.append(self.inner_box)
        self.inner_box.set_visible(False)

        box = Gtk.Box(spacing=6, homogeneous=True)
        self.inner_box.append(box)
        self.auth_type = Gtk.Entry(sensitive=False, tooltip_text="Authentication type")
        box.append(self.auth_type)

        self.auth_username = BindableEntry(
            placeholder_text="Username", tooltip_text="Username for authentication"
        )
        box.append(self.auth_username)

        self.auth_secret_uuid = BindableEntry(
            placeholder_text="Authentication secret UUID",
            tooltip_text="UUID of corresponding libvirt secret",
        )
        self.inner_box.append(self.auth_secret_uuid)

        self.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

    def onAuthSwitchChanged(self, *args):
        auth = ET.SubElement(self.source_tree, "auth")
        if self.auth_switch.get_active():
            if auth is None:
                auth = ET.SubElement(self.source_tree, "auth")
            self.inner_box.set_visible(True)
            self.bind()
        else:
            self.inner_box.set_visible(False)
            if auth is not None:
                self.source_tree.remove(auth)

        self.show_apply_cb()

    def setTree(self, source_tree: ET.Element):
        self.source_tree = source_tree

    def setVisible(self, visible: bool, pool_type: str):
        self.pool_type = pool_type

        self.set_visible(visible)

        if visible == True:
            self.auth_type.get_buffer().set_text(
                "ceph" if pool_type == "rbd" else "chap", -1
            )
            auth = self.source_tree.find("auth")
            if auth is None:
                self.auth_switch.set_active(False)
            else:
                self.auth_switch.set_active(True)
                self.bind()
        else:
            auth = self.source_tree.find("auth")
            if auth is not None:
                self.source_tree.remove(auth)

    def bind(self):
        auth = self.source_tree.find("auth")
        auth.set("type", "ceph" if self.pool_type == "ceph" else "chap")

        self.auth_username.bindAttr(auth, "username", self.show_apply_cb)

        secret = auth.find("secret")
        if secret is None:
            secret = ET.SubElement(auth, "secret", attrib={"uuid": ""})
        self.auth_secret_uuid.bindAttr(secret, "uuid", self.show_apply_cb)


class PoolSourceRow(Adw.PreferencesRow):
    def __init__(self, pool_capabilities: PoolCapabilities, show_apply_cb):
        super().__init__()

        self.pool_capabilities = pool_capabilities
        self.show_apply_cb = show_apply_cb
        self.source_tree = None

        self.devices_box = None
        self.devices_list = None
        self.device_rows = []

        self.hosts_box = None
        self.hosts_list = None
        self.host_rows = []

        self.auth_box = None

        self.name_entry = None
        self.format_selection = None
        self.dir_entry = None

        self.build()

    def build(self):
        outer_box = Gtk.Box(
            spacing=6,
            margin_top=12,
            margin_bottom=12,
            margin_start=12,
            margin_end=12,
            orientation=Gtk.Orientation.VERTICAL,
        )
        self.set_child(outer_box)

        label = Gtk.Label(
            label="Storage source",
            css_classes=["heading"],
            hexpand=True,
            halign=Gtk.Align.START,
        )
        outer_box.append(label)

        # Devices box
        self.devices_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        outer_box.append(self.devices_box)

        box = Gtk.Box()
        self.devices_box.append(box)
        label = Gtk.Label(
            label="Devices",
            hexpand=True,
            halign=Gtk.Align.START,
        )
        box.append(label)
        btn = iconButton(
            "",
            "list-add-symbolic",
            self.onAddDeviceClicked,
            css_classes=["flat"],
            tooltip_text="Add storage device",
        )
        box.append(btn)

        self.devices_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.devices_box.append(self.devices_list)

        self.devices_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Hosts box
        self.hosts_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        outer_box.append(self.hosts_box)

        box = Gtk.Box()
        self.hosts_box.append(box)
        label = Gtk.Label(
            label="Hosts",
            hexpand=True,
            halign=Gtk.Align.START,
        )
        box.append(label)
        btn = iconButton(
            "",
            "list-add-symbolic",
            self.onAddHostClicked,
            css_classes=["flat"],
            tooltip_text="Add storage host",
        )
        box.append(btn)

        self.hosts_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.hosts_box.append(self.hosts_list)

        self.hosts_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Auth box
        self.auth_box = AuthBox(self.pool_capabilities, self.show_apply_cb)
        outer_box.append(self.auth_box)

        # Rest
        self.name_entry = BindableEntry(
            placeholder_text="Backend storage name",
            tooltip_text="Name for named storage device",
        )
        outer_box.append(self.name_entry)

        self.format_box = Gtk.Box(spacing=6, hexpand=True)
        outer_box.append(self.format_box)
        self.format_box.append(Gtk.Label(label="Pool format"))
        self.format_selection = Gtk.DropDown(
            tooltip_text="Storage pool format", hexpand=True
        )
        self.format_selection.connect("notify::selected", self.onFormatChanged)
        self.format_box.append(self.format_selection)

        self.dir_entry = BindableEntry(
            placeholder_text="Source directory", tooltip_text="Source directory"
        )
        outer_box.append(self.dir_entry)

    def onAddDeviceClicked(self, btn):
        dev = ET.SubElement(self.source_tree, "device", attrib={"path": ""})
        self.addDeviceRow(dev)

    def onAddHostClicked(self, btn):
        host = ET.SubElement(self.source_tree, "host", attrib={"name": "", "port": ""})
        self.addHostRow(host)

    def onFormatChanged(self, *args):
        f = self.source_tree.find("format")
        options = []
        model = self.format_selection.get_model()
        for i in range(model.get_n_items()):
            options.append(model.get_string(i))
        f.set("type", options[self.format_selection.get_selected()])

        self.show_apply_cb()

    def loadTree(self, source_tree: ET.Element):
        self.source_tree = source_tree
        self.auth_box.setTree(source_tree)

    def addDeviceRow(self, xml_elem: ET.Element):
        row = DeviceRow(xml_elem, self)
        self.devices_list.append(row)
        self.device_rows.append(row)
        self.show_apply_cb()

    def removeDeviceRow(self, row):
        self.source_tree.remove(row.xml_elem)
        self.device_rows.remove(row)
        self.devices_list.remove(row)
        self.show_apply_cb()

    def addHostRow(self, xml_elem: ET.Element):
        row = HostRow(xml_elem, self)
        self.hosts_list.append(row)
        self.host_rows.append(row)
        self.show_apply_cb

    def removeHostRow(self, row):
        self.source_tree.remove(row.xml_elem)
        self.host_rows.remove(row)
        self.hosts_list.remove(row)
        self.show_apply_cb()

    def reload(self, pool_type: str):
        pool_formats = self.pool_capabilities.pool_formats

        # Devices
        if pool_type in [
            "fs",
            "logical",
            "disk",
            "iscsi",
            "iscsi-direct",
            "zfs",
            "vstorage",
        ]:
            self.devices_box.set_visible(True)
            devices = self.source_tree.findall("device")
            for row in self.device_rows:
                self.devices_list.remove(row)
            self.device_rows.clear()
            for d in devices:
                self.addDeviceRow(d)
        else:
            # Not needed to remove devices from xml, as this is
            # done further up if necessary.
            self.devices_box.set_visible(False)
            for row in self.device_rows:
                self.devices_list.remove(row)
            self.device_rows.clear()

        # Directory
        if pool_type in ["netfs", "gluster"]:  # Dir not really needed here
            self.dir_entry.set_visible(True)
            d = self.source_tree.find("dir")
            if d is None:
                d = ET.SubElement(self.source_tree, "dir", attrib={"path": ""})
            self.dir_entry.bindAttr(d, "path", self.show_apply_cb)
        else:
            self.dir_entry.set_visible(False)
            self.dir_entry.unbind()
            d = self.source_tree.find("dir")
            if d is not None:
                self.source_tree.remove(d)  # There can only be one anyway

        # Hosts
        if pool_type in ["netfs", "iscsi", "iscsi-direct", "rbd", "gluster"]:
            self.hosts_box.set_visible(True)
            hosts = self.source_tree.findall("host")
            for row in self.host_rows:
                self.hosts_list.remove(row)
            self.host_rows.clear()
            for h in hosts:
                self.addHostRow(h)
        else:
            self.hosts_box.set_visible(False)
            for row in self.host_rows:
                self.hosts_list.remove(row)
            self.host_rows.clear()

        # Authentication
        if pool_type in ["iscsi", "iscsi-direct", "rbd"]:
            self.auth_box.setVisible(True, pool_type)
        else:
            self.auth_box.setVisible(False, pool_type)

        # Source name
        if pool_type in ["logical", "rbd", "gluster"]:
            self.name_entry.set_visible(True)
            name = self.source_tree.find("name")
            if name is None:
                name = ET.SubElement(self.source_tree, "name")

            self.name_entry.bindText(name, self.show_apply_cb)
        else:
            self.name_entry.set_visible(False)
            self.name_entry.unbind()
            name = self.source_tree.find("name")
            if name is not None:
                self.source_tree.remove(name)

        # Source format
        if pool_type in ["fs", "netfs", "disk", "logical"]:
            self.format_selection.disconnect_by_func(self.onFormatChanged)
            self.format_box.set_visible(True)

            f = self.source_tree.find("format")
            format_options = pool_formats[pool_type]
            self.format_selection.set_model(Gtk.StringList(strings=format_options))

            if f is None:
                f = ET.SubElement(
                    self.source_tree, "format", attrib={"type": format_options[0]}
                )
            if f.get("type", format_options[0]) not in format_options:
                f.set("type", format_options[0])

            self.format_selection.set_selected(format_options.index(f.get("type")))
            self.format_selection.connect("notify::selected", self.onFormatChanged)

        else:
            self.format_box.set_visible(False)
            f = self.source_tree.find("format")
            if f is not None:
                self.source_tree.remove(f)
