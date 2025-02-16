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
import libvirt
from gi.repository import Adw, Gtk

from realms.libvirt_wrap import Domain
from realms.libvirt_wrap.constants import *
from realms.ui.components import sourceViewSetText, xmlSourceView


class InspectSnapshotDialog:
    def __init__(
        self,
        window: Adw.ApplicationWindow,
        domain: Domain,
        snapshot: libvirt.virDomainSnapshot,
    ):
        self.window = window
        self.domain = domain
        self.snapshot = snapshot

        self.domain.register_callback_any(self.onConnectionEvent, None)

        # Create a Builder
        self.builder = Gtk.Builder.new_from_resource(
            "/com/github/marreitin/realms/gtk/inspectsnapshot.ui"
        )

        # Obtain and show the main window
        self.dialog = self.obj("main-dialog")
        self.dialog.connect("closed", self.onDialogClosed)
        self.dialog.present(self.window)

        self.xml_view = xmlSourceView()
        self.xml_view.set_editable(False)
        self.obj("xml-box").append(self.xml_view)
        sourceViewSetText(self.xml_view, snapshot.getXMLDesc())

    def obj(self, name: str):
        o = self.builder.get_object(name)
        if o is None:
            raise NotImplementedError(f"Object { name } could not be found!")
        return o

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id, opaque):
        if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.dialog.close()
        elif type_id == CALLBACK_TYPE_DOMAIN_LIFECYCLE:
            if event_id == libvirt.VIR_DOMAIN_EVENT_DEFINED:
                self.dialog.close()

    def onDialogClosed(self, *args):
        self.domain.unregister_callback(self.onConnectionEvent)
