#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

from lxml import etree
from datetime import datetime

from utilities.constants import Paths
from gui import about

# Import our own modules
from widget_manager import WidgetManager
from widget_chooser import WidgetChooser
from screen_chooser import ScreenChooser
from widget_window import WidgetWindow
from screen_stack import ScreenStack
from widget_area import WidgetArea
from header_bar import HeaderBar

from utilities import ini_info

# Set up logging
from utilities import logger
log = logger.get(__name__)

class HazzyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)

        # Get the XML file path
        self.xml_file = ini_info.get_xml_file()

        self.widget_manager = WidgetManager()

        self.connect('button-press-event', self.on_button_press)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.box)

        self.header_bar = HeaderBar(self, title='Hazzy')
        self.set_titlebar(self.header_bar)

        self.overlay = Gtk.Overlay()
        self.box.pack_start(self.overlay, True, True, 0)

        self.screen_stack = ScreenStack()
        self.overlay.add(self.screen_stack)

        self.stack_switcher = Gtk.StackSwitcher()
        self.stack_switcher.set_stack(self.screen_stack)
        self.header_bar.set_custom_title(self.stack_switcher)

        self.widget_chooser = WidgetChooser()
        self.overlay.add_overlay(self.widget_chooser)

        self.screen_chooser = ScreenChooser()
        self.overlay.add_overlay(self.screen_chooser)

        self.menu_button = Gtk.MenuButton()
        self.menu_button.set_popover(self.make_menu_popover())
        self.header_bar.pack_start(self.menu_button)

        self.set_size_request(900, 600)


    def make_menu_popover(self):
        #Create a menu popover - very temporary, need to do something neater
        popover = Gtk.PopoverMenu.new()

        pbox = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        pbox.set_property('margin', 10)
        popover.add(pbox)

        edit = Gtk.CheckButton.new()
        edit.set_label("Edit Layout")
        edit.set_active(True)
        edit.connect('toggled', self.on_edit_layout_toggled)
        pbox.pack_start(edit, False, False, 5)

        about = Gtk.ModelButton.new()
        about.set_label("About")
        about.connect('clicked', self.on_show_about_clicked)
        pbox.pack_start(about, False, False, 5)

        quit = Gtk.ModelButton.new()
        quit.set_label("Quit")
        quit.connect('clicked', Gtk.main_quit)

        pbox.pack_start(quit, False, False, 5)
        pbox.show_all()

        return popover

    def on_button_press(self, widget, event):
        # Remove focus when clicking on non focusable area
        self.get_toplevel().set_focus(None)

    def on_show_widget_choser_clicked(self, widget):
        visible = self.widget_chooser.get_visible()
        self.widget_chooser.set_visible(not visible)

    def on_show_screen_choser_clicked(self, widget):
        visible = self.screen_chooser.get_visible()
        self.screen_chooser.set_visible(not visible)

    def on_edit_layout_toggled(self, widget):
        edit = widget.get_active()
        # Hide eventbox used for drag/resize
        screens = self.screen_stack.get_children()
        for screen in screens:
            widgets = screen.get_children()
            for widget in widgets:
                widget.show_overlay(edit)

    def on_show_about_clicked(self, widegt):
        about.About(self)

    def set_gtk_theme(self, theme=None):
        settings = self.get_settings()
        if not theme:
            theme = settings.get_default().get_property("gtk-theme-name")
        settings.set_string_property("gtk-theme-name", theme, "")

    def set_icon_theme(self, theme=None):
        settings = self.get_settings()
        if not theme:
            theme = settings.get_default().get_property("gtk-icon-theme-name")
        settings.set_string_property("gtk-icon-theme-name", theme, "")

    def load_from_xml(self):

        if not os.path.exists(self.xml_file):
            return

        try:
            tree = etree.parse(self.xml_file)
        except etree.XMLSyntaxError as e:
            error_str = e.error_log.filter_from_level(etree.ErrorLevels.FATAL)
            log.error(error_str)
            return

        root = tree.getroot()

        # Windows (Might support multiple windows in future, so iterate)
        for window in root.iter('window'):
            window_name = window.get('name')
            window_title = window.get('title')

            props = self.get_propertys(window)

            self.set_default_size(int(props['w']), int(props['h']))
            self.move(int(props['x']), int(props['y']))
            self.set_maximized(props['maximize'])
            self.set_fullscreen(props['fullscreen'])

            # Add screens
            screens = []
            for screen in window.iter('screen'):
                screen_obj = WidgetArea()
                screen_name = screen.get('name')
                screen_title = screen.get('title')
                screen_pos = int(screen.get('position'))

                self.screen_stack.add_screen(screen_obj, screen_name, screen_title)
                self.screen_stack.child_set_property(screen_obj, 'position', screen_pos)
                screens.append(screen_name)

                # Add widgets
                for widget in screen.iter('widget'):
                    package = widget.get('package')
                    if not self.widget_manager.check_exist(package):
                        log.error('The package "{}" could not be found'.format(package))
                        continue
                    obj, title, size = self.widget_manager.get_widget(package)
                    wwindow = WidgetWindow(package, obj, title)

                    props = self.get_propertys(widget)

                    screen_obj.put(wwindow, int(props['x']), int(props['y']))
                    wwindow.set_size_request(int(props['w']), int(props['h']))

        self.screen_chooser.view.fill_iconview(screens)


    def save_to_xml(self):

        # Create XML root element & comment
        root = etree.Element("hazzy_interface")
        root.append(etree.Comment('Interface for: {}'.format(Paths.MACHINE_NAME)))

        # Add time stamp
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        root.append(etree.Comment('Last modified: {}'.format(time_str)))

        # Main window size & position (TODO need to iterate to support multi window)
        win = etree.SubElement(root, "window")
        win.set('name', 'Window 1')
        win.set('title', 'Main Window')

        self.set_property(win, 'maximize', self.header_bar.window_maximized)
        self.set_property(win, 'fullscreen', self.header_bar.window_fullscreen)

        x = self.get_position().root_x
        y = self.get_position().root_y
        w, h = self.get_size()

        for prop, value in zip(['x','y','w','h'], [x,y,w,h]):
            self.set_property(win, prop, value)

        # Screens
        screens = self.screen_stack.get_children()
        for screen in screens:
            screen_name = self.screen_stack.child_get_property(screen, 'name')
            screen_title = self.screen_stack.child_get_property(screen, 'title')
            screen_pos = self.screen_stack.child_get_property(screen, 'position')

            scr = etree.SubElement(win, "screen")
            scr.set('name', screen_name)
            scr.set('title', screen_title)
            scr.set('position', str(screen_pos))

            # Widgets
            widgets = screen.get_children()
            for widget in widgets:
                wid = etree.SubElement(scr, "widget")
                wid.set('package', widget.module_package)

                x = screen.child_get_property(widget, 'x')
                y = screen.child_get_property(widget, 'y')
                w = widget.get_size_request().width
                h = widget.get_size_request().height

                for prop, value in zip(['x','y','w','h'], [x,y,w,h]):
                    self.set_property(wid, prop, value)

        with open(self.xml_file, 'w') as fh:
            fh.write(etree.tostring(root, pretty_print=True))

# Helpers

    def set_property(self, parent, name, value):
        prop = etree.SubElement(parent, 'property')
        prop.set('name', name)
        prop.text = str(value)

    def get_propertys(self, parent):
        props = {}
        for prop in parent.iterchildren('property'):
            props[prop.get('name')] = prop.text
        return props

    def set_maximized(self, maximized):
        if maximized == 'True':
            self.maximize()
        else:
            self.unmaximize()

    def set_fullscreen(self, fullscreen):
        if fullscreen == 'True':
            self.fullscreen()
        else:
            self.unfullscreen()
