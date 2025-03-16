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

from realms.libvirt_wrap import Connection
from realms.libvirt_wrap.constants import *
from realms.ui.components import sourceViewGetText, sourceViewSetText, xmlSourceView
from realms.ui.components.common import simpleErrorDialog
from realms.ui.components.net import NetGeneralGroup, NetIPGroup
from realms.ui.components.preference_widgets import RealmsPreferencesPage


class AddNetDialog:
    """Dialog to add a virtual network."""
    def __init__(self, window: Adw.ApplicationWindow, connection: Connection):
        self.window = window
        self.connection = connection

        self.connection.registerCallback(self.__onConnectionEvent__)

        # Create a Builder
        self.builder = Gtk.Builder.new_from_resource(
            "/com/github/marreitin/realms/gtk/addnet.ui"
        )

        # Obtain and show the main window
        self.dialog = self.__obj__("main-dialog")
        self.dialog.connect("closed", self.__onDialogClosed__)
        self.dialog.present(self.window)

        prefs_page = RealmsPreferencesPage(clamp=False)
        self.__obj__("prefs-box").append(prefs_page)

        self.prefs_group = NetGeneralGroup(True, self.window, lambda *x: [], None)
        prefs_page.add(self.prefs_group)

        self.ip_group = NetIPGroup(self, lambda *x: [])
        prefs_page.add(self.ip_group)

        self.tree = ET.Element("network")
        self.prefs_group.updateData(self.tree, True)
        self.ip_group.updateData(self.tree)

        self.__obj__("btn-finish").connect("clicked", self.__onApplyClicked__)

        self.xml_view = xmlSourceView()
        self.__obj__("xml-box").append(self.xml_view)

        self.__obj__("main-stack").connect("notify::visible-child", self.__onStackChanged__)

    def __onApplyClicked__(self, _):
        try:
            if self.__obj__("main-stack").get_visible_child_name() != "XML":
                self.connection.addNetworkTree(
                    self.tree, self.prefs_group.getAutostart()
                )
            else:
                xml = sourceViewGetText(self.xml_view)
                self.connection.addNetwork(xml, self.prefs_group.getAutostart())
            self.dialog.close()
        except Exception as e:
            simpleErrorDialog("Invalid settings", str(e), self.window)

    def __onStackChanged__(self, *_):
        name = self.__obj__("main-stack").get_visible_child_name()
        if name == "settings":
            xml = sourceViewGetText(self.xml_view)
            self.tree = ET.fromstring(xml)
            self.prefs_group.updateData(self.tree, True)
        else:
            ET.indent(self.tree)
            xml = ET.tostring(self.tree, encoding="unicode")
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

    def getWindow(self):
        """Return window, used for hosting the IP page."""
        return self.window

    def __onDialogClosed__(self, *args):
        self.connection.unregisterCallback(self.__onConnectionEvent__)
