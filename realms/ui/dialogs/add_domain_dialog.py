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

from gi.repository import Adw, Gio, Gtk
from jinja2 import Environment

from realms.helpers import stringToBytes
from realms.helpers.templates import TemplateManager
from realms.libvirt_wrap import Connection
from realms.libvirt_wrap.constants import *
from realms.ui.components import (
    GenericPreferencesRow,
    hspacer,
    iconButton,
    propertyRow,
    sourceViewGetText,
    xmlSourceView,
)
from realms.ui.components.common import simpleErrorDialog
from realms.ui.components.network_chooser import NetworkChooserRow
from realms.ui.components.preference_widgets import RealmsPreferencesPage
from realms.ui.components.volume_chooser import VolumeChooser


class SettingsField:
    def __init__(self, parent, settings_dict: dict):
        self.parent = parent
        self.settings_dict = settings_dict

    def getWidget(self):
        """Return the widget for this setting."""
        raise NotImplementedError

    def submit(self) -> dict:
        """Returns dictionary with variables set to values."""
        raise NotImplementedError


class StrRow(SettingsField):
    def __init__(self, parent, settings_dict: dict):
        super().__init__(parent, settings_dict)

        self.row = Adw.EntryRow(title=self.settings_dict["name"])

    def getWidget(self):
        return self.row

    def submit(self):
        return {self.settings_dict["output"]["value"]: self.row.get_text()}


class IntRow(SettingsField):
    def __init__(self, parent, settings_dict: dict):
        super().__init__(parent, settings_dict)

        min_val = self.settings_dict["params"]["min"]
        max_val = self.settings_dict["params"]["max"]
        self.row = Adw.SpinRow(
            title=self.settings_dict["name"],
            adjustment=Gtk.Adjustment(lower=min_val, step_increment=1, upper=max_val),
            digits=0,
            value=min_val,
        )

    def getWidget(self):
        return self.row

    def submit(self):
        return {self.settings_dict["output"]["value"]: int(self.row.get_value())}


class ListRow(SettingsField):
    def __init__(self, parent, settings_dict: dict):
        super().__init__(parent, settings_dict)

        self.row = Adw.ComboRow(
            title=self.settings_dict["name"],
            model=Gtk.StringList(strings=self.settings_dict["params"]["selection"]),
        )

    def getWidget(self):
        return self.row

    def submit(self):
        return {
            self.settings_dict["output"]["value"]: self.settings_dict["params"][
                "selection"
            ][self.row.get_selected()]
        }


class DataRow(SettingsField):
    def __init__(self, parent, settings_dict: dict):
        super().__init__(parent, settings_dict)

        self.row = Adw.EntryRow(title=self.settings_dict["name"])

        self.row.connect("changed", self.__onChanged__)

    def __onChanged__(self, *_):
        self.row.set_css_classes([])
        try:
            stringToBytes(self.row.get_text())
        except:
            self.row.set_css_classes(["error"])

    def getWidget(self):
        return self.row

    def submit(self):
        return {
            self.settings_dict["output"]["value"]: stringToBytes(self.row.get_text())
        }


class FileRow(SettingsField):
    def __init__(self, parent, settings_dict: dict):
        super().__init__(parent, settings_dict)

        self.row = Adw.EntryRow(title=self.settings_dict["name"])

        self.open_dialog = None
        if parent.connection.is_local:
            self.open_dialog = Gtk.FileDialog.new()
            self.open_dialog.set_title("Select a File")

            self.browse_btn = iconButton(
                "",
                "inode-directory-symbolic",
                self.__onBrowseClicked__,
                css_classes=["flat"],
                tooltip_text="Browse local paths",
            )
            self.row.add_suffix(self.browse_btn)

    def __onBrowseClicked__(self, _):
        self.browse_btn.set_sensitive(False)
        self.open_dialog.open(None, None, self.__onFileDialogCB__)

    def __onFileDialogCB__(self, dialog, result):
        self.browse_btn.set_sensitive(True)
        try:
            file = dialog.open_finish(result)
            if file is not None:
                self.row.set_text(file.get_path())
        except:
            pass

    def getWidget(self):
        return self.row

    def submit(self):
        return {self.settings_dict["output"]["value"]: self.row.get_text()}


class CreateVolRow(SettingsField):
    """Row to create a virtual volume when creating
    a domain."""

    def __init__(self, parent, settings_dict: dict):
        super().__init__(parent, settings_dict)

        self.row = GenericPreferencesRow()

        box = Gtk.Box(spacing=6)
        box.append(Gtk.Label(label=self.settings_dict["name"]))
        box.append(hspacer())
        self.row.addChild(box)

        self.chooser = VolumeChooser(
            self.parent.window, self.parent.connection, lambda: None
        )
        self.row.addChild(self.chooser)

    def getWidget(self):
        return self.row

    def submit(self) -> dict:
        data = {
            self.settings_dict["output"]["pool"]: self.chooser.getPool().name(),
            self.settings_dict["output"]["volume"]: self.chooser.getVolume().name(),
        }

        return data


class NetworkRow(SettingsField):
    """Row to select a virtual network when creating
    a domain."""

    def __init__(self, parent, settings_dict: dict):
        super().__init__(parent, settings_dict)

        self.row = NetworkChooserRow(
            self.parent.connection, lambda: None, title=self.settings_dict["name"]
        )

    def getWidget(self):
        """Return the widget for this setting."""
        return self.row

    def submit(self) -> dict:
        """Returns dictionary with variables set to values."""
        return {self.settings_dict["output"]["network"]: self.row.getNetwork().name()}


class SettingsPage(Adw.NavigationPage):
    def __init__(self, parent, template_data: dict):
        super().__init__(title="fields-page")

        self.parent: AddDomainDialog = parent
        self.template_data = template_data
        self.rows = []

        page = RealmsPreferencesPage(clamp=False)
        self.set_child(page)

        self.group = Adw.PreferencesGroup(title="Template settings")
        page.add(self.group)

        self.__buildFields__()

    def __buildFields__(self):
        if "settings" not in self.template_data:
            return

        settings = self.template_data["settings"]
        for s in settings:
            row = None
            if s["type"] == "str":
                row = StrRow(self.parent, s)
            elif s["type"] == "int":
                row = IntRow(self.parent, s)
            elif s["type"] == "list":
                row = ListRow(self.parent, s)
            elif s["type"] == "data":
                row = DataRow(self.parent, s)
            elif s["type"] == "file":
                row = FileRow(self.parent, s)
            elif s["type"] == "volume":
                row = CreateVolRow(self.parent, s)
            elif s["type"] == "network":
                row = NetworkRow(self.parent, s)
            else:
                raise NotImplementedError("This setting type is not implemented")
            self.rows.append(row)
            self.group.add(row.getWidget())

    def submit(self) -> dict:
        """Run actions and create dict with variables for templating domain xml

        Returns:
            dict: Variables created by pre-actions-page
        """
        variables = {}
        for row in self.rows:
            variables |= row.submit()
        return variables


class AddDomainDialog:
    """Dialog for adding a domain."""

    def __init__(self, window: Adw.ApplicationWindow, connection: Connection):
        super().__init__()

        self.window = window
        self.connection = connection

        self.templates = TemplateManager.listTemplatesAll()

        self.settings_page = None

        self.connection.registerCallback(self.__onConnectionEvent__)

        self.__build__()

    def __build__(self):
        # Create a Builder
        self.builder = Gtk.Builder.new_from_resource(
            "/com/github/marreitin/realms/gtk/adddom.ui"
        )

        # Obtain and show the main window
        self.dialog = self.__obj__("main-dialog")
        self.dialog.connect("closed", self.__onDialogClosed__)
        self.dialog.present(self.window)

        group = Adw.PreferencesGroup()
        self.__obj__("status-page").set_child(group)
        self.template_row = Adw.ComboRow(
            title="Pick a template",
            model=Gtk.StringList(strings=[t["name"] for t in self.templates]),
        )
        self.template_row.connect("notify::selected", self.__onTemplateSelected__)
        group.add(self.template_row)

        self.template_desc_row = propertyRow("Template description")
        self.template_desc_row.add_prefix(
            Gtk.Image.new_from_gicon(
                Gio.ThemedIcon.new_from_names(["info-outline-symbolic"])
            )
        )
        group.add(self.template_desc_row)

        if len(self.templates) == 0:
            self.template_desc_row.set_subtitle("No templates found")

        self.__obj__("btn-next").connect("clicked", self.__onNextClicked__)
        self.__obj__("btn-back").connect("clicked", self.__onBackClicked__)
        self.__obj__("btn-finish").connect("clicked", self.__onApplyClicked__)

        self.__obj__("nav-view").connect("popped", self.__onNavPopped__)

        self.xml_view = xmlSourceView()
        self.__obj__("xml-box").append(self.xml_view)

        self.__obj__("main-stack").connect(
            "notify::visible-child", self.__onStackChanged__
        )

        self.__setControlButtonStates__()
        self.__onTemplateSelected__()

    def __setControlButtonStates__(self):
        """Set the control buttons in the header bar, depending
        on the current state."""
        name = self.__obj__("main-stack").get_visible_child_name()
        if name == "guided":
            if self.settings_page is None:
                self.__obj__("btn-back").set_visible(False)
                self.__obj__("btn-next").set_visible(True)
                self.__obj__("btn-finish").set_visible(False)
            else:
                self.__obj__("btn-back").set_visible(True)
                self.__obj__("btn-next").set_visible(False)
                self.__obj__("btn-finish").set_visible(True)
        else:
            self.__obj__("btn-back").set_visible(False)
            self.__obj__("btn-next").set_visible(False)
            self.__obj__("btn-finish").set_visible(True)

    def __onTemplateSelected__(self, *_):
        """A template was selected, show it's description."""
        if len(self.templates) == 0:
            return
        selected_template = self.templates[self.template_row.get_selected()]
        if "description" in selected_template:
            self.template_desc_row.set_visible(True)
            self.template_desc_row.set_subtitle(selected_template["description"])
        else:
            self.template_desc_row.set_visible(False)

    def __onNextClicked__(self, _):
        """Show the settings for the selected template."""
        selected_template = self.templates[self.template_row.get_selected()]

        self.settings_page = SettingsPage(self, selected_template)
        self.__obj__("nav-view").push(self.settings_page)
        self.__setControlButtonStates__()

    def __onBackClicked__(self, *_):
        self.__obj__("nav-view").pop()

    def __onNavPopped__(self, *_):
        self.settings_page = None
        self.__setControlButtonStates__()

    def __onApplyClicked__(self, _):
        """Either directly try to define the domain from the given XML
        when the XML editor was used, otherwise collect all settings,
        run jinja and then try to define the domain."""
        try:
            xml = ""
            if self.__obj__("main-stack").get_visible_child_name() == "xml":
                xml = sourceViewGetText(self.xml_view)
            else:
                variables = self.settings_page.submit()

                # Template xml
                selected_template = self.templates[self.template_row.get_selected()]
                template = selected_template["template"]
                env = Environment()
                temp = env.from_string(template)
                xml = temp.render(**variables)
            print(xml)

            self.connection.addDomain(xml)
            self.dialog.close()
        except Exception as e:
            traceback.print_exc()
            simpleErrorDialog("Invalid settings", str(e), self.window)

    def __onStackChanged__(self, *_):
        # XML preview is not really possible
        self.__setControlButtonStates__()

    def __obj__(self, name: str):
        o = self.builder.get_object(name)
        if o is None:
            raise NotImplementedError(f"Object { name } could not be found!")
        return o

    def __onConnectionEvent__(self, conn, obj, type_id, event_id, detail_id):
        if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.dialog.close()

    def __onDialogClosed__(self, *_):
        self.connection.unregisterCallback(self.__onConnectionEvent__)
