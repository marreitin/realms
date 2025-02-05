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
"""Bindable widgets that directly take over an
element in a xml tree, setting it's value.

Important: Use *.getWidget() to get the actual widget,
since not all bindable widgets can make use of inheritance.
"""

import xml.etree.ElementTree as ET

from gi.repository import Adw, Gtk

from realms.helpers import getETText


class BindableEntryRow(Adw.EntryRow):
    """Adwaita EntryRow that can be bound to a xml tag's text or an attribute."""

    def __init__(self, *args, **kwargs):
        """Create row"""
        super().__init__(*args, **kwargs)

        self.elem = None
        self.attr = None
        self.changed_cb = None
        self.in_trans = None
        self.out_trans = None
        self.connect("changed", self.__onChanged__)

    def getWidget(self):
        """Get this widget"""
        return self

    def unbind(self):
        """Remove any bindings"""
        self.elem = None
        self.attr = None
        self.changed_cb = None
        self.in_trans = None
        self.out_trans = None

    def bindText(
        self,
        elem: ET.Element,
        changed_cb: callable = None,
        in_trans: callable = None,
        out_trans: callable = None,
    ):
        """Bind this entry to text property

        Args:
            elem (ET.Element): XML element
            changed_cb (callable): Call when changed
            in_trans (callable): Transform input to text
            out_trans (callable): Transform text to output
        """
        self.unbind()

        self.in_trans = in_trans
        self.out_trans = out_trans
        if self.in_trans is None:
            self.in_trans = lambda x: x
        if self.out_trans is None:
            self.out_trans = lambda x: x

        self.set_text(self.out_trans(getETText(elem)))
        self.elem = elem
        self.attr = None
        self.changed_cb = changed_cb

    def bindAttr(
        self,
        elem: ET.Element,
        attr: str,
        changed_cb: callable = None,
        in_trans: callable = None,
        out_trans: callable = None,
    ):
        """Bind this entry to attribute

        Args:
            elem (ET.Element): XML element
            attr (str): attribute name
            in_trans (callable): Transform input to text
            out_trans (callable): Transform text to output
        """
        self.unbind()

        self.in_trans = in_trans
        self.out_trans = out_trans
        if self.in_trans is None:
            self.in_trans = lambda x: x
        if self.out_trans is None:
            self.out_trans = lambda x: x

        self.set_text(self.out_trans(elem.get(attr, "")))
        self.elem = elem
        self.attr = attr
        self.changed_cb = changed_cb

    def __onChanged__(self, *_):
        """The state changed."""
        self.set_css_classes([])

        if self.elem is not None:
            try:
                self.in_trans(self.get_text())
            except:
                self.set_css_classes(["error"])

            if self.attr is None:
                self.elem.text = self.in_trans(self.get_text())
            else:
                self.elem.set(self.attr, self.in_trans(self.get_text()))
        if self.changed_cb is not None:
            self.changed_cb()


class BindablePasswordRow:
    """Bindable Adwaita PasswordRow that can be bound to a xml text/attribute."""

    def __init__(self, **kwargs):
        """Create row"""
        self.widget = Adw.PasswordEntryRow(**kwargs)
        self.set_visible = self.widget.set_visible

        self.elem = None
        self.attr = None
        self.changed_cb = None
        self.in_trans = None
        self.out_trans = None
        self.widget.connect("changed", self.__onChanged__)

    def getWidget(self):
        """Get this widget"""
        return self.widget

    def unbind(self):
        """Remove any bindings"""
        self.elem = None
        self.attr = None
        self.changed_cb = None
        self.in_trans = None
        self.out_trans = None

    def bindText(
        self,
        elem: ET.Element,
        changed_cb: callable = None,
        in_trans: callable = None,
        out_trans: callable = None,
    ):
        """Bind this entry to text property

        Args:
            elem (ET.Element): XML element
            changed_cb (callable): Call when changed
            in_trans (callable): Transform input to text
            out_trans (callable): Transform text to output
        """
        self.unbind()

        self.in_trans = in_trans
        self.out_trans = out_trans
        if self.in_trans is None:
            self.in_trans = lambda x: x
        if self.out_trans is None:
            self.out_trans = lambda x: x

        self.widget.set_text(self.out_trans(getETText(elem)))
        self.elem = elem
        self.attr = None
        self.changed_cb = changed_cb

    def bindAttr(
        self,
        elem: ET.Element,
        attr: str,
        changed_cb: callable = None,
        in_trans: callable = None,
        out_trans: callable = None,
    ):
        """Bind this entry to attribute

        Args:
            elem (ET.Element): XML element
            attr (str): attribute name
            in_trans (callable): Transform input to text
            out_trans (callable): Transform text to output
        """
        self.unbind()

        self.in_trans = in_trans
        self.out_trans = out_trans
        if self.in_trans is None:
            self.in_trans = lambda x: x
        if self.out_trans is None:
            self.out_trans = lambda x: x

        self.widget.set_text(self.out_trans(elem.get(attr, "")))
        self.elem = elem
        self.attr = attr
        self.changed_cb = changed_cb

    def __onChanged__(self, *_):
        """The state changed."""
        if self.elem is not None:
            if self.attr is None:
                self.elem.text = self.in_trans(self.widget.get_text())
            else:
                self.elem.set(self.attr, self.in_trans(self.widget.get_text()))
        if self.changed_cb is not None:
            self.changed_cb()


class BindableEntry(Gtk.Entry):
    """General Gtk Entry that can be bound to a xml text/attribute."""

    def __init__(self, *args, **kwargs):
        """Create entry"""
        super().__init__(*args, **kwargs)

        self.elem = None
        self.attr = None
        self.changed_cb = None
        self.in_trans = None
        self.out_trans = None
        self.connect("changed", self.__onChanged__)

    def getWidget(self):
        """Get this widget"""
        return self

    def unbind(self):
        """Remove any bindings"""
        self.elem = None
        self.attr = None
        self.changed_cb = None
        self.in_trans = None
        self.out_trans = None

    def bindText(
        self,
        elem: ET.Element,
        changed_cb: callable = None,
        in_trans: callable = None,
        out_trans: callable = None,
    ):
        """Bind this entry to text property

        Args:
            elem (ET.Element): XML element
            changed_cb (callable): Call when changed
            in_trans (callable): Transform input to text
            out_trans (callable): Transform text to output
        """
        self.unbind()

        self.in_trans = in_trans
        self.out_trans = out_trans
        if self.in_trans is None:
            self.in_trans = lambda x: x
        if self.out_trans is None:
            self.out_trans = lambda x: x

        self.set_text(self.out_trans(getETText(elem)))
        self.elem = elem
        self.attr = None
        self.changed_cb = changed_cb

    def bindAttr(
        self,
        elem: ET.Element,
        attr: str,
        changed_cb: callable = None,
        in_trans: callable = None,
        out_trans: callable = None,
    ):
        """Bind this entry to attribute

        Args:
            elem (ET.Element): XML element
            attr (str): attribute name
            in_trans (callable): Transform input to text
            out_trans (callable): Transform text to output
        """
        self.unbind()

        self.in_trans = in_trans
        self.out_trans = out_trans
        if self.in_trans is None:
            self.in_trans = lambda x: x
        if self.out_trans is None:
            self.out_trans = lambda x: x

        self.set_text(self.out_trans(elem.get(attr, "")))
        self.elem = elem
        self.attr = attr
        self.changed_cb = changed_cb

    def __onChanged__(self, *_):
        """The state changed."""
        self.set_css_classes([])

        if self.elem is not None:
            try:
                self.in_trans(self.get_text())
            except:
                self.set_css_classes(["error"])

            if self.attr is None:
                self.elem.text = self.in_trans(self.get_text())
            else:
                self.elem.set(self.attr, self.in_trans(self.get_text()))
        if self.changed_cb is not None:
            self.changed_cb()


class BindableComboRow(Adw.ComboRow):
    """A Adwaita ComboRow that can be bound to a xml text/attribute."""

    def __init__(self, selection: list[str], default: str = None, **kwargs):
        """Create ComborRow

        Args:
            selection (list[str]): List of choices
            default (str, optional): Possible additional default choice. Defaults to None.
        """
        super().__init__(**kwargs)

        self.selection = selection.copy()
        self.default = default
        if self.default is not None:
            self.selection.insert(0, self.default)
        self.set_model(Gtk.StringList(strings=self.selection))
        self.elem = None
        self.attr = None
        self.changed_cb = None
        self.connect("notify::selected", self.__onChanged__)

    def getWidget(self):
        """Get this widget"""
        return self

    def setSelection(self, selection: list[str]):
        """Set new selection

        Args:
            selection (list): List of presented strings
        """
        self.selection = selection.copy()
        if self.default is not None and self.default not in self.selection:
            self.selection.insert(0, self.default)
        self.selection.sort()
        self.set_model(Gtk.StringList(strings=self.selection))

    def setSelectedString(self, selected_str: str):
        """Set a selected string

        Args:
            selected_str (str): String to select, must be in previously set selection
        """
        changed_cb = self.changed_cb
        self.changed_cb = None
        self.set_selected(self.selection.index(selected_str))
        self.changed_cb = changed_cb

    def getSelectedString(self) -> str:
        """Return the currently selected string

        Returns:
            str: Selected string
        """
        return self.selection[self.get_selected()]

    def unbind(self):
        """Remove any bindings"""
        self.elem = None
        self.attr = None
        self.changed_cb = None

    def bindText(
        self,
        elem: ET.Element,
        changed_cb: callable = None,
    ):
        """Bind this combo to text property

        Args:
            elem (ET.Element): XML element
            changed_cb (callable): Call when changed
        """
        self.unbind()

        if getETText(elem) in self.selection:
            self.set_selected(self.selection.index(getETText(elem)))
        elif elem.text is None:
            self.set_selected(0)
            if len(self.selection):
                elem.text = self.selection[self.get_selected()]
        else:
            self.selection.append(elem.text)
            self.setSelection(self.selection)
            self.set_selected(len(self.selection) - 1)
        self.elem = elem
        self.attr = None
        self.changed_cb = changed_cb

    def bindAttr(
        self,
        elem: ET.Element,
        attr: str,
        changed_cb: callable = None,
    ):
        """Bind this combo to attribute

        Args:
            elem (ET.Element): XML element
            attr (str): attribute name
        """
        self.unbind()

        if elem.get(attr, "") in self.selection:
            self.set_selected(self.selection.index(elem.get(attr, "")))
        elif elem.get(attr) is None:
            self.set_selected(0)
            if len(self.selection):
                elem.set(attr, self.selection[self.get_selected()])
        else:
            self.selection.append(elem.get(attr))
            self.setSelection(self.selection)
            self.set_selected(len(self.selection) - 1)
        self.elem = elem
        self.attr = attr
        self.changed_cb = changed_cb

    def __onChanged__(self, *_):
        """The state changed."""
        if self.elem is not None:
            if self.attr is None:
                self.elem.text = self.selection[self.get_selected()]
            else:
                if self.default is not None and self.get_selected() == 0:
                    if self.elem.attrib.get(self.attr) is not None:
                        del self.elem.attrib[self.attr]
                else:
                    self.elem.set(self.attr, self.selection[self.get_selected()])
        if self.changed_cb is not None:
            self.changed_cb()


class ExistentialComboRow(Adw.ComboRow):
    """Creates an Adwaita ComboRow that deletes a xml tag if the default value
    is selected, but the selected value is written into the attribute"""

    def __init__(
        self, tag: str, attr: str, selection: list[str], default: str, **kwargs
    ):
        """Create a combo row

        Args:
            tag (str): The tag it should bind to
            attr (str): The attribute of the tag the selected value is written to
            selection (list[str]): List of choices
            default (str): The default choice
        """
        super().__init__(**kwargs)

        self.tag = tag
        self.attr = attr
        self.selection = selection.copy()
        self.default = default
        self.selection.insert(0, self.default)
        self.set_model(Gtk.StringList(strings=self.selection))

        self.elem = None
        self.changed_cb = None

        self.connect("notify::selected", self.__onChanged__)

    def getWidget(self):
        """Get this widget"""
        return self

    def setSelection(self, selection):
        """Set new selection

        Args:
            selection (_type_): List of presented strings
        """
        self.selection = selection.copy()
        if self.default is not None and self.default not in self.selection:
            self.selection.insert(0, self.default)
        self.set_model(Gtk.StringList(strings=self.selection))

    def getSelectedString(self) -> str:
        """Return the currently selected string

        Returns:
            str: Selected string
        """
        return self.selection[self.get_selected()]

    def unbind(self):
        """Remove any bindings"""
        self.elem = None
        self.changed_cb = None

    def bind(
        self,
        elem: ET.Element,
        changed_cb: callable = None,
    ):
        """Bind this combo to attribute

        Args:
            elem (ET.Element): XML element
        """
        self.unbind()

        e = elem.find(self.tag)
        if e is not None:
            if e.get(self.attr, "") in self.selection:
                self.set_selected(self.selection.index(e.get(self.attr, "")))
            elif e.get(self.attr) is None:
                self.set_selected(0)
            else:
                self.selection.append(e.get(self.attr))
                self.setSelection(self.selection)
                self.set_selected(len(self.selection) - 1)
        else:
            self.set_selected(0)

        self.elem = elem
        self.changed_cb = changed_cb

    def __onChanged__(self, *_):
        """The state changed."""
        if self.elem is not None:
            e = self.elem.find(self.tag)
            if self.getSelectedString() == self.default and e is not None:
                self.elem.remove(e)
            elif self.getSelectedString() != self.default:
                if e is None:
                    e = ET.SubElement(self.elem, self.tag)
                e.clear()
                e.set(self.attr, self.getSelectedString())
        if self.changed_cb is not None:
            self.changed_cb()


class BindableDropDown(Gtk.DropDown):
    """A Gtk DropDown that can be bound to a xml text/attribute"""

    def __init__(self, selection: list[str], default=None, **kwargs):
        """Create bindable dropdown

        Args:
            selection (list[str]): List of selectable string
            default (_type_, optional): Additional default string, which is not in selection.
        """
        super().__init__(**kwargs)

        self.selection = selection.copy()
        self.default = default
        if self.default is not None:
            self.selection.insert(0, self.default)
        self.set_model(Gtk.StringList(strings=self.selection))
        self.elem = None
        self.attr = None
        self.changed_cb = None
        self.connect("notify::selected", self.__onChanged__)

    def getWidget(self):
        """Get this widget"""
        return self

    def setSelection(self, selection):
        """Set new selection

        Args:
            selection (_type_): List of presented strings
        """
        self.selection = selection.copy()
        if self.default is not None and self.default not in self.selection:
            self.selection.insert(0, self.default)
        self.set_model(Gtk.StringList(strings=self.selection))

    def setSelectedString(self, selected_str: str):
        """Set a selected string

        Args:
            selected_str (str): String to select, must be in previously set selection
        """
        changed_cb = self.changed_cb
        self.changed_cb = None
        self.set_selected(self.selection.index(selected_str))
        self.changed_cb = changed_cb

    def getSelectedString(self) -> str:
        """Return the currently selected string

        Returns:
            str: Selected string
        """
        return self.selection[self.get_selected()]

    def unbind(self):
        """Remove any bindings"""
        self.elem = None
        self.attr = None
        self.changed_cb = None

    def bindText(
        self,
        elem: ET.Element,
        changed_cb: callable = None,
    ):
        """Bind this combo to text property

        Args:
            elem (ET.Element): XML element
            changed_cb (callable): Call when changed
        """
        self.unbind()

        if getETText(elem) in self.selection:
            self.set_selected(self.selection.index(getETText(elem)))
        elif elem.text is None:
            self.set_selected(0)
            elem.text = self.selection[self.get_selected()]
        else:
            self.selection.append(elem.text)
            self.setSelection(self.selection)
            self.set_selected(len(self.selection) - 1)
        self.elem = elem
        self.attr = None
        self.changed_cb = changed_cb

    def bindAttr(
        self,
        elem: ET.Element,
        attr: str,
        changed_cb: callable = None,
    ):
        """Bind this combo to attribute

        Args:
            elem (ET.Element): XML element
            attr (str): attribute name
        """
        self.unbind()

        if elem.get(attr, "") in self.selection:
            self.set_selected(self.selection.index(elem.get(attr, "")))
        elif elem.get(attr) is None:
            self.set_selected(0)
            elem.set(attr, self.selection[self.get_selected()])
        else:
            self.selection.append(elem.get(attr))
            self.setSelection(self.selection)
            self.set_selected(len(self.selection) - 1)
        self.elem = elem
        self.attr = attr
        self.changed_cb = changed_cb

    def __onChanged__(self, *_):
        """The state changed."""
        if self.elem is not None:
            if self.attr is None:
                self.elem.text = self.selection[self.get_selected()]
            else:
                if self.default is not None and self.get_selected() == 0:
                    if self.elem.attrib.get(self.attr) is not None:
                        del self.elem.attrib[self.attr]
                else:
                    self.elem.set(self.attr, self.selection[self.get_selected()])
        if self.changed_cb is not None:
            self.changed_cb()


class BindableSwitchRow:
    """A Adwaita SwitchRow that can be bound to a xml text/attribute."""

    def __init__(self, positive: str, negative: str, default: bool = None, **kwargs):
        """Create switch row. Widget is called self.switch_row; this is only a wrapper!

        Args:
            positive (str): What to fill in when actived
            negative (str): What to fill in when deactivated
            default (bool, optional): Default state if value is unset. Defaults to None.
        """
        self.switch_row = Adw.SwitchRow(**kwargs)

        self.positive = positive
        self.negative = negative
        self.default = default

        self.elem = None
        self.attr = None
        self.changed_cb = None
        self.switch_row.connect("notify::active", self.__onChanged__)

        self.set_visible = self.switch_row.set_visible

    def getWidget(self) -> Adw.SwitchRow:
        """Get this widget"""
        return self.switch_row

    def unbind(self):
        """Remove any bindings"""
        self.elem = None
        self.attr = None
        self.changed_cb = None

    def bindText(
        self,
        elem: ET.Element,
        changed_cb: callable = None,
    ):
        """Bind this switch to text property

        Args:
            elem (ET.Element): XML element
            changed_cb (callable): Call when changed
        """
        self.unbind()

        self.switch_row.set_active(getETText(elem.text) == self.positive)
        if elem.text is None and self.default is not None:
            self.switch_row.set_active(self.default)
            elem.text = self.positive if self.default else self.negative

        self.elem = elem
        self.attr = None
        self.changed_cb = changed_cb

    def bindAttr(
        self,
        elem: ET.Element,
        attr: str,
        changed_cb: callable = None,
    ):
        """Bind this switch to attribute

        Args:
            elem (ET.Element): XML element
            attr (str): attribute name
        """
        self.unbind()

        self.switch_row.set_active(elem.get(attr) == self.positive)
        if elem.get(attr) is None and self.default is not None:
            self.switch_row.set_active(self.default)
            elem.set(
                attr,
                self.positive if self.default else self.negative,
            )

        self.elem = elem
        self.attr = attr
        self.changed_cb = changed_cb

    def __onChanged__(self, *_):
        """The state changed."""
        if self.elem is not None:
            if self.attr is None:
                self.elem.text = (
                    self.positive if self.switch_row.get_active() else self.negative
                )
            else:
                self.elem.set(
                    self.attr,
                    self.positive if self.switch_row.get_active() else self.negative,
                )
        if self.changed_cb is not None:
            self.changed_cb()


class ExistentialSwitchRow:
    """A Adwaita SwitchRow that removes the specified tag from the tree if it
    is deactivated. The actual value is written into the attribute specified.
    """

    def __init__(self, tag: str, attrib: dict, **kwargs):
        """Switch row that removes a tag when unselected

        Args:
            tag (str): The tag to add/remove
            attrib(dict): Create the tag with additional attributes
        """
        self.switch_row = Adw.SwitchRow(**kwargs)

        self.elem = None
        self.tag = tag
        self.attrib = attrib
        self.changed_cb = None
        self.switch_row.connect("notify::active", self.__onChanged__)

        self.set_visible = self.switch_row.set_visible

    def getWidget(self) -> Adw.SwitchRow:
        """Get this widget"""
        return self.switch_row

    def unbind(self):
        """Remove any bindings"""
        self.elem = None
        self.changed_cb = None

    def bind(
        self,
        elem: ET.Element,
        changed_cb: callable = None,
    ):
        """Bind this switch to text property

        Args:
            elem (ET.Element): XML element
            changed_cb (callable): Call when changed
        """
        self.unbind()
        e = elem.find(self.tag)
        if e is None:
            self.switch_row.set_active(False)
        else:
            self.switch_row.set_active(True)

        self.elem = elem
        self.changed_cb = changed_cb

    def __onChanged__(self, *_):
        """The state changed."""
        if self.elem is not None:
            e = self.elem.find(self.tag)
            if self.switch_row.get_active() and e is None:
                ET.SubElement(self.elem, self.tag, attrib=self.attrib)
            elif not self.switch_row.get_active() and e is not None:
                self.elem.remove(e)
        if self.changed_cb is not None:
            self.changed_cb()


class BindableSpinRow:
    """A Adwaita SpinRow that can be bound to a xml text/attribute."""

    def __init__(self, out_format: callable, unset_val: float = None, **kwargs):
        """Create the widget

        Args:
            out_format (callable): Function taking a value and returning a string for xml.
            unset_val (float, optional): Value when the attribute should vanish. Defaults to None.
        """
        self.spin_row = Adw.SpinRow(**kwargs)

        self.out_format = out_format
        self.unset_val = unset_val

        self.elem = None
        self.attr = None
        self.changed_cb = None
        self.spin_row.connect("notify::value", self.__onChanged__)

        self.set_visible = self.spin_row.set_visible

    def getWidget(self):
        """Get this widget"""
        return self.spin_row

    def getValue(self):
        """Return the value of the row."""
        return self.out_format(self.spin_row.get_value())

    def unbind(self):
        """Remove any bindings"""
        self.elem = None
        self.attr = None
        self.changed_cb = None

    def bindText(
        self,
        elem: ET.Element,
        changed_cb: callable = None,
    ):
        """Bind this spinner to text property

        Args:
            elem (ET.Element): XML element
            changed_cb (callable): Call when changed
        """
        self.unbind()

        self.spin_row.set_value(float(getETText(elem)))

        self.elem = elem
        self.attr = None
        self.changed_cb = changed_cb

    def bindAttr(
        self,
        elem: ET.Element,
        attr: str,
        changed_cb: callable = None,
    ):
        """Bind this spinner to attribute

        Args:
            elem (ET.Element): XML element
            attr (str): attribute name
            changed_cb (callable): Call when changed
        """
        self.unbind()

        self.spin_row.set_value(float(elem.get(attr, "-1")))

        self.elem = elem
        self.attr = attr
        self.changed_cb = changed_cb

    def __onChanged__(self, *_):
        """The state changed."""
        if self.elem is not None:
            if self.attr is None:
                self.elem.text = self.out_format(self.spin_row.get_value())
            else:
                self.elem.set(self.attr, self.out_format(self.spin_row.get_value()))
                if (
                    self.unset_val is not None
                    and self.spin_row.get_value() == self.unset_val
                ):
                    if self.elem.attrib.get(self.attr) is not None:
                        del self.elem.attrib[self.attr]
        if self.changed_cb is not None:
            self.changed_cb()


class BindableSpinButton:
    def __init__(self, out_format: callable, unset_val: float = None, **kwargs):
        """Create spin button, widget is called self.spin_btn; this is only a wrapper!"""
        self.spin_btn = Gtk.SpinButton(**kwargs)

        self.out_format = out_format
        self.unset_val = unset_val

        self.elem = None
        self.attr = None
        self.changed_cb = None
        self.spin_btn.connect("notify::value", self.__onChanged__)

        self.set_visible = self.spin_btn.set_visible

    def getWidget(self):
        """Get this widget"""
        return self.spin_btn

    def getValue(self):
        """Return the value of the row."""
        return self.out_format(self.spin_btn.get_value())

    def unbind(self):
        """Remove any bindings"""
        self.elem = None
        self.attr = None
        self.changed_cb = None

    def bindText(
        self,
        elem: ET.Element,
        changed_cb: callable = None,
    ):
        """Bind this spinner to text property

        Args:
            elem (ET.Element): XML element
            changed_cb (callable): Call when changed
        """
        self.unbind()

        self.spin_btn.set_value(float(getETText(elem)))

        self.elem = elem
        self.attr = None
        self.changed_cb = changed_cb

    def bindAttr(
        self,
        elem: ET.Element,
        attr: str,
        changed_cb: callable = None,
    ):
        """Bind this spinner to attribute

        Args:
            elem (ET.Element): XML element
            attr (str): attribute name
            changed_cb (callable): Call when changed
        """
        self.unbind()

        self.spin_btn.set_value(float(elem.get(attr, "-1")))

        self.elem = elem
        self.attr = attr
        self.changed_cb = changed_cb

    def __onChanged__(self, *_):
        """The state changed."""
        if self.elem is not None:
            if self.attr is None:
                self.elem.text = self.out_format(self.spin_btn.get_value())
            else:
                self.elem.set(self.attr, self.out_format(self.spin_btn.get_value()))
                if (
                    self.unset_val is not None
                    and self.spin_btn.get_value() == self.unset_val
                ):
                    if self.elem.attrib.get(self.attr) is not None:
                        del self.elem.attrib[self.attr]
        if self.changed_cb is not None:
            self.changed_cb()
