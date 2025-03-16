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
import traceback
import xml.etree.ElementTree as ET

import libvirt
from gi.repository import Adw, Gtk

from realms.libvirt_wrap import Domain
from realms.libvirt_wrap.constants import *
from realms.ui.components import sourceViewGetText, sourceViewSetText, xmlSourceView
from realms.ui.components.common import simpleErrorDialog
from realms.ui.components.domain.domain_page_host import DomainPageHost
from realms.ui.components.domain.tag_to_page import tagToPage
from realms.ui.window_reference import WindowReference


class AddDeviceDialog(DomainPageHost):
    """Dialog to add a virtual device to a domain."""

    # List of device names
    device_names = [
        "",
        "serial",
        "controller",
        "disk",
        "filesystem",
        "graphics",
        "hostdev",
        "iommu",
        "input",
        "lease",
        "memory",
        "memballoon",
        "interface",
        "panic",
        "rng",
        "redirdev",
        "redirfilter",
        "shmem",
        "smartcard",
        "sound",
        "tpm",
        "hub",
        "video",
        "vsock",
        "watchdog",
    ]

    # List of descriptive titles
    descriptive_titles = [
        "",
        "Character",
        "Controller",
        "Disk",
        "Filesystem",
        "Graphics",
        "Host Device",
        "I/O Memory Management Unit",
        "Input Device",
        "Lease",
        "Memory",
        "Memory Balloon",
        "Network Interface",
        "Panic Device",
        "Random Number Generator",
        "Redirection Device",
        "Redirection Filter",
        "Shared Memory",
        "Smart Card",
        "Sound Card",
        "Trusted Platform Module",
        "USB Hub",
        "Video Device",
        "Virtual Socket",
        "Watchdog Timer",
    ]

    def __init__(
        self,
        window: Adw.ApplicationWindow,
        domain: Domain,
        xml_tree: ET.Element,
        device_added_cb,
    ):
        self.window = window
        self.domain = domain
        self.xml_tree = xml_tree
        self.device_added_cb = device_added_cb
        self.device_tree = None
        self.device_settings = None

        self.domain.registerCallback(self.__onConnectionEvent__)

        # Create a Builder
        self.builder = Gtk.Builder.new_from_resource(
            "/com/github/marreitin/realms/gtk/adddev.ui"
        )

        # Obtain and show the main window
        self.dialog = self.__obj__("main-dialog")
        self.dialog.connect("closed", self.__onDialogClosed__)
        self.dialog.present(self.window)

        group = Adw.PreferencesGroup()
        self.__obj__("edit-box").append(group)
        self.type_row = Adw.ComboRow(
            title="Device type",
            model=Gtk.StringList(strings=self.descriptive_titles),
        )
        group.add(self.type_row)
        self.type_row.connect("notify::selected", self.__onTypeSelected__)

        self.__obj__("btn-finish").connect("clicked", self.__onApplyClicked__)

        self.xml_view = xmlSourceView()
        self.__obj__("xml-box").append(self.xml_view)

        self.__obj__("main-stack").connect(
            "notify::visible-child", self.__onStackChanged__
        )

    def __onTypeSelected__(self, *args):
        """A device type was selected."""
        if self.type_row.get_selected() == 0:
            # Empty default was chosen.
            if self.device_settings is not None:
                self.__obj__("edit-box").remove(self.device_settings.prefs_page)
            self.__obj__("btn-finish").set_sensitive(False)
            return

        self.__obj__("btn-finish").set_sensitive(True)
        tag = self.device_names[self.type_row.get_selected()]
        self.device_tree = ET.Element(tag)

        self.__updateDevicePage__()

    def __updateDevicePage__(self):
        """Show the correct device page."""
        if self.device_settings is not None:
            self.__obj__("edit-box").remove(self.device_settings.prefs_page)

        tag = self.device_tree.tag
        page_type = tagToPage(tag)

        self.device_settings = page_type(self, self.device_tree, True)
        self.device_settings.buildFull()
        self.__obj__("edit-box").append(self.device_settings.prefs_page)

    def __onApplyClicked__(self, _):
        try:
            if self.__obj__("main-stack").get_visible_child_name() == "xml":
                xml = sourceViewGetText(self.xml_view)
                self.device_tree = ET.fromstring(xml)
            self.device_added_cb(self.device_tree)
            self.dialog.close()
        except Exception as e:
            traceback.print_exc()
            simpleErrorDialog("Invalid settings", str(e), self.window)

    def __onStackChanged__(self, *_):
        name = self.__obj__("main-stack").get_visible_child_name()
        if name == "settings":
            xml = sourceViewGetText(self.xml_view)
            if xml != "":
                self.device_tree = ET.fromstring(xml)
                self.__updateDevicePage__()
        else:
            xml = ""
            if self.device_tree is not None:
                ET.indent(self.device_tree)
                xml = ET.tostring(self.device_tree, encoding="unicode")
            sourceViewSetText(self.xml_view, xml)

    def __obj__(self, name: str):
        o = self.builder.get_object(name)
        if o is None:
            raise NotImplementedError(f"Object { name } could not be found!")
        return o

    def __onConnectionEvent__(self, conn, obj, type_id, event_id, detail_id):
        if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.dialog.close()
        elif type_id == CALLBACK_TYPE_DOMAIN_GENERIC:
            if event_id == DOMAIN_EVENT_DELETED:
                self.dialog.close()
        elif type_id == CALLBACK_TYPE_DOMAIN_LIFECYCLE:
            if event_id == libvirt.VIR_DOMAIN_EVENT_DEFINED:
                self.dialog.close()

    def __onDialogClosed__(self, *args):
        self.domain.unregisterCallback(self.__onConnectionEvent__)

    # Implement DomainPageHost
    def getWindow(self):
        return self.window

    def getWindowRef(self):
        return WindowReference(self.window)
