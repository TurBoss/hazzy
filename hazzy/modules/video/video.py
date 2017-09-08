#!/usr/bin/env python

import logging
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gtk, Gst

log = logging.getLogger(__name__)

Gst.init(None)
Gst.init_check(None)


class GstWidget(Gtk.Box):
    def __init__(self, *args, **kwargs):
        Gtk.Box.__init__(self)
        self.connect('unmap', self.on_unmap)
        self.connect('map', self.on_map)

    def on_message(self, bus, message):
        # log.debug("Message: %s", message)
        if message:
            struct = message.get_structure()
            if struct:
                struct_name = struct.get_name()
                # log.debug('Message name: %s', struct_name)

                if struct_name == 'GstMessageError':
                    err, debug = message.parse_error()
                    log.error('GstError: %s, %s', err, debug)
                elif struct_name == 'GstMessageWarning':
                    err, debug = message.parse_warning()
                    log.warning('GstWarning: %s, %s', err, debug)

    def run(self):
        p = "autovideosrc  \n"
        # p = "uridecodebin uri=file:///tmp/qr.png "
        # p = "uridecodebin uri=file:///tmp/v.webm "
        p += " ! tee name=t \n"
        p += "       t. ! queue ! videoconvert \n"
        p += "                  ! zbar cache=true attach_frame=true \n"
        p += "                  ! fakesink \n"
        p += "       t. ! queue ! videoconvert \n"
        p += ("                 ! gtksink "
              "sync=false "
              "name=imagesink "
              # "max-lateness=2000000000000  "
              "enable-last-sample=false "
              "\n"
              )

        pipeline = p
        log.info("Launching pipeline %s", pipeline)
        pipeline = Gst.parse_launch(pipeline)

        self.imagesink = pipeline.get_by_name('imagesink')
        self.gtksink_widget = self.imagesink.get_property("widget")
        log.info("About to remove children from %r", self)
        for child in self.get_children():
            log.info("About to remove child: %r", child)
            self.remove(child)
        # self.gtksink_widget.set_property("expand", False)
        log.info("Adding sink widget: %r", self.gtksink_widget)
        # self.add(self.gtksink_widget)
        self.pack_start(self.gtksink_widget, True, True, 0)
        self.gtksink_widget.show()

        self.pipeline = pipeline

        bus = pipeline.get_bus()
        bus.connect('message', self.on_message)
        bus.add_signal_watch()

        pipeline.set_state(Gst.State.PLAYING)

    def pause(self):
        self.pipeline.set_state(Gst.State.PAUSED)

    def on_map(self, *args, **kwargs):
        '''It seems this is called when the widget is becoming visible'''
        self.run()

    def on_unmap(self, *args, **kwargs):
        '''Hopefully called when this widget is hidden,
        e.g. when the tab of a notebook has changed'''
        self.pipeline.set_state(Gst.State.PAUSED)
        # Actually, we stop the thing for real
        self.pipeline.set_state(Gst.State.NULL)


def main():

    window = Gtk.Window()
    window.connect('destroy', Gtk.main_quit)

    # Create a gstreamer pipeline with no sink.
    # A sink will be created inside the GstWidget.
    widget = GstWidget()

    window.add(widget)
    window.show_all()

    Gtk.main()

if __name__ == "__main__":
    main()
