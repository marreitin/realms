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

import libvirt
from gi.repository import Adw, Gtk

from realms.helpers import ResultWrapper, failableAsyncJob
from realms.libvirt_wrap import Domain
from realms.libvirt_wrap.constants import *
from realms.ui.components import sourceViewGetText, xmlSourceView
from realms.ui.components.common import simpleErrorDialog


class TakeSnapshotDialog:
    def __init__(self, window: Adw.ApplicationWindow, domain: Domain):
        self.window = window
        self.domain = domain

        self.domain.register_callback_any(self.onConnectionEvent)

        # Create a Builder
        self.builder = Gtk.Builder.new_from_resource(
            "/com/github/marreitin/realms/gtk/takesnapshot.ui"
        )

        # Obtain and show the main window
        self.dialog = self.obj("main-dialog")
        self.dialog.connect("closed", self.onDialogClosed)
        self.dialog.present(self.window)

        self.obj("btn-finish").connect("clicked", self.onTakeClicked)

        self.xml_view = xmlSourceView()
        self.obj("xml-box").append(self.xml_view)

        self.obj("name-row").grab_focus()

    def onTakeClicked(self, btn):
        btn.set_sensitive(False)

        tree = None
        if self.obj("main-stack").get_visible_child_name() == "xml":
            xml = sourceViewGetText(self.xml_view)
            tree = ET.fromstring(xml)
        else:
            tree = ET.Element("domainsnapshot")
            name = self.obj("name-row").get_text()
            if name:
                n = ET.SubElement(tree, "name")
                n.text = name
            desc = self.obj("desc-row").get_text()
            if name:
                d = ET.SubElement(tree, "desc")
                d.text = desc

        def onFail(e):
            simpleErrorDialog("Taking snapshot failed", str(e), self.window)

        def onDone(res: ResultWrapper):
            btn.set_sensitive(True)
            if not res.failed:
                self.dialog.close()

        failableAsyncJob(
            self.domain.takeSnapshot,
            [ET.tostring(tree, encoding="unicode")],
            onFail,
            onDone,
        )

    def obj(self, name: str):
        o = self.builder.get_object(name)
        if o is None:
            raise NotImplementedError(f"Object { name } could not be found!")
        return o

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id):
        if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.dialog.close()
        elif type_id == CALLBACK_TYPE_DOMAIN_LIFECYCLE:
            if event_id == libvirt.VIR_DOMAIN_EVENT_DEFINED:
                self.dialog.close()

    def onDialogClosed(self, *_):
        self.domain.unregister_callback(self.onConnectionEvent)
