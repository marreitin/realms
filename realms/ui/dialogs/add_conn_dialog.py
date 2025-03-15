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
from gi.repository import Adw, Gtk

from realms.helpers import Settings


class AddConnDialog:
    hypervisor_types = {
        "Bhyve": "bhyve",
        "Cloud": "ch",
        "HyperV": "hyperv",
        "LXC": "lxc",
        "OpenVZ": "openvz",
        "QEMU/KVM": "qemu",
        "Virtual Box": "vbox",
        "Virtuozzo": "vz",
        "VMware ESX": "esx",
        "VMware Fusion": "vmwarefusion",
        "VMware GSX": "gsx",
        "VMware Player": "vmwareplayer",
        "VMware VPX": "vpx",
        "VMware Workstation": "vmwarews",
        "Xen": "xen",
        "Manual": "manual",
    }

    default_paths = {
        "bhyve": "session",
        "ch": "ch",
        "HyperV": "",
        "hyperv": "system",
        "lxc": "system",
        "openvz": "system",
        "qemu": "system",
        "vbox": "session",
        "vz": "system",
        "esx": "",
        "vmwarefusion": "session",
        "gsx": "",
        "vmwareplayer": "session",
        "vpx": "",
        "vmwarews": "session",
        "xen": "system",
        "manual": "",
    }

    def __init__(self, window: Adw.ApplicationWindow):
        self.window = window

        # Create a Builder
        self.builder = Gtk.Builder.new_from_resource(
            "/com/github/marreitin/realms/gtk/addconn.ui"
        )

        # Obtain and show the main window
        self.dialog = self.obj("main-dialog")
        self.dialog.present(self.window)

        self.obj("remote").set_enable_expansion(False)

        self.obj("type").set_model(
            Gtk.StringList(strings=list(self.hypervisor_types.keys()))
        )
        self.obj("type").set_selected(5)

        self.setVisibleRows()

        self.obj("name").connect("changed", self.onNameChanged)
        self.obj("name").grab_focus()
        self.obj("custom-url").connect("changed", self.onCustomURLChanged)
        self.obj("type").connect("notify::selected", self.onTypeChanged)
        self.obj("remote").connect("notify::enable-expansion", self.updateGeneratedURL)
        self.obj("rhost").connect("changed", self.onRHostChanged)
        self.obj("ruser").connect("changed", self.onRUserChanged)

        self.obj("btn-finish").connect("clicked", self.onApplyClicked)

    def setVisibleRows(self):
        self.updateGeneratedURL()
        self.obj("remote").set_visible(True)
        self.obj("url").set_visible(True)
        self.obj("custom-url").set_visible(False)

        hypervisor_type = self.hypervisor_types[
            self.obj("type").get_selected_item().get_string()
        ]

        if hypervisor_type == "manual":
            self.obj("remote").set_visible(False)
            self.obj("url").set_visible(False)
            self.obj("custom-url").set_visible(True)

    def onTypeChanged(self, row, pspec):
        if pspec.name == "selected":
            self.setVisibleRows()

    def buildURL(self):
        hypervisor_type = self.hypervisor_types[
            self.obj("type").get_selected_item().get_string()
        ]
        if hypervisor_type == "manual":
            return self.obj("custom-url").get_text()

        url = ""
        transport = ""
        if self.obj("remote").get_enable_expansion():
            transport = "+ssh"
        url += f"{ hypervisor_type }{ transport }://"

        if self.obj("remote").get_enable_expansion():
            url += self.obj("ruser").get_text()
            url += "@"
            url += self.obj("rhost").get_text()

        url += f"/{ self.default_paths[hypervisor_type] }"
        return url

    def updateGeneratedURL(self, *args):
        self.obj("url").set_subtitle(self.buildURL())

    def onNameChanged(self, *args):
        self.obj("name").set_css_classes([])
        self.updateGeneratedURL()

    def onCustomURLChanged(self, *args):
        self.obj("custom-url").set_css_classes([])
        self.updateGeneratedURL()

    def onRHostChanged(self, *args):
        self.obj("rhost").set_css_classes([])
        self.updateGeneratedURL()

    def onRUserChanged(self, *args):
        self.obj("ruser").set_css_classes([])
        self.updateGeneratedURL()

    def onApplyClicked(self, btn):
        failed = False

        name = self.obj("name").get_text()
        if not name:
            self.obj("name").set_css_classes(["error"])
            self.obj("name").set_title("A connection needs a name")
            failed = True

        url = self.buildURL()
        if url == "":
            self.obj("custom-url").set_css_classes(["error"])
            self.obj("custom-url").set_title("URL must be provided")
            failed = True

        hypervisor_type = self.hypervisor_types[
            self.obj("type").get_selected_item().get_string()
        ]
        if hypervisor_type != "manual":
            if self.obj("remote").get_enable_expansion():
                rhost = self.obj("rhost").get_text()
                if not rhost:
                    self.obj("rhost").set_css_classes(["error"])
                    self.obj("rhost").set_title("The remote host must be set")
                    failed = True
                ruser = self.obj("ruser").get_text()
                if not ruser:
                    self.obj("ruser").set_css_classes(["error"])
                    self.obj("ruser").set_title("The remote user must be set")
                    failed = True

        if failed:
            return

        # All good
        desc = self.obj("description").get_text()
        conns = Settings.get("connections")
        if conns is None:
            conns = []
        item = {
            "name": name,
            "desc": desc,
            "url": url,
            "autoconnect": self.obj("autoconnect").get_active(),
        }
        conns.append(item)
        Settings.put("connections", conns)

        self.window.addConnection(item)

        self.dialog.close()

    def obj(self, name: str):
        o = self.builder.get_object(name)
        if o is None:
            raise NotImplementedError(f"Object { name } could not be found!")
        return o
