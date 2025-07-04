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

from realms.helpers import bytesToString
from realms.libvirt_wrap.constants import *
from realms.ui.components import ActionOption, ApplyRow, propertyRow, selectDialog
from realms.ui.components.common import deleteRow
from realms.ui.components.preference_widgets import RealmsPreferencesPage


class ConnectionDetailsPage(Gtk.Box):
    """Page that hosts basically all settings for a connection, including
    the action box to connect, disconnect etc, and some details about the
    hypervisor.
    """

    def __init__(self, parent):
        super().__init__()

        self.parent = parent
        self.forget_btn = None

        self.apply_row = None
        self.secure_icon = None
        self.encrypted_icon = None

        self.prefs_page = None

        self.prefs_group = None
        self.name_row = None
        self.desc_row = None
        self.url_row = None
        self.autoconnect_row = None
        self.hostname_row = None
        self.security_row = None

        self.info_group = None
        self.max_vcpus_row = None
        self.max_mem_row = None
        self.emulator_path_row = None
        self.domain_type_row = None
        self.machine_row = None
        self.arch_row = None
        self.libvirt_ver_row = None
        self.conn_ver_row = None

        self.__build__()

    def __build__(self):
        """Build self."""
        toolbar_view = Adw.ToolbarView(hexpand=True, vexpand=True)
        self.append(toolbar_view)

        self.apply_row = ApplyRow(
            self.onApplyClicked,
            lambda *args: self.loadSettings(),
            "Disconnect to apply changes",
        )
        toolbar_view.add_bottom_bar(self.apply_row)
        self.apply_row.set_visible(False)

        # Main preferences
        self.prefs_page = RealmsPreferencesPage()
        toolbar_view.set_content(self.prefs_page)

        self.prefs_group = Adw.PreferencesGroup()
        self.prefs_page.add(self.prefs_group)

        # Security status icons
        sec_status_box = Gtk.Box(spacing=6)

        self.secure_icon = Gtk.Image.new_from_icon_name("security-high")
        self.secure_icon.set_tooltip_text("Secure")
        sec_status_box.append(self.secure_icon)

        self.encrypted_icon = Gtk.Image.new_from_icon_name(
            "network-wireless-encrypted-symbolic"
        )
        self.encrypted_icon.set_tooltip_text("Encrypted")
        sec_status_box.append(self.encrypted_icon)

        # Preference rows.
        self.name_row = Adw.EntryRow(title="Name")
        self.prefs_group.add(self.name_row)
        self.desc_row = Adw.EntryRow(title="Description")
        self.prefs_group.add(self.desc_row)
        self.url_row = Adw.EntryRow(title="URL")
        self.prefs_group.add(self.url_row)
        self.autoconnect_row = Adw.SwitchRow(
            title="Autoconnect", subtitle="Connect when opening app"
        )
        self.prefs_group.add(self.autoconnect_row)
        self.security_row = Adw.ActionRow(title="Security Status")
        self.security_row.add_suffix(sec_status_box)
        self.prefs_group.add(self.security_row)

        self.name_row.connect("changed", self.onSettingsChanged)
        self.desc_row.connect("changed", self.onSettingsChanged)
        self.url_row.connect("changed", self.onSettingsChanged)
        self.autoconnect_row.connect("notify::active", self.onSettingsChanged)

        self.prefs_group.add(deleteRow(self.onForgetClicked))

        self.__buildHypervisorInfo__()

        self.loadSettings()
        self.setStatus()
        self.refreshInfo()

    def __buildHypervisorInfo__(self):
        """Build the box with hypervisor info."""
        # Some hypervisor infos
        self.info_group = Adw.PreferencesGroup()
        self.prefs_page.add(self.info_group)
        self.info_group.set_title("Hypervisor Information")
        refresh_btn = Gtk.Button(
            icon_name="update-symbolic", css_classes=["flat"], tooltip_text="Refresh"
        )
        refresh_btn.connect("clicked", self.refreshInfo)
        self.info_group.set_header_suffix(refresh_btn)

        self.hostname_row = propertyRow("Hostname", subtitle="unavailable")
        self.info_group.add(self.hostname_row)

        self.max_vcpus_row = propertyRow("Available vCPUs", subtitle="unavailable")
        self.info_group.add(self.max_vcpus_row)

        self.max_mem_row = propertyRow("Available Memory", subtitle="unavailable")
        self.info_group.add(self.max_mem_row)

        self.emulator_path_row = propertyRow("Emulator Path", subtitle="unavailable")
        self.info_group.add(self.emulator_path_row)

        self.domain_type_row = propertyRow("Hypervisor Type", subtitle="unavailable")
        self.info_group.add(self.domain_type_row)

        self.machine_row = propertyRow("Machine Type", subtitle="unavailable")
        self.info_group.add(self.machine_row)

        self.arch_row = propertyRow("Architecture", subtitle="unavailable")
        self.info_group.add(self.arch_row)

        self.libvirt_ver_row = propertyRow("Libvirt Version", subtitle="unavailable")
        self.info_group.add(self.libvirt_ver_row)

        self.conn_ver_row = propertyRow("Hypervisor Version", subtitle="unavailable")
        self.info_group.add(self.conn_ver_row)

    def setStatus(self):
        """Update the status (icons and some buttons)."""
        state = self.parent.connection.getState()
        if state == CONNECTION_STATE_CONNECTED:
            self.security_row.set_visible(True)
            self.secure_icon.set_visible(self.parent.connection.isSecure())
            self.encrypted_icon.set_visible(self.parent.connection.isEncrypted())

            self.apply_row.setShowWarning(True)
            self.apply_row.setShowApply(False)
        elif state == CONNECTION_STATE_CONNECTING:
            self.security_row.set_visible(False)

            self.apply_row.setShowWarning(False)
            self.apply_row.setShowApply(True)
        else:
            self.security_row.set_visible(False)

            self.apply_row.setShowWarning(False)
            self.apply_row.setShowApply(True)

        self.refreshInfo()

    def loadSettings(self):
        """Load a connections settings."""
        self.name_row.set_text(self.parent.connection.name)
        self.desc_row.set_text(self.parent.connection.description)
        self.url_row.set_text(self.parent.connection.url)
        self.autoconnect_row.set_active(self.parent.connection.autoconnect)

    def refreshInfo(self, *_):
        """Refresh hypervisor info."""
        if not self.parent.connection.isConnected():
            self.info_group.set_visible(False)
            return

        self.info_group.set_visible(True)

        try:
            self.hostname_row.set_subtitle(str(self.parent.connection.hostname()))
        except:
            pass
        try:
            self.max_vcpus_row.set_subtitle(str(self.parent.connection.maxVCPUs()))
        except:
            pass
        try:
            self.max_mem_row.set_subtitle(
                bytesToString(self.parent.connection.maxMemory())
            )
        except:
            pass

        try:
            domain_caps = self.parent.connection.getDomainCapabilities()
            self.emulator_path_row.set_subtitle(domain_caps.emulator_path)
            self.domain_type_row.set_subtitle(domain_caps.domain)
            self.machine_row.set_subtitle(domain_caps.machine)
            self.arch_row.set_subtitle(domain_caps.arch)
        except:
            pass

        self.libvirt_ver_row.set_subtitle(
            str(self.parent.connection.getLibvirtVersion())
        )
        self.conn_ver_row.set_subtitle(
            str(self.parent.connection.getHypervisorVersion())
        )

    def onApplyClicked(self, _):
        """Apply was clicked."""
        new_settings = {
            "name": self.name_row.get_text(),
            "desc": self.desc_row.get_text(),
            "url": self.url_row.get_text(),
            "autoconnect": self.autoconnect_row.get_active(),
        }
        self.parent.connection.setSettings(new_settings)
        self.onSettingsChanged()

    def onSettingsChanged(self, *_):
        """Check if any settings differ from default, show apply button if necessary"""
        new_settings = {
            "name": self.name_row.get_text(),
            "desc": self.desc_row.get_text(),
            "url": self.url_row.get_text(),
            "autoconnect": self.autoconnect_row.get_active(),
        }
        self.apply_row.set_visible(new_settings != self.parent.connection.settings)

    def onForgetClicked(self, _):
        """Deletion was requested."""
        dialog = selectDialog(
            "Forget connection?",
            "Objects created on the hypervisor will not be affected",
            [
                ActionOption(
                    "Forget",
                    self.parent.connection.deleteConnection,
                    appearance=Adw.ResponseAppearance.DESTRUCTIVE,
                )
            ],
        )
        dialog.present(self.parent.window_ref.window)
