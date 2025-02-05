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
from gi.repository import Adw


class ActionOption:
    """Class to hold an action that can be shown in a selectDialog. Exists
    only so dialogs can be made more generic.
    """

    def __init__(
        self,
        title: str,
        selected_cb: callable,
        selected_cb_args: list = None,
        appearance: Adw.ResponseAppearance = Adw.ResponseAppearance.DEFAULT,
    ):
        """Create an ActionOption

        Args:
            title (str): What the action is called and what is shows up as.
                         Must be unique for this dialog.
            selected_cb (callable): Callback to call when this action was selected.
            selected_cb_args (list, optional): Calls selected_cb with these arguments.
            appearance (Adw.ResponseAppearance, optional): Optional response appearance.
        """
        self.title = title
        self.selected_cb = selected_cb
        self.selected_cb_args = selected_cb_args
        if selected_cb_args is None:
            self.selected_cb_args = []
        self.appearance = appearance

    def _callback(self):
        """The option was selected"""
        self.selected_cb(*self.selected_cb_args)


def selectDialog(
    heading: str, body: str, actions: list[ActionOption], show_cancel=True
) -> Adw.AlertDialog:
    """Create an alert dialog with the given options

    Args:
        heading (str): Dialog title
        body (str): Dialog body (descriptive text)
        actions (list[ActionOption]): List of actions to present.
        An action to close the dialog will be added automatically.

    Returns:
        Adw.AlertDialog: The dialog. It is not shown, only created.
    """
    if show_cancel:
        actions.insert(0, ActionOption("Cancel", lambda: []))

    def onResponse(_, resp_id):
        if resp_id == "Cancel":
            return  # Nothing was selected
        for action in actions:
            if action.title == resp_id:
                action._callback()
                break

    dialog = Adw.AlertDialog(heading=heading, body=body)
    dialog.connect("response", onResponse)

    for action in actions:
        dialog.add_response(action.title, action.title)
        dialog.set_response_appearance(action.title, action.appearance)

    if show_cancel:
        dialog.set_default_response("Cancel")

    return dialog
