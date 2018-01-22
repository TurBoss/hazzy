#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of Hazzy.
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk

from OpenGL.GL import glClearColor, glClear, GL_COLOR_BUFFER_BIT, glFlush

PYDIR = os.path.join(os.path.dirname(__file__))


class Gremlin3(Gtk.Box):
    title = 'Gremlin3'
    author = ''
    version = '0.1.0'
    date = '5/11/2017'
    description = 'Basic module skeleton'

    def __init__(self, widget_window):
        Gtk.Box.__init__(self)

        gl_area = Gtk.GLArea()
        gl_area.connect('render', self.area_render)
        gl_area.connect('realize', self.area_realize)
        #gl_area.connect('create-context', self.area_context)

        self.pack_start(gl_area, True, True, 0)

    def area_realize (self, gl_area):
        error = gl_area.get_error()
        if error != None:
            print "your graphics card is probably too old : ", error
        else:
            print gl_area, "realize... fine so far"

    def area_context(self, gl_area):
        # not needed except for special instances, read the docs
        c = gl_area.get_context()
        print c , "context"
        return c

    def area_render(self, area, context):
        #print gl_area
        #print gl_context
        glClearColor (0.5, 0.5, 0.5, 1.0)
        glClear (GL_COLOR_BUFFER_BIT)
        glFlush()
        print "rendering... done"
        return True