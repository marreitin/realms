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
"""A collection of useful widgets."""

from gi.repository import Adw, Gtk


def iconButton(
    label: str,
    icon_name: str,
    cb: callable = None,
    hexpand=False,
    vexpand=False,
    **kwargs
) -> Gtk.Button:
    """Create a nice button with an icon

    Args:
        label (str): label text
        icon_name (str): Icon name
        cb (callable): Clicked callback
        kwargs: Any other arguments for the button

    Returns:
        Gtk.Button: Button
    """
    button = Gtk.Button(
        hexpand=hexpand, vexpand=vexpand, valign=Gtk.Align.BASELINE_CENTER, **kwargs
    )
    if label == "":
        button.set_icon_name(icon_name)
    elif icon_name == "":
        button.set_label(label)
    else:
        content = Adw.ButtonContent()
        content.set_label(label)
        content.set_icon_name(icon_name)
        button.set_child(content)

    if cb is not None:
        button.connect("clicked", cb)
    return button


def splitIconButton(label: str, icon_name: str, **kwargs) -> Gtk.Button:
    """Create a nice splitbutton with an icon

    Args:
        label (str): label text
        icon_name (str): Icon name
        kwargs: Any other arguments for the button

    Returns:
        Gtk.Button: Button
    """
    button = Adw.SplitButton(
        hexpand=False, vexpand=False, valign=Gtk.Align.BASELINE_CENTER, **kwargs
    )
    if label == "":
        button.set_icon_name(icon_name)
    else:
        content = Adw.ButtonContent()
        content.set_label(label)
        content.set_icon_name(icon_name)
        button.set_child(content)
    return button


def propertyRow(title: str, **kwargs) -> Adw.ActionRow:
    """Generate a property row

    Args:
        title (str): Title string

    Returns:
        Adw.ActionRow: Generated action row
    """
    row = Adw.ActionRow(
        title=title, css_classes=["property"], subtitle_selectable=True, **kwargs
    )

    return row


def warningLabelRow(
    warning: str, color: str = None, margin: int = 0, icon="dialog-warning-symbolic"
) -> Gtk.Box:
    """Generate a row that display a warning.

    Args:
        warning (str): Warning message
        color (str, optional): Optional color string. Defaults to None.
        margin (int, optional): Additional margin. Defaults to 0.
        icon (str, optional): Optional icon name. Defaults to "dialog-warning-symbolic".

    Returns:
        Gtk.Box: _description_
    """
    box = Gtk.Box(
        spacing=6,
        hexpand=True,
        vexpand=False,
        margin_top=margin,
        margin_bottom=margin,
        margin_start=margin,
        margin_end=margin,
    )

    icon = Gtk.Image.new_from_icon_name(icon)
    if color:
        icon.set_css_classes([color])
    box.append(icon)

    label = Gtk.Label(
        label=warning, tooltip_text=warning, valign=Gtk.Align.BASELINE_CENTER, wrap=True
    )
    box.append(label)

    return box


def hspacer() -> Gtk.Separator:
    """Horizontal spacer, taking up as much space
    as it can."""
    spacer = Gtk.Separator()
    spacer.set_css_classes(["spacer"])
    spacer.set_hexpand(True)
    spacer.set_vexpand(False)
    return spacer


def vspacer() -> Gtk.Separator:
    """Vertical spacer, taking up as much space
    as it can."""
    spacer = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
    spacer.set_css_classes(["spacer"])
    spacer.set_hexpand(False)
    spacer.set_vexpand(True)
    return spacer


def simpleErrorDialog(header: str, msg: str, window: Adw.ApplicationWindow) -> None:
    """Generate and show a simple error dialog

    Args:
        header (str): Header text
        msg (str): Message text
        window (Adw.ApplicationWindow): Window to show it in
    """
    alert_dialog = Adw.AlertDialog(heading=header, body=msg)
    alert_dialog.add_response("0", "Ok")
    alert_dialog.connect("response", lambda *args: [])
    alert_dialog.present(window)
