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
# All libvirt related custom constants

"""Definitions for custom event ids."""

(
    CALLBACK_TYPE_CONNECTION_GENERIC,
    CALLBACK_TYPE_DOMAIN_LIFECYCLE,
    CALLBACK_TYPE_DOMAIN_GENERIC,
    CALLBACK_TYPE_POOL_LIFECYCLE,
    CALLBACK_TYPE_POOL_GENERIC,
    CALLBACK_TYPE_NETWORK_LIFECYCLE,
    CALLBACK_TYPE_NETWORK_GENERIC,
    CALLBACK_TYPE_SECRET_LIFECYCLE,
    CALLBACK_TYPE_SECRET_GENERIC,
) = range(9)

(
    CONNECTION_EVENT_CONNECTED,
    CONNECTION_EVENT_DISCONNECTED,
    CONNECTION_EVENT_DELETED,
    CONNECTION_EVENT_SETTINGS_CHANGED,
    CONNECTION_EVENT_ATTEMPT_CONNECT,
    CONNECTION_EVENT_CONNECTION_FAILED,
) = range(6)

(
    DOMAIN_EVENT_DELETED,
    DOMAIN_EVENT_ADDED,
    DOMAIN_EVENT_SNAPSHOT_TAKEN,
    DOMAIN_EVENT_SNAPSHOT_DELETED,
) = range(4)

(
    POOL_EVENT_DELETED,
    POOL_EVENT_ADDED,
    POOL_EVENT_VOLUME_ADDED,
    POOL_EVENT_VOLUME_DELETED,
) = range(4)

(NETWORK_EVENT_DELETED, NETWORK_EVENT_ADDED) = range(2)

(SECRET_EVENT_DELETED, SECRET_EVENT_ADDED) = range(2)

(
    CONNECTION_STATE_DISCONNECTED,
    CONNECTION_STATE_CONNECTED,
    CONNECTION_STATE_CONNECTING,
) = range(3)
