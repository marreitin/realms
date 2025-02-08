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

from gi.repository import Adw, Gtk

from realms.helpers import (
    ResultWrapper,
    bytesToString,
    failableAsyncJob,
    getETText,
    stringToBytes,
)
from realms.libvirt_wrap import Pool
from realms.libvirt_wrap.constants import *
from realms.ui.builders import (
    BindableEntryRow,
    GenericPreferencesRow,
    sourceViewGetText,
    sourceViewSetText,
    xmlSourceView,
)
from realms.ui.builders.common import simpleErrorDialog
from realms.ui.builders.pool.pool_permissions_box import PoolPermissionsBox


class AddVolumeDialog:
    def __init__(
        self, window: Adw.ApplicationWindow, pool: Pool, create_cb: callable = None
    ):
        self.window = window
        self.pool = pool
        self.create_cb = create_cb
        self.pool.register_callback_any(self.__onConnectionEvent__, None)
        self.tree = None

        # Create a Builder
        self.builder = Gtk.Builder.new_from_resource(
            "/com/github/marreitin/realms/gtk/addvol.ui"
        )

        # Obtain and show the main window
        self.dialog = self.__obj__("main-dialog")
        self.dialog.connect("closed", self.__onDialogClosed__)
        self.dialog.present(self.window)

        self.__obj__("btn-finish").connect("clicked", self.__onApplyClicked__)
        self.__obj__("btn-finish").set_sensitive(False)

        self.xml_view = xmlSourceView()
        self.__obj__("xml-box").append(self.xml_view)

        self.__obj__("main-stack").connect(
            "notify::visible-child", self.__onStackChanged__
        )

        # Build preferences
        prefs_group = Adw.PreferencesGroup(title="Volume settings")
        self.__obj__("prefs-page").add(prefs_group)

        self.name_row = BindableEntryRow(title="Name")
        prefs_group.add(self.name_row)

        volume_formats = self.pool.pool_capabilities.volume_formats
        format_types = volume_formats[self.pool.getETree().get("type")]
        if format_types is not None:
            self.format_row = Adw.ComboRow(
                title="Volume format", model=Gtk.StringList(strings=format_types)
            )
            prefs_group.add(self.format_row)
            self.format_row.connect("notify::selected", self.__onFormatChanged__)

        self.capacity_row = BindableEntryRow(title="Capacity")
        prefs_group.add(self.capacity_row)

        self.allocation_row = BindableEntryRow(title="Allocation")
        prefs_group.add(self.allocation_row)

        self.perms_row = GenericPreferencesRow()
        self.perms_row.addChild(
            Gtk.Label(label="Target permissions", halign=Gtk.Align.START)
        )
        self.perms_box = PoolPermissionsBox(lambda *x: [])
        self.perms_row.addChild(self.perms_box)
        prefs_group.add(self.perms_row)

        self.__loadTree__()

    def __loadTree__(self):
        if self.tree is None:
            self.tree = ET.Element("volume")

        name = self.tree.find("name")
        if name is None:
            name = ET.SubElement(self.tree, "name")
        self.name_row.bindText(name, self.__checkValidity__)

        capacity = self.tree.find("capacity")
        if capacity is None:
            capacity = ET.SubElement(self.tree, "capacity")
        self.capacity_row.bindText(
            capacity,
            self.__checkValidity__,
            lambda t: str(stringToBytes(t)),
            bytesToString,
        )

        allocation = self.tree.find("allocation")
        if allocation is None:
            allocation = ET.SubElement(self.tree, "allocation")
        self.allocation_row.bindText(
            allocation,
            self.__checkValidity__,
            lambda t: str(stringToBytes(t)),
            bytesToString,
        )

        target = self.tree.find("target")
        if target is None:
            target = ET.SubElement(self.tree, "target")

        permissions = target.find("permissions")
        if permissions is None:
            permissions = ET.SubElement(target, "permissions")
        self.perms_box.connectData(permissions)

        volume_formats = self.pool.pool_capabilities.volume_formats
        format_types = volume_formats[self.pool.getETree().get("type")]
        if format_types is not None:
            f = target.find("format")
            if f is None:
                f = ET.SubElement(target, "format")
            if f.get("type", "") not in format_types:
                f.set("type", format_types[0])
            self.format_row.set_selected(
                format_types.index(f.get("type", format_types[0]))
            )

    def __onApplyClicked__(self, btn):
        def onFailed(e: Exception):
            traceback.print_exc()
            simpleErrorDialog("Couldn't create volume", str(e), self.window)
            self.__loadTree__()

        def onSucceeded(res: ResultWrapper):
            if res.failed:
                return
            vir_volume = res.data
            self.dialog.close()
            if self.create_cb is not None:
                self.create_cb(vir_volume)

        try:
            # Clean tree from unused permissions
            target = self.tree.find("target")
            permissions = target.find("permissions")
            if [
                getETText(permissions.find("owner")),
                getETText(permissions.find("group")),
                getETText(permissions.find("mode")),
            ] == ["", "", ""]:
                target.remove(permissions)
            elif "" in [
                getETText(permissions.find("owner")),
                getETText(permissions.find("group")),
                getETText(permissions.find("mode")),
            ]:
                raise ValueError(
                    "When using permissions, at least owner, group and mode have to be filled out"
                )

            if self.__obj__("main-stack").get_visible_child_name() != "xml":
                failableAsyncJob(
                    self.pool.addVolume, [self.tree], onFailed, onSucceeded
                )
            else:
                xml = sourceViewGetText(self.xml_view)
                failableAsyncJob(self.pool.addVolumeXML, [xml], onFailed, onSucceeded)

        except Exception as e:
            simpleErrorDialog("Invalid settings", str(e), self.window)

    def __checkValidity__(self, *_):
        self.__obj__("btn-finish").set_sensitive(False)

        if not self.name_row.getWidget().get_text():
            return

        if not self.capacity_row.getWidget().get_text():
            return

        target = self.tree.find("target")
        permissions = target.find("permissions")

        if [
            getETText(permissions.find("owner")),
            getETText(permissions.find("group")),
            getETText(permissions.find("mode")),
        ].count("") not in [0, 3]:
            return

        self.__obj__("btn-finish").set_sensitive(True)

    def __onStackChanged__(self, *args):
        name = self.__obj__("main-stack").get_visible_child_name()
        if name == "settings":
            xml = sourceViewGetText(self.xml_view)
            self.tree = ET.fromstring(xml)
            self.__loadTree__()
        else:
            ET.indent(self.tree)
            xml = ET.tostring(self.tree, encoding="unicode")
            sourceViewSetText(self.xml_view, xml)

    def __onFormatChanged__(self, *args):
        volume_formats = self.pool.pool_capabilities.volume_formats
        format_types = volume_formats[self.pool.getETree().get("type")]
        selected = self.format_row.get_selected()

        target = self.tree.find("target")
        f = target.find("format")
        if f is None:
            f = ET.SubElement(target, "format")
        f.set("type", format_types[selected])

    def __obj__(self, name: str):
        o = self.builder.get_object(name)
        if o is None:
            raise NotImplementedError(f"Object { name } could not be found!")
        return o

    def __onConnectionEvent__(self, conn, obj, type_id, event_id, detail_id, opaque):
        if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.dialog.close()
        elif type_id == CALLBACK_TYPE_POOL_GENERIC:
            if event_id in [POOL_EVENT_DELETED]:
                self.dialog.close()

    def __onDialogClosed__(self, *args):
        self.pool.unregister_callback(self.__onConnectionEvent__)
