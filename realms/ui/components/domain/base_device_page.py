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

from realms.ui.components.apply_row import UpdateRow
from realms.ui.components.domain.domain_page_host import DomainPageHost
from realms.ui.components.preference_widgets import RealmsPreferencesPage


class BaseDevicePage:
    def __init__(
        self,
        parent: DomainPageHost,
        xml_tree: ET.Element,
        use_for_adding=False,
        can_update=False,
    ):
        """Create a device page

        Args:
            parent (DomainDetailsTab): Parent of self
            xml_tree (ET.Element): XML tree of this page
            use_for_adding (bool, optional): Don't show some elements if this page is used for
            adding a device. Defaults to False.
            can_update (bool, optional): Wheter this page can make use of live
            updating. Defaults to False.
        """
        self.parent = parent
        self.xml_tree = xml_tree
        self.use_for_adding = use_for_adding
        self.can_update = can_update

        self.prefs_page = None
        self.nav_page = None
        self.update_row = None

        self.__changed__ = False

    def updateData(self):
        """Must be implemented."""
        raise NotImplementedError

    def setXML(self, xml_tree: ET.Element):
        """Update the xml data. Doesn't trigger a rebuild."""
        self.xml_tree = xml_tree
        self.__changed__ = False

    def buildFull(self):
        """Build the entire navigation page; only after this the nav_page
        attribute will actually be a Adw.NavigationPage. This is important
        to make the UI more responsive.
        """
        self.prefs_page = RealmsPreferencesPage(clamp=not self.use_for_adding)

        if not self.use_for_adding:
            self.nav_page = Adw.NavigationPage(title="asd")

            toolbar_view = Adw.ToolbarView()
            self.nav_page.set_child(toolbar_view)

            toolbar_view.set_content(self.prefs_page)

            self.update_row = UpdateRow(
                self.applyUpdate, lambda *_: self.parent.updateData()
            )
            self.update_row.set_visible(False)
            toolbar_view.add_bottom_bar(self.update_row)

        if self.__changed__:
            self.showApply()

        self.build()

    def build(self):
        """To be implemented."""
        raise NotImplementedError

    def showApply(self, *_):
        """Show the apply button or the update row."""
        self.__changed__ = True
        if self.use_for_adding:
            return
        if self.can_update:
            self.update_row.set_visible(True)
            self.parent.onDefinitionChanged()
        else:
            self.parent.onDefinitionChanged()

    def setCanUpdate(self, can_update):
        """Set whether this page offers the update option. When allowing updates,
        it additionally makes sure that, in case a setting was changed, the update
        row appears."""
        self.can_update = can_update

        if not self.can_update and self.update_row is not None:
            self.update_row.set_visible(False)
        elif self.can_update and self.update_row is not None:
            self.update_row.set_visible(self.__changed__)

    def getTitle(self) -> str:
        """Get a human-readable title of the device."""
        raise NotImplementedError

    def getDescription(self) -> str:
        """Get a human-readable description of the device."""
        raise NotImplementedError

    def getIconName(self) -> str:
        """Get the name of a fitting icon of the device."""
        raise NotImplementedError

    def deleteDevice(self, *_):
        """The delete button was clicked."""
        self.parent.deleteDevice(self)

    def applyUpdate(self, *_):
        """The update button was clicked."""
        try:
            self.parent.onDeviceUpdate(self.xml_tree)
            self.__changed__ = False
            self.parent.updateData()
        except Exception as e:
            self.parent.window_ref.window.pushToastText(str(e))
