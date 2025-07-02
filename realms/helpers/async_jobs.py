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
import threading
import traceback
from dataclasses import dataclass

from gi.repository import GLib


def asyncJob(f: callable, args: any, cb: callable):
    """Generic job that runs asynchronously and then calls back with the result

    Args:
        f (callable): Function to run asynchronously
        args (any): Arguments for f
        cb (callable): Callback, will be called with results from f
    """

    def __run__(args):
        ret = f(*args)
        GLib.idle_add(cb, ret)

    thread = threading.Thread(target=__run__, args=[args], daemon=True)
    thread.start()


@dataclass
class ResultWrapper:
    data: any
    failed: bool


def failableAsyncJob(f: callable, args: any, except_cb: callable, finally_cb: callable):
    """Generic job that runs asynchronously and calls back upon failure, then calls back
    again with a ResultWrapper as argument

    Args:
        f (callable): Function to run asynchronously
        args (any): Arguments for f
        except_cb (callable): Callback on failure, called with exception
        finally_cb (callable): Final callback with ResultWrapper for data
    """

    def __onExcept__(e: Exception):
        except_cb(e)
        finally_cb(ResultWrapper(None, True))

    def __run__(args):
        try:
            res = f(*args)
            GLib.idle_add(finally_cb, ResultWrapper(res, False))
        except Exception as e:
            traceback.print_exc()
            GLib.idle_add(__onExcept__, e)

    thread = threading.Thread(target=__run__, args=[args], daemon=True)
    thread.start()


class RepeatJob:
    def __init__(self, f: callable, args: any, cb: callable, interval: int):
        """Job that spawns after interval a thread to run a job, then calls back
        with the result to the main thread.

        Args:
            f (callable): Function to run asynchronously
            args (any): Arguments for f
            cb (callable): Callback, will be called with results from f
            interval (int): Seconds at which to repeat task
        """
        self.f = f
        self.args = args
        self.cb = cb
        self.stop_flag = threading.Event()

        GLib.timeout_add(interval * 1000, self.__onTimeout__)
        self.__onTimeout__()

    def __onTimeout__(self):
        if self.stop_flag.is_set():
            self.stop_flag.clear()
            return False  # Cancel timeout
        thread = threading.Thread(target=self.__run__, args=[self.args], daemon=True)
        thread.start()
        return True

    def __run__(self, args):
        ret = self.f(*args)
        GLib.idle_add(self.cb, ret)

    def trigger(self):
        """Trigger execution of this job."""
        self.__onTimeout__()

    def stopTask(self):
        """Stop the repeated task, a running task will however not be killed."""
        self.stop_flag.set()
