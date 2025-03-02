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

from realms.helpers import getETText
from realms.libvirt_wrap import Connection, Secret
from realms.libvirt_wrap.constants import *
from realms.ui.components import iconButton
from realms.ui.components.preference_widgets import RealmsPreferencesPage
from realms.ui.dialogs.secret_dialog import SecretDialog


class SecretRow(Adw.ActionRow):
    """Row for a single secret in a connections secrets list."""

    def __init__(self, connection: Connection, secret: Secret, parent):
        super().__init__(activatable=True, selectable=False)

        self.connection = connection
        self.secret = secret
        self.parent = parent

        self.type_label = Gtk.Label(css_classes=["dim-label", "caption"], margin_end=12)
        self.add_suffix(self.type_label)

        open_btn = Gtk.Image.new_from_icon_name("external-link-symbolic")
        self.add_suffix(open_btn)

        self.update()

        self.connect("activated", self.onActivated)

    def onActivated(self, _):
        """A row was selected, show the details for that secret."""
        SecretDialog(self.parent.parent.window_ref.window, self.connection, self.secret)

    def update(self):
        """Update this rows metadata."""
        tree = self.secret.getETree()
        desc = tree.find("description")
        subtitle = "[No description]"
        if desc is not None:
            subtitle = getETText(desc)
        if subtitle != "":
            self.set_title(subtitle)

        self.set_subtitle(self.secret.getUUID())
        self.type_label.set_label(tree.find("usage").get("type").upper())


class SecretsPage(Gtk.Box):
    """Box with a list of all retrievable secrets of a
    connection."""

    def __init__(self, parent):
        super().__init__()

        self.parent = parent

        self.connection = self.parent.connection
        self.connection.register_callback_any(self.onConnectionEvent)

        self.secret_rows = []

        self.build()

    def build(self):
        """Build self."""
        self.prefs_page = RealmsPreferencesPage()
        self.append(self.prefs_page)

        self.secrets_group = Adw.PreferencesGroup(
            title="Secrets",
        )
        self.prefs_page.add(self.secrets_group)

        self.action_group = Adw.PreferencesGroup(vexpand=True)
        self.prefs_page.add(self.action_group)

        self.no_secrets_status = Adw.StatusPage(
            title="No secrets found",
            description="Some connections don't allow listing secrets.",
            icon_name="padlock2-symbolic",
            vexpand=True,
            child=iconButton(
                "Add secret",
                "",
                self.onAddSecretClicked,
                css_classes=["pill", "suggested-action"],
                margin_top=12,
                halign=Gtk.Align.CENTER,
            ),
        )
        self.action_group.add(self.no_secrets_status)

        add_btn = iconButton(
            "Add secret",
            "",
            self.onAddSecretClicked,
            css_classes=["pill", "suggested-action"],
            margin_top=12,
            halign=Gtk.Align.CENTER,
        )
        self.secrets_group.add(add_btn)

        self.refreshSecrets()

    def listSecrets(self, vir_secrets: list[libvirt.virSecret]):
        """Show the given secrets in the UI."""
        self.no_secrets_status.set_visible(len(vir_secrets) == 0)
        self.secrets_group.set_visible(len(vir_secrets) != 0)
        for vir_secret in vir_secrets:
            secret = Secret(self.connection, vir_secret)
            row = SecretRow(self.connection, secret, self)
            self.secret_rows.append(row)
            self.secrets_group.add(row)

    def refreshSecrets(self):
        """Refreshing was requested."""
        if self.connection.isConnected():
            self.connection.listSecrets(self.listSecrets)
        else:
            for row in self.secret_rows:
                self.secrets_group.remove(row)
            self.secret_rows.clear()

    def onAddSecretClicked(self, _):
        """Plus was clicked."""
        SecretDialog(self.parent.window_ref.window, self.connection, None)

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id):
        """Handle connection events."""
        if type_id == CALLBACK_TYPE_SECRET_GENERIC:
            if event_id == SECRET_EVENT_ADDED:
                pass
            elif event_id == SECRET_EVENT_DELETED:
                self.onSecretDeleted(obj)
        elif type_id == CALLBACK_TYPE_SECRET_LIFECYCLE:
            if event_id == libvirt.VIR_SECRET_EVENT_DEFINED:
                self.onSecretDefined(obj)
            elif event_id == libvirt.VIR_SECRET_EVENT_UNDEFINED:
                self.onSecretDeleted(obj)
        elif type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id == CONNECTION_EVENT_CONNECTED:
                self.refreshSecrets()
            elif event_id == CONNECTION_EVENT_DISCONNECTED:
                self.connection.unregister_callback(self.onConnectionEvent)
            elif event_id == CONNECTION_EVENT_DELETED:
                self.connection.unregister_callback(self.onConnectionEvent)

    def onSecretDefined(self, vir_secret: libvirt.virSecret):
        """A new secret was defined."""
        r = None
        for row in self.secret_rows:
            if row.secret.getUUID() == vir_secret.UUIDString():
                r = row
                break
        # The secret was only redefined
        if r is not None:
            r.update()
            return

        secret = Secret(self.connection, vir_secret)
        row = SecretRow(self.connection, secret, self)
        self.secret_rows.append(row)
        self.secrets_group.add(row)
        self.no_secrets_status.set_visible(False)
        self.secrets_group.set_visible(True)

    def onSecretDeleted(self, vir_secret: libvirt.virSecret):
        """A secret was deleted."""
        r = None
        for row in self.secret_rows:
            if row.secret.getUUID() == vir_secret.UUIDString():
                r = row
                break
        if r is not None:
            self.secret_rows.remove(r)
            self.secrets_group.remove(r)

        if len(self.secret_rows) == 0:
            self.no_secrets_status.set_visible(True)
            self.secrets_group.set_visible(False)
