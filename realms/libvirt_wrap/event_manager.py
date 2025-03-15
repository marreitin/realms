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

from .common import *


class EventManager:
    """Simple base class that allows managing events with
    arbitrarily many callbacks. Used for most libvirt wrapping
    classes.
    """

    def __init__(self):
        self.event_callbacks = []

    def registerCallback(self, _cb: callable):
        """Register a callback to the wrappers callback multiplexer.
        It will be called on any lifecycle event of *any* domain.

        Args:
            _cb (callable): Callback

        Raises:
            ValueError: Raise if function already registered
        """
        el = None
        for cb in self.event_callbacks:
            if cb == _cb:
                el = cb
                break
        if el is not None:
            raise ValueError("Callback already registered")
        self.event_callbacks.append(_cb)

    def unregisterCallback(self, _cb: callable):
        """Unregister event callback

        Args:
            _cb (callable): Callback

        Raises:
            ValueError: If not registered
        """
        el = None
        for cb in self.event_callbacks:
            if cb == _cb:
                el = cb
                break
        if el is not None:
            self.event_callbacks.remove(el)
            print(f"Removed callback { _cb }")
        else:
            raise ValueError("Callback was not registered")

    def sendEvent(self, conn, obj, type_id, event_id, detail_id):
        """Send out event to all subscribed callbacks"""
        # printEvent(conn, obj, type_id, event_id, detail_id)
        for cb in self.event_callbacks.copy():
            cb(conn, obj, type_id, event_id, detail_id)
