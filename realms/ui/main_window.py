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
from gi.repository import Adw, Gio, GLib, Gtk

from realms.ui.components import iconButton
from realms.ui.connection_row import ConnectionRow
from realms.ui.tabs import BaseDetailsTab

from .dialogs.add_conn_dialog import AddConnDialog

(OVERLAY_NONE, OVERLAY_NO_CONN, OVERLAY_NO_TAB) = range(3)


class MainWindow(Adw.ApplicationWindow):
    """Main window class. It will only show the sidebar if it
    is the primary window."""

    def __init__(self, is_primary: bool):
        """Create an application window

        Args:
            is_primary (bool): Decide if this window is the primary window. Other windows will
                be closed when the primary window closes, and other windows will only show tabs,
                no sidebar.
        """
        super().__init__()

        self.is_primary = is_primary

        self.child = None
        self.nav_view = None
        self.main_nav_page = None
        self.sidebar_nav_page = None
        self.toast_overlay = None
        self.main_toolbar_view = None
        self.header = None
        self.main_area_overlay = None
        self.no_conns_status = None
        self.add_conn_button = None
        self.no_tabs_status = None
        self.tab_bar = None
        self.tab_view = None
        self.options_popover = None
        self.hamburger_button = None

        self.open_sidebar_btn = None
        self.sidebar_list_box = None

        self.overlay_status = OVERLAY_NO_CONN

        self.sidebar_children = {}  # Dict from URL to ListBoxRow
        self.open_tabs = []  # List with open tab pages

        self.toast_copy_action = Gio.SimpleAction(
            name="copy-toast", parameter_type=GLib.VariantType.new(type_string="s")
        )
        self.toast_copy_action.connect("activate", self.onToastCopied)
        self.add_action(self.toast_copy_action)

        self.build()

    def build(self):
        """Fill the main window with the core UI elements"""
        self.set_default_size(1600, 1200)
        self.set_title("Realms")
        self.connect("close-request", self.onWindowClosed)

        self.nav_view = Adw.OverlaySplitView(hexpand=True, vexpand=True)
        self.set_content(self.nav_view)

        self.main_nav_page = Adw.NavigationPage(
            title="Realms", hexpand=True, vexpand=True, css_classes=["view"]
        )
        self.nav_view.set_content(self.main_nav_page)

        self.sidebar_nav_page = Adw.NavigationPage(title="Realms")
        self.sidebar_nav_page.set_size_request(300, -1)
        self.nav_view.set_sidebar(self.sidebar_nav_page)

        self.toast_overlay = Adw.ToastOverlay(hexpand=True, vexpand=True)
        self.main_nav_page.set_child(self.toast_overlay)
        self.main_toolbar_view = Adw.ToolbarView(
            top_bar_style=Adw.ToolbarStyle.FLAT, hexpand=True, vexpand=True
        )
        self.toast_overlay.set_child(self.main_toolbar_view)

        # Main content (Up to AdwTabView)
        self.header = Adw.HeaderBar()
        self.main_toolbar_view.add_top_bar(self.header)

        # Hamburger menu
        self.buildHamburgerMenu()

        # Content of main page
        self.buildMainArea()

        # Sidebar stuff
        if self.is_primary:
            self.open_sidebar_btn = iconButton(
                "",
                "panel-left-symbolic",
                lambda *btn: self.nav_view.set_show_sidebar(
                    not self.nav_view.get_show_sidebar()
                ),
            )
            self.header.pack_start(self.open_sidebar_btn)

            scroll = Gtk.ScrolledWindow()
            self.sidebar_nav_page.set_child(scroll)

            self.sidebar_list_box = Gtk.ListBox(
                css_classes=["navigation-sidebar"],
                selection_mode=Gtk.SelectionMode.NONE,
            )
            scroll.set_child(self.sidebar_list_box)
        else:
            self.nav_view.set_show_sidebar(False)

        self.setOverlays()

    def buildHamburgerMenu(self):
        """Build the hamburger menu."""
        open_about_action = Gio.SimpleAction(name="open-about", parameter_type=None)
        open_about_action.connect("activate", self.onOpenAboutClicked)
        self.add_action(open_about_action)

        add_conn_action = Gio.SimpleAction(name="add-connection", parameter_type=None)
        add_conn_action.connect("activate", self.onAddConnClicked)
        self.add_action(add_conn_action)

        menu = Gio.Menu()
        menu.append("Add connection", "win.add-connection")
        menu.append("About", "win.open-about")

        self.options_popover = Gtk.PopoverMenu(menu_model=menu)

        self.hamburger_button = Gtk.MenuButton(
            popover=self.options_popover, icon_name="open-menu-symbolic"
        )
        self.header.pack_end(self.hamburger_button)

    def buildMainArea(self):
        """Build the content of the main area, mostly a bunch of overlays."""
        self.main_area_overlay = Gtk.Overlay(hexpand=True, vexpand=True)
        self.main_toolbar_view.set_content(self.main_area_overlay)

        self.tab_bar = Adw.TabBar(hexpand=True, autohide=False)
        self.main_toolbar_view.add_top_bar(self.tab_bar)

        self.tab_view = Adw.TabView(hexpand=True, vexpand=True)
        self.tab_bar.set_view(self.tab_view)
        self.tab_view.connect("close-page", self.onTabClosed)
        self.tab_view.connect("page-attached", self.onTabAttached)
        self.tab_view.connect("page-detached", self.onTabDetached)
        self.tab_view.connect("create-window", self.onCreateWindow)
        self.main_area_overlay.set_child(self.tab_view)

        if self.is_primary:
            self.no_conns_status = Adw.StatusPage(
                title="No connections",
                description="",
                vexpand=True,
                icon_name="offline-globe-symbolic",
                child=iconButton(
                    "Add connection",
                    "",
                    self.onAddConnClicked,
                    css_classes=["pill", "suggested-action"],
                    halign=Gtk.Align.CENTER,
                ),
            )

            self.main_area_overlay.add_overlay(self.no_conns_status)

        self.no_tabs_status = Adw.StatusPage(
            vexpand=True,
            icon_name="com.github.marreitin.realms",
            title="Realms",
        )
        self.main_area_overlay.add_overlay(self.no_tabs_status)

    def addConnection(self, conn: dict):
        """Add a connection to the sidebar

        Args:
            conn (dict): Connection dictionary from settings

        Raises:
            ValueError: If the new URL already is registered
        """
        url = conn["url"]
        if url in self.sidebar_children:
            raise ValueError("URL already exists")

        row = ConnectionRow(conn, self)
        index = len(self.sidebar_children)
        self.sidebar_list_box.insert(row, index)
        self.sidebar_children[url] = row

        self.overlay_status = OVERLAY_NONE if self.open_tabs else OVERLAY_NO_TAB
        self.setOverlays()

    def removeConnection(self, url: str):
        """Remove a connection

        Args:
            url (str): The connections URL
        """
        row = self.sidebar_children[url]
        self.sidebar_list_box.remove(row)
        del self.sidebar_children[url]

        if len(self.sidebar_children) == 0:
            self.overlay_status = OVERLAY_NO_CONN
        else:
            self.overlay_status = OVERLAY_NONE if self.open_tabs else OVERLAY_NO_TAB
        self.setOverlays()

    def updateConnectionURL(self, old_url: str, new_url: str):
        """Change a connections URL

        Args:
            old_url (str): Old URL
            new_url (str): New URL

        Raises:
            ValueError: If the new URL already is registered
        """
        if old_url == new_url:
            return

        if new_url in self.sidebar_children:
            raise ValueError("URL already exists")

        print(self.sidebar_children)
        self.sidebar_children[new_url] = self.sidebar_children[old_url]
        del self.sidebar_children[old_url]

    def tabExists(self, uuid: str) -> bool:
        """Check if a tab is already open

        Args:
            uuid (str): The tabs unique identifier

        Returns:
            bool: If it already exists
        """
        for page in self.open_tabs:
            if page.get_child().getUniqueIdentifier() == uuid:
                self.tab_view.set_selected_page(page)
                return True
        return False

    def addOrShowTab(self, content: BaseDetailsTab, title: str, icon_name: str) -> None:
        """Add a new tab. Use self.tabExists to check if the tab is already open
        before opening it

        Args:
            content (Gtk.Widget): Content of the new tab
            title (str): Any title for the tab
            icon (str): Any icon for the tab
        """
        uuid = content.getUniqueIdentifier()
        if self.tabExists(uuid):
            raise ValueError  # Remove eventually for the sake of efficiency

        tab_page = self.tab_view.append(content)
        tab_page.set_title(title)
        icon = Gio.ThemedIcon.new_from_names([icon_name])
        tab_page.set_icon(icon)
        self.tab_view.set_selected_page(tab_page)

        self.overlay_status = OVERLAY_NONE
        self.setOverlays()

    def onWindowClosed(self, *_):
        """When this window closes, close all tabs."""
        for tab in self.open_tabs:
            tab.get_child().end()
        self.get_application().onWindowClosed(self)

    def onTabClosed(self, _, tab_page):
        """Is called when the tab closes. It ends the page inside."""
        tab_page.get_child().end()

        if len(self.open_tabs) == 0:
            self.overlay_status = OVERLAY_NO_TAB
            self.setOverlays()

    def onTabAttached(self, tab_view, tab_page, pos):
        """Add tab was dragged into this window."""
        for page in self.open_tabs:
            if (
                page.get_child().getUniqueIdentifier()
                == tab_page.get_child().getUniqueIdentifier()
            ):
                tab_view.close_page(tab_page)
                return

        self.tab_view.set_selected_page(tab_page)
        self.open_tabs.insert(pos, tab_page)
        tab_page.get_child().setWindow(self)

        self.overlay_status = OVERLAY_NONE
        self.setOverlays()

    def onTabDetached(self, _, tab_page, pos):
        """A tab was detached from this window."""
        # The page might not be in there if page attachment was refused.
        if tab_page in self.open_tabs:
            self.open_tabs.remove(tab_page)

        # Secondary windows should close when they don't have any tabs.
        if len(self.open_tabs) == 0 and not self.is_primary:
            self.close()
        elif len(self.open_tabs) == 0:
            self.overlay_status = (
                OVERLAY_NO_TAB if len(self.sidebar_children) else OVERLAY_NO_CONN
            )
            self.setOverlays()

    def onCreateWindow(self, _):
        """A new window was created"""
        win = self.get_application().addWindow(False)
        return win.tab_view

    def onAddConnClicked(self, *_):
        """Open the dialog to add a connection."""
        AddConnDialog(self)

    def onOpenAboutClicked(self, *_):
        """Open the about dialog."""
        about = Adw.AboutDialog(
            application_icon="com.github.marreitin.realms",
            application_name="Realms",
            comments="An incomplete libvirt client for the modern GNOME desktop",
            developers=["marreitin"],
            version="20240130",
            license_type=Gtk.License.GPL_3_0,
            website="https://github.com/marreitin/realms",
            issue_url="https://github.com/marreitin/realms/issues",
        )
        about.present(self)

    def closeTab(self, child: Gtk.Widget):
        """User requested to close a tab."""
        page = self.tab_view.get_page(child)
        self.tab_view.close_page(page)

    def pushToastText(
        self, text: str, timeout=5, priority=Adw.ToastPriority.NORMAL
    ) -> None:
        """Push a toast into this window

        Args:
            text (str): The message to display
            timeout (int, optional): Timeout. Defaults to 5.
            priority (_type_, optional): Priority for toast ordering. Defaults to Adw.ToastPriority.NORMAL.
        """
        toast = Adw.Toast(
            title=text,
            timeout=timeout,
            priority=priority,
            button_label="Copy",
            action_name="win.copy-toast",
            action_target=GLib.Variant.new_string(text),
            use_markup=False,
        )
        self.toast_overlay.add_toast(toast)

    def onToastCopied(self, _: Gio.SimpleAction, variant: GLib.Variant):
        """The message on the toast was copied."""
        text = variant.get_string()
        clipboard = self.get_clipboard()
        clipboard.set(text)

    def setOverlays(self):
        """Depending on the current state, set the overlayed status boxes

        Raises:
            Exception: On invalid state
        """
        if self.is_primary:
            self.nav_view.set_show_sidebar(True)
            self.open_sidebar_btn.set_visible(True)

        if self.overlay_status == OVERLAY_NONE:
            if self.is_primary:
                self.no_conns_status.set_visible(False)
            self.no_tabs_status.set_visible(False)

        elif self.overlay_status == OVERLAY_NO_TAB:
            if self.is_primary:
                self.no_conns_status.set_visible(False)
            self.no_tabs_status.set_visible(True)

        elif self.overlay_status == OVERLAY_NO_CONN and self.is_primary:
            self.nav_view.set_show_sidebar(False)
            self.open_sidebar_btn.set_visible(False)

            if self.is_primary:
                self.no_conns_status.set_visible(True)
            self.no_tabs_status.set_visible(False)

        elif self.overlay_status == OVERLAY_NO_CONN:
            pass  # Nothing happens as the window will close anyway.

        else:
            raise NotImplementedError("This should not be reached")
