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
from gi.repository import GLib


def prettyTime(unix: str | int):
    """Transform unix time into a pretty, localised description

    Args:
        unix (str|int): Unix timestamp
    """
    if isinstance(unix, str):
        unix = int(unix)

    time = GLib.DateTime.new_from_unix_utc(unix)
    time = time.to_timezone(GLib.TimeZone.new_local())
    # Use preferred representation of time and date for locale.
    return time.format("%x %X")
