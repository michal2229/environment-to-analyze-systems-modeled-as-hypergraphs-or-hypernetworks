#! /usr/bin/env python3
# -*- coding: utf-8 -*-

## @file application-main.py
## @package application_main

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject

from GuiWindow import GuiWindow

## Część właściwa programu głównego. Nie jest wykonywana, w przypadku importu tego pliku do innego pliku.
if __name__ == "__main__":
    GObject.threads_init()  # init threads?
    

    
    

    ## Obiekt okna aplikacji.
    pa = GuiWindow()
    # GLib.timeout_add(int(1000 * pa.TIME_DELTA_SEC), pa.animate)

    Gtk.main()
