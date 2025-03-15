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
import traceback
from os import remove
from threading import Event

import libvirt
from gi.repository import Adw, GLib, Gtk

from realms.helpers import asyncJob, bytesToString
from realms.libvirt_wrap import Volume
from realms.libvirt_wrap.constants import *


class DownloadVolumeDialog:
    def __init__(self, window: Adw.ApplicationWindow, volume: Volume):
        self.window = window
        self.volume = volume
        self.volume.pool.registerCallback(self.onConnectionEvent)
        self.tree = None
        self.cancel_event = Event()

        # Create a Builder
        self.builder = Gtk.Builder.new_from_resource(
            "/com/github/marreitin/realms/gtk/downloadvol.ui"
        )

        # Obtain and show the main window
        self.dialog = self.obj("main-dialog")
        self.dialog.connect("closed", self.onDialogClosed)

        self.obj("btn-cancel").connect("clicked", self.onCancelClicked)

        self.start()

    def start(self):
        """Start the download of the volume."""

        def updateProgress(size, bytes_received):
            percentage = int((bytes_received / size) * 100)
            self.obj("download-progress").set_fraction(bytes_received / size)
            self.obj("download-progress").set_text(
                f"{ bytesToString(bytes_received) } / { bytesToString(size) } - { percentage }%"
            )

        def downloadVolume(folder: str):
            """Run the download and write contents to the chosen file."""
            stream = self.volume.pool.connection.__connection__.newStream()
            try:
                size = self.volume.getCapacity()
                bytes_received = 0
                self.volume.volume.download(stream, 0, 0)

                batch_size = 262120
                filename = f"{ folder }/{ self.volume.getName() }"

                with open(filename, "wb") as f:
                    stream_bytes = stream.recv(batch_size)
                    while stream_bytes != b"" and not self.cancel_event.is_set():
                        f.write(stream_bytes)
                        stream_bytes = stream.recv(batch_size)
                        bytes_received += batch_size

                        # Only update the progress bar occasionally.
                        if int(bytes_received / batch_size) % 20 == 0:
                            GLib.idle_add(
                                lambda *x: updateProgress(size, bytes_received), None
                            )
            except libvirt.libvirtError:
                traceback.print_exc()

            try:
                stream.finish()
            except libvirt.libvirtError:
                print("Finishing stream failed")
                traceback.print_exc()

            # If the file already exists when cancelling, remove it.
            if self.cancel_event.is_set():
                try:
                    remove(filename)
                except OSError:
                    pass

            print("Done downloading")

        def onFolderSelected(dialog, result):
            folder = dialog.select_folder_finish(result)
            if folder is None:
                pass
            else:
                self.dialog.present(None)
                asyncJob(
                    downloadVolume, [folder.get_path()], lambda *x: self.dialog.close()
                )

        # Present dialog to pick saving location
        dialog = Gtk.FileDialog(title="Select download location")
        dialog.select_folder(self.window, None, onFolderSelected)

    def onCancelClicked(self, btn):
        """Cancel the download."""
        self.cancel_event.set()
        btn.set_sensitive(False)

    def obj(self, name: str):
        o = self.builder.get_object(name)
        if o is None:
            raise NotImplementedError(f"Object { name } could not be found!")
        return o

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id):
        if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.onCancelClicked(self.obj("btn-cancel"))
                self.dialog.close()
        elif type_id == CALLBACK_TYPE_POOL_GENERIC:
            if event_id in [POOL_EVENT_DELETED]:
                self.onCancelClicked(self.obj("btn-cancel"))
                self.dialog.close()

    def onDialogClosed(self, *_):
        self.cancel_event.set()
        self.volume.pool.unregisterCallback(self.onConnectionEvent)
