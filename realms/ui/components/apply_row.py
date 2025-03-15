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
"""Build the rows that pop up allowing to commit the changes."""

from gi.repository import Gtk

from realms.ui.components.common import iconButton, warningLabelRow
from realms.ui.components.preference_widgets import realmsClamp


class ApplyRow(Gtk.Box):
    """Row offering an apply and a reset option, and additionally
    presenting a warning."""

    def __init__(self, apply_cb: callable, cancel_cb: callable, warning: str):
        """Build an apply-row for preference pages. It offers the options
        to either apply changes or revert them.

        Args:
            apply_cb (callable): Callback when apply button is clicked
            cancel_cb (callable): Callback when cancel button is clicked
        """
        super().__init__(
            spacing=6,
            margin_top=6,
            margin_bottom=6,
            margin_start=6,
            margin_end=6,
            hexpand=True,
        )

        clamp = realmsClamp()
        self.append(clamp)
        box = Gtk.Box(spacing=6)
        clamp.set_child(box)

        self.warning = warningLabelRow(warning, "warning")
        self.warning.set_visible(False)
        box.append(self.warning)

        button = iconButton(
            "",
            "edit-undo-symbolic",
            cb=cancel_cb,
            tooltip_text="Revert",
            halign=Gtk.Align.END,
            hexpand=True,
        )
        box.append(button)

        self.apply_btn = iconButton(
            "Apply",
            "",
            cb=apply_cb,
            tooltip_text="Apply",
            css_classes=["suggested-action"],
            halign=Gtk.Align.END,
            hexpand=False,
        )
        box.append(self.apply_btn)

    def setShowWarning(self, visible: bool):
        """Set visibility of warning

        Args:
            visible (bool): Visibility
        """
        self.warning.set_visible(visible)

    def setShowApply(self, visible: bool):
        """Set visibility of apply button

        Args:
            visible (bool): Visibility
        """
        self.apply_btn.set_visible(visible)


class UpdateRow(Gtk.Box):
    """Bit more simple row offering an update and a reset option.
    The warning is always shown."""

    def __init__(self, update_cb: callable, cancel_cb: callable):
        """Build an update-row for preference pages

        Args:
            update_cb (callable): Callback when apply button is clicked
        """
        super().__init__(
            spacing=6,
            margin_top=6,
            margin_bottom=6,
            margin_start=6,
            margin_end=6,
            hexpand=True,
        )

        clamp = realmsClamp()
        self.append(clamp)
        box = Gtk.Box(spacing=6)
        clamp.set_child(box)

        self.warning = warningLabelRow("Changes apply immediately", "warning")
        box.append(self.warning)

        button = iconButton(
            "",
            "edit-undo-symbolic",
            cb=cancel_cb,
            tooltip_text="Revert",
            halign=Gtk.Align.END,
            hexpand=True,
        )
        box.append(button)

        self.update_btn = iconButton(
            "Update",
            "",
            cb=update_cb,
            tooltip_text="Apply",
            css_classes=["destructive-action"],
            halign=Gtk.Align.END,
            hexpand=False,
        )
        box.append(self.update_btn)
