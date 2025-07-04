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
"""Methods to build the xml views."""

from gi.repository import Adw, Gio, GLib, Gtk, GtkSource

from realms.ui.components.common import addShortcut, iconButton

language_manager = GtkSource.LanguageManager()


def xmlSourceView(buffer_changed_cb: callable = None) -> GtkSource.View:
    """Build a simple box to display and edit XML.

    Args:
        buffer_changed_cb (callable, optional): Callback on buffer change. Defaults to None.

    Returns:
        GtkSource.View: The widget.
    """
    source_view = GtkSource.View(
        hexpand=True,
        vexpand=True,
        css_classes=["flat", "monospace"],
        show_line_numbers=True,
        indent_width=2,
        auto_indent=True,
        buffer=GtkSource.Buffer(
            language=language_manager.get_language("xml"),
            highlight_syntax=True,
            enable_undo=True,
        ),
    )

    # Make the SourceView follow system style.
    def setStyle(mgr, *_):
        style_manager = GtkSource.StyleSchemeManager.get_default()
        buffer = source_view.get_buffer()
        if mgr.get_dark():
            buffer.set_style_scheme(style_manager.get_scheme("Adwaita-dark"))
        else:
            buffer.set_style_scheme(style_manager.get_scheme("Adwaita"))

    def onSourceViewUnmap(mgr):
        mgr.disconnect_by_func(setStyle)

    app_style_manager = Adw.StyleManager.get_default()
    setStyle(app_style_manager)
    app_style_manager.connect("notify::dark", setStyle)
    source_view.connect("destroy", lambda *x: onSourceViewUnmap(app_style_manager))

    buffer = source_view.get_buffer()
    if buffer_changed_cb is not None:
        buffer.connect("changed", buffer_changed_cb)

    return source_view


def sourceViewGetText(source_view: GtkSource.View) -> str:
    """Get the text out of a GTK source-view."""
    buffer = source_view.get_buffer()
    return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)


def sourceViewSetText(source_view: GtkSource.View, text: str):
    """Set the text of a GTK source-view."""
    buffer = source_view.get_buffer()
    buffer.set_text(text)


class XMLView(Gtk.Box):
    """A complete xml view that additionally offers loading and
    storing XML files, as well as handling live changes.
    """

    def __init__(self, show_apply_cb):
        super().__init__()
        self.show_apply_cb = show_apply_cb

        self.source_view = None
        self.save_btn = None
        self.open_btn = None
        self.search_revealer = None
        self.search_entry = None
        self.search_settings = None
        self.search_context = None

        self.build()

    def build(self):
        """Build this widget."""
        self.set_hexpand(True)
        self.set_vexpand(True)

        overlay = Gtk.Overlay()
        self.append(overlay)

        scrolled = Gtk.ScrolledWindow(
            hexpand=True,
            vexpand=True,
            margin_bottom=12,
            margin_top=12,
            margin_start=12,
            margin_end=12,
        )
        overlay.set_child(scrolled)

        self.source_view = xmlSourceView()

        scrolled.set_child(self.source_view)

        buffer = self.source_view.get_buffer()
        buffer.connect("changed", self.__onEntryChanged__)

        self.search_settings = GtkSource.SearchSettings()
        self.search_context = GtkSource.SearchContext(
            buffer=buffer, settings=self.search_settings
        )

        controls_box = Gtk.Box(
            halign=Gtk.Align.END,
            valign=Gtk.Align.START,
            css_classes=["linked"],
            margin_end=24,
            margin_top=18,
        )
        overlay.add_overlay(controls_box)

        self.open_btn = iconButton(
            "", "document-open-symbolic", self.__onLoad__, tooltip_text="Open"
        )
        controls_box.append(self.open_btn)

        self.save_btn = iconButton(
            "", "document-save-symbolic", self.__onSave__, tooltip_text="Save"
        )
        controls_box.append(self.save_btn)

        search_btn = iconButton(
            "", "edit-find-symbolic", self.__onSearch__, tooltip_text="Search"
        )
        controls_box.append(search_btn)

        self.search_revealer = Gtk.Revealer(
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.START,
            hexpand=False,
            vexpand=False,
        )
        overlay.add_overlay(self.search_revealer)
        search_box = Gtk.Box(
            margin_top=18,
            css_classes=["linked"],
        )
        self.search_revealer.set_child(search_box)

        self.search_entry = Gtk.Entry(width_request=120, placeholder_text="Search")
        self.search_entry.connect("changed", self.__searchEntryChanged__)
        search_box.append(self.search_entry)

        close_search_btn = iconButton(
            "",
            "cross-small-symbolic",
            self.__hideSearch__,
            tooltip_text="Close",
        )
        search_box.append(close_search_btn)

        addShortcut(self.source_view, "<Control>f", self.__onSearch__)
        addShortcut(self.source_view, "<Control>s", self.__onSave__)
        addShortcut(self.source_view, "<Control>o", self.__onLoad__)
        addShortcut(
            self.source_view,
            "Escape",
            self.__hideSearch__,
        )

    def setText(self, text: str):
        """Set the text content."""
        sourceViewSetText(self.source_view, text)

    def getText(self) -> str:
        """Get the current text content."""
        return sourceViewGetText(self.source_view)

    def __onLoad__(self, *_):
        """The button to load xml was clicked."""

        def onOpen(dialog, result):
            try:
                file = dialog.open_finish(result)
            except Exception:
                return

            if file is None:
                return

            try:
                path = file.get_path()
                with open(path, "r") as f:
                    sourceViewSetText(self.source_view, f.read())
            except Exception:
                pass

        dialog = Gtk.FileDialog(title="Load XML")
        dialog.open(None, None, onOpen)

    def __onSave__(self, *_):
        """The button to save the XML was clicked."""

        def onWriteDone(stream, result):
            success = stream.write_bytes_finish(result)
            stream.close()
            if not success:
                raise Exception("Failed to write file.")

        def onSaved(dialog, result):
            try:
                file = dialog.save_finish(result)
            except Exception:
                return

            if file is None:
                return

            if file.query_exists():
                stream = file.replace(None, False, Gio.FileCreateFlags.PRIVATE, None)
            else:
                stream = file.create(Gio.FileCreateFlags.PRIVATE, None)

            stream.write_bytes_async(
                GLib.Bytes.new(bytearray(self.getText().encode())),
                0,
                None,
                callback=onWriteDone,
            )

        dialog = Gtk.FileDialog(
            title="Save XML",
            default_filter=Gtk.FileFilter(mime_types=["application/xml"]),
        )
        dialog.save(None, None, onSaved)

    def __onSearch__(self, *_):
        self.search_revealer.set_reveal_child(True)

        if self.search_revealer.get_reveal_child:
            self.search_entry.grab_focus()

    def __hideSearch__(self, *_):
        self.search_revealer.set_reveal_child(False)
        self.search_entry.set_text("")
        self.search_settings.set_search_text(None)
        self.source_view.grab_focus()

    def __searchEntryChanged__(self, *_):
        self.search_settings.set_search_text(self.search_entry.get_text())

    def __onEntryChanged__(self, *_):
        """The text was edited."""
        self.show_apply_cb()
