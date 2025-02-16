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

from realms.helpers import getETText
from realms.libvirt_wrap import Connection, Secret
from realms.libvirt_wrap.constants import *
from realms.ui.components import (
    ActionOption,
    BindableComboRow,
    BindableEntryRow,
    BindablePasswordRow,
    BindableSwitchRow,
    iconButton,
    propertyRow,
    selectDialog,
    sourceViewGetText,
    sourceViewSetText,
    xmlSourceView,
)
from realms.ui.components.common import simpleErrorDialog

(
    MODE_ADDING,
    MODE_EDITING,
) = range(2)


class SecretDialog:
    def __init__(
        self,
        window: Adw.ApplicationWindow,
        connection: Connection,
        secret: Secret = None,
    ):
        self.window = window
        self.connection = connection
        self.secret = secret

        if self.secret is None:
            self.mode = MODE_ADDING
        else:
            self.mode = MODE_EDITING

        self.connection.register_callback_any(self.onConnectionEvent, None)

        # Create a Builder
        self.builder = Gtk.Builder.new_from_resource(
            "/com/github/marreitin/realms/gtk/addsecret.ui"
        )

        # Obtain and show the main window
        self.dialog = self.obj("main-dialog")
        self.dialog.connect("closed", self.onDialogClosed)
        self.dialog.present(self.window)
        self.dialog.set_title(
            "Add secret" if self.mode == MODE_ADDING else "Edit secret"
        )

        self.xml_tree = (
            ET.Element("secret") if self.mode == MODE_ADDING else self.secret.getETree()
        )

        self.group = Adw.PreferencesGroup(hexpand=True)
        self.obj("prefs-box").append(self.group)

        if self.mode == MODE_ADDING:
            self.uuid_row = BindableEntryRow(title="UUID")
        else:
            self.uuid_row = propertyRow("UUID")
        self.group.add(self.uuid_row)

        self.desc_row = BindableEntryRow(title="Description")
        self.group.add(self.desc_row)

        self.private_row = BindableSwitchRow("yes", "no", False, title="Private")
        self.group.add(self.private_row.getWidget())

        self.ephemeral_row = BindableSwitchRow(
            "yes",
            "no",
            False,
            title="Ephemeral",
            subtitle="Only ever keep this secret in memory",
        )
        self.group.add(self.ephemeral_row.getWidget())

        self.usage_row = BindableComboRow(
            ["volume", "ceph", "iscsi", "tls", "vtpm"], title="Usage type"
        )
        self.group.add(self.usage_row)

        self.volume_row = BindableEntryRow(title="Associated storage volume")
        self.group.add(self.volume_row)

        self.name_row = BindableEntryRow(title="Referencable name")
        self.group.add(self.name_row)

        self.iscsi_row = BindableEntryRow(title="Referencable target name")
        self.group.add(self.iscsi_row)

        self.value_row = BindablePasswordRow(title="Secret value")
        self.group.add(self.value_row.getWidget())

        if self.mode == MODE_EDITING:
            delete_row = Adw.ActionRow()
            self.group.add(delete_row)
            self.delete_btn = iconButton(
                "Remove", "user-trash-symbolic", css_classes=["flat"]
            )
            self.delete_btn.connect("clicked", self.onRemoveClicked)
            delete_row.add_prefix(self.delete_btn)

        self.updateUI()

        self.obj("btn-finish").set_visible(False)
        self.obj("btn-finish").connect("clicked", self.onApplyClicked)

        self.xml_view = xmlSourceView(lambda *a: self.showApply())
        self.obj("xml-box").append(self.xml_view)

        self.obj("main-stack").connect("notify::visible-child", self.onStackChanged)

    def updateUI(self):
        self.ephemeral_row.bindAttr(self.xml_tree, "ephemeral", self.showApply)
        self.private_row.bindAttr(self.xml_tree, "private", self.showApply)

        uuid = self.xml_tree.find("uuid")
        if uuid is None:
            uuid = ET.SubElement(self.xml_tree, "uuid")
        if self.mode == MODE_ADDING:
            self.uuid_row.bindText(uuid, self.showApply)
        else:
            self.uuid_row.set_subtitle(getETText(uuid))

        desc = self.xml_tree.find("description")
        if desc is None:
            desc = ET.SubElement(self.xml_tree, "description")
        self.desc_row.bindText(desc, self.showApply)

        usage = self.xml_tree.find("usage")
        if usage is None:
            usage = ET.SubElement(self.xml_tree, "usage", attrib={"type": "volume"})

        self.usage_row.bindAttr(usage, "type", self.onUsageTypeChanged)

        self.volume_row.set_visible(False)
        self.name_row.set_visible(False)
        self.iscsi_row.set_visible(False)

        if self.usage_row.getSelectedString() == "volume":
            self.volume_row.set_visible(True)
            volume = usage.find("volume")
            if volume is None:
                volume = ET.SubElement(usage, "volume")
            self.volume_row.bindText(volume, self.showApply)
        elif self.usage_row.getSelectedString() == "iscsi":
            self.iscsi_row.set_visible(True)
            target = usage.find("target")
            if target is None:
                target = ET.SubElement(usage, "target")
            self.iscsi_row.bindText(target, self.showApply)
        elif self.usage_row.getSelectedString() in ["ceph", "tls", "vtpm"]:
            self.name_row.set_visible(True)
            name = usage.find("name")
            if name is None:
                name = ET.SubElement(usage, "name")
            self.name_row.bindText(name, self.showApply)

        value = ET.Element("value")
        if self.mode == MODE_EDITING:
            try:
                value.text = self.secret.getSecretValue()
            except:
                self.value_row.getWidget().set_visible(False)
        else:
            value.text = ""
        self.value_row.bindText(value, self.showApply)

    def onUsageTypeChanged(self):
        usage = self.xml_tree.find("usage")
        usage.clear()
        usage.set("type", self.usage_row.getSelectedString())
        self.updateUI()
        self.showApply()

    def showApply(self):
        self.obj("btn-finish").set_visible(True)

    def onApplyClicked(self, btn):
        try:
            if self.obj("main-stack").get_visible_child_name() != "xml":
                xml = ET.tostring(self.xml_tree, encoding="unicode")
            else:
                xml = sourceViewGetText(self.xml_view)

            value = self.value_row.getWidget().get_text()
            if self.mode == MODE_ADDING:
                self.connection.addSecret(xml, value)
            else:
                self.secret.updateDefinition(xml)
                if self.value_row.getWidget().get_visible() and value != "":
                    self.secret.setSecretValue(value)

            self.dialog.close()
        except Exception as e:
            simpleErrorDialog("Invalid settings", str(e), self.window)

    def onStackChanged(self, *args):
        name = self.obj("main-stack").get_visible_child_name()
        if name == "settings":
            xml = sourceViewGetText(self.xml_view)
            self.xml_tree = ET.fromstring(xml)
            self.updateUI()
        else:
            ET.indent(self.xml_tree)
            xml = ET.tostring(self.xml_tree, encoding="unicode")
            sourceViewSetText(self.xml_view, xml)

    def obj(self, name: str):
        o = self.builder.get_object(name)
        if o is None:
            raise NotImplementedError(f"Object { name } could not be found!")
        return o

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id, opaque):
        if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.dialog.close()

    def onDialogClosed(self, *args):
        self.connection.unregister_callback(self.onConnectionEvent)

    def onRemoveClicked(self, *args):
        def onDelete():
            self.secret.deleteSecret()
            self.dialog.close()

        dialog = selectDialog(
            "Delete secret?",
            "Deleting a secret is irreversible",
            [
                ActionOption(
                    "Delete", onDelete, appearance=Adw.ResponseAppearance.DESTRUCTIVE
                )
            ],
        )
        dialog.present(self.window)
