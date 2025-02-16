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
from realms.ui.components.pool.pool_prefs_group import PoolPreferencesGroup


class AddPoolDialog:
    def __init__(self, window: Adw.ApplicationWindow, connection: Connection):
        self.window = window
        self.connection = connection

        self.connection.register_callback_any(self.__onConnectionEvent__, None)

        # Create a Builder
        self.builder = Gtk.Builder.new_from_resource(
            "/com/github/marreitin/realms/gtk/addpool.ui"
        )

        # Obtain and show the main window
        self.dialog = self.__obj__("main-dialog")
        self.dialog.connect("closed", self.__onDialogClosed__)
        self.dialog.present(self.window)

        self.prefs = PoolPreferencesGroup(
            self.connection.getPoolCapabilities(),
            True,
            self.window,
            lambda *x: [],
            None,
            title="Storage pool settings",
        )
        self.tree = ET.Element("pool")
        self.prefs.updateBindings(self.tree, True)

        self.__obj__("prefs-page").add(self.prefs)

        self.__obj__("btn-finish").connect("clicked", self.__onApplyClicked__)

        self.xml_view = xmlSourceView()
        self.__obj__("xml-box").append(self.xml_view)

        self.__obj__("main-stack").connect(
            "notify::visible-child", self.__onStackChanged__
        )

    def __onApplyClicked__(self, _):
        try:
            if self.__obj__("main-stack").get_visible_child_name() != "XML":
                self.connection.addPoolTree(self.tree, self.prefs.getAutostart())
            else:
                xml = sourceViewGetText(self.xml_view)
                self.connection.addPool(xml, self.prefs.getAutostart())
            self.dialog.close()
        except Exception as e:
            simpleErrorDialog("Invalid settings", str(e), self.window)

    def __onStackChanged__(self, *_):
        name = self.__obj__("main-stack").get_visible_child_name()
        if name == "settings":
            xml = sourceViewGetText(self.xml_view)
            self.tree = ET.fromstring(xml)
            self.prefs.updateBindings(self.tree, True)
        else:
            ET.indent(self.tree)
            xml = ET.tostring(self.tree, encoding="unicode")
            sourceViewSetText(self.xml_view, xml)

    def __obj__(self, name: str):
        o = self.builder.get_object(name)
        if o is None:
            raise NotImplementedError(f"Object { name } could not be found!")
        return o

    def __onConnectionEvent__(self, conn, obj, type_id, event_id, detail_id, _):
        if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.dialog.close()

    def __onDialogClosed__(self, *_):
        self.connection.unregister_callback(self.__onConnectionEvent__)
