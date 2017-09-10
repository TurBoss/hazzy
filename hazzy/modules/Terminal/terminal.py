#!/usr/bin/env python

import os
import sys
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Vte', '2.91')

from gi.repository import Gtk, Vte
from gi.repository import GLib

PYDIR = os.path.join(os.path.dirname(__file__))

print "PYDIR", PYDIR

class Terminal(Gtk.ScrolledWindow):

    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)

        self.terminal=Vte.Terminal()
        self.terminal.spawn_sync(
                Vte.PtyFlags.DEFAULT,   # depreciated, does nothing?
                os.environ['HOME'],     # where to start the command?
                ["/bin/bash"],          # where is the emulator?
                [],                     # it's ok to leave this list empty
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,                   # at least None is required
                None,
                )

        self.terminal.set_font_scale(1.1)

        self.set_size_request(200, 200)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.add(self.terminal)

def main():
    win = Gtk.Window()
    win.connect('delete-event', Gtk.main_quit)
    win.add(Terminal())
    win.show_all()

    Gtk.main()

if __name__ == '__main__':
    main()
