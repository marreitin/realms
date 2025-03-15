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

from gi.repository import Adw

from realms.helpers import getETText
from realms.libvirt_wrap import PoolCapabilities
from realms.ui.components.bindable_entries import BindableComboRow, BindableEntryRow
from realms.ui.components.common import deleteRow, propertyRow
from realms.ui.window_reference import WindowReference

from .pool_source_row import PoolSourceRow
from .pool_target_row import PoolTargetRow


class PoolPreferencesGroup(Adw.PreferencesGroup):
    """General preferences group for storage pools.
    It is separated to make also use of it when creating new pools.
    """

    def __init__(
        self,
        pool_capabilities: PoolCapabilities,
        allow_name_edit: bool,
        window_ref: WindowReference,
        show_apply_cb: callable,
        delete_cb: callable,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.pool_capabilities = pool_capabilities
        self.allow_name_edit = allow_name_edit
        self.window_ref = window_ref
        self.show_apply_cb = show_apply_cb
        self.delete_cb = delete_cb

        self.xml_tree = None

        # General settings group
        self.name_row = None
        self.uuid_row = None
        self.title_row = None
        self.desc_row = None
        self.autostart_row = None
        self.type_row = None

        self.source_row = None
        self.target_row = None

        self.build()

    def build(self):
        if not self.allow_name_edit:
            self.name_row = propertyRow("Name")
            self.add(self.name_row)

            self.uuid_row = propertyRow("UUID")
            self.add(self.uuid_row)
        else:
            self.name_row = BindableEntryRow(title="Name")
            self.add(self.name_row)

        self.autostart_row = Adw.SwitchRow(
            title="Autostart", subtitle="Start storage pool on boot"
        )
        self.autostart_row.connect("notify::active", self.show_apply_cb)
        self.add(self.autostart_row)

        pool_types = self.pool_capabilities.pool_types
        self.type_row = BindableComboRow(pool_types, "", title="Storage Pool Type")
        self.add(self.type_row)

        self.source_row = PoolSourceRow(self.pool_capabilities, self.show_apply_cb)
        self.add(self.source_row)

        self.target_row = PoolTargetRow(self.show_apply_cb)
        self.add(self.target_row)

        if self.delete_cb is not None:
            self.add(deleteRow(self.delete_cb))

    def updateBindings(self, xml_tree: ET.Element, autostart: bool):
        """Update Bindings to xml tree"""
        self.xml_tree = xml_tree
        name = self.xml_tree.find("name")
        if name is None:
            name = ET.SubElement(self.xml_tree, "name")

        if not self.allow_name_edit:
            self.name_row.set_subtitle(getETText(name))
            self.uuid_row.set_subtitle(getETText(self.xml_tree.find("uuid")))
        else:
            self.name_row.bindText(name, self.show_apply_cb)

            self.set_title("")

        self.type_row.bindAttr(self.xml_tree, "type", self.onTypeChanged)

        self.autostart_row.set_active(autostart)

        source = self.xml_tree.find("source")
        if source is None:
            source = ET.SubElement(self.xml_tree, "source")
        self.source_row.loadTree(source)

        target = self.xml_tree.find("target")
        if target is None:
            target = ET.SubElement(self.xml_tree, "target")
        self.target_row.loadTree(target)

        self.setPoolType()

    def setPoolType(self):
        """Update which settings are shown from the given pool type"""
        pool_type = self.type_row.getSelectedString()
        if pool_type in [
            "dir",
            "fs",
            "netfs",
            "logical",
            "disk",
            "iscsi",
            "scsi",
            "mpath",
            "zfs",
        ]:
            self.target_row.set_visible(True)
        else:
            self.target_row.set_visible(False)
            target = self.xml_tree.find("target")
            target.clear()

        if pool_type in ["", "dir"]:
            self.source_row.set_visible(False)
            source = self.xml_tree.find("source")
            source.clear()
        else:
            self.source_row.set_visible(True)

        self.source_row.reload(pool_type)
        self.target_row.reload(pool_type)

    def getAutostart(self) -> bool:
        return self.autostart_row.get_active()

    def onTypeChanged(self, *args):
        if self.xml_tree is None:
            return

        self.setPoolType()
        self.show_apply_cb()
