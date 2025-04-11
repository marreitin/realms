# # Realms, a libadwaita libvirt client.
# # Copyright (C) 2025
# #
# # This program is free software: you can redistribute it and/or modify
# # it under the terms of the GNU General Public License as published by
# # the Free Software Foundation, either version 3 of the License, or
# # (at your option) any later version.
# #
# # This program is distributed in the hope that it will be useful,
# # but WITHOUT ANY WARRANTY; without even the implied warranty of
# # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# # GNU General Public License for more details.
# #
# # You should have received a copy of the GNU General Public License
# # along with this program.  If not, see <https://www.gnu.org/licenses/>.
# import xml.etree.ElementTree as ET

# import libvirt
# from gi.repository import Adw, Gtk, RdwSpice, GObject, Rdw, RdwVnc

# from realms.helpers import ResultWrapper, failableAsyncJob, getETText, prettyTime
# from realms.libvirt_wrap import Domain
# from realms.libvirt_wrap.constants import *
# from realms.ui.components import ActionOption, iconButton, selectDialog
# from realms.ui.components.preference_widgets import RealmsPreferencesPage
# from realms.ui.dialogs.inspect_snapshot_dialog import InspectSnapshotDialog
# from realms.ui.dialogs.take_snapshot_dialog import TakeSnapshotDialog
# from realms.ui.window_reference import WindowReference


# class DisplayBox(Gtk.Box):
#     def __init__(self, domain: Domain, window_ref: WindowReference):
#         super().__init__(orientation=Gtk.Orientation.VERTICAL)

#         self.domain = domain
#         self.window_ref = window_ref


#         print([r.get_name() for r in GObject.list_properties(Rdw.Display)])
#         spice = RdwSpice.DisplayClass()
#         print(dir(RdwSpice))
#         print(dir(Rdw))
#         help(RdwVnc)
#         print(dir(RdwVnc.DisplayClass))
#         print(spice)
#         # session = spice.session()
#         # session.set_uri("/var/lib/libvirt/qemu/domain-1-Ubuntu/spice.sock")
#         # session.connect_channel_new(window_ref.window.get_application(), lambda *x: print(x))
#         # session.connect_disconnected(window_ref.window.get_application(), lambda *x: print(x))
#         # session.connect()

#         self.domain.registerCallback(self.__onConnectionEvent__)

#     def __onConnectionEvent__(self, conn, obj, type_id, event_id, _):
#         if type_id == CALLBACK_TYPE_DOMAIN_GENERIC:
#             pass
#         elif type_id == CALLBACK_TYPE_DOMAIN_LIFECYCLE:
#             pass

#     def end(self):
#         self.domain.unregisterCallback(self.__onConnectionEvent__)
