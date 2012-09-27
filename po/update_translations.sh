#!/bin/sh
#
# Copyright: 2007-2009 Canonical Ltd.
#
#  This program is free software; you can redistribute it and/or 
#  modify it under the terms of the GNU General Public License as 
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA

LANGS="de_DE"

intltool-extract --type=gettext/glade ../share/usb-imagewriter/imagewriter.xml
xgettext --language=Python --keyword=_ --keyword=N_ --output=imagewriter.pot ../lib/imagewriter.py ../share/usb-imagewriter/imagewriter.xml.h
rm -f ../share/usb-imagewriter/imagewriter.xml.h

# to create a lang specific .po file, run (replace de_DE and de.po with your data):
#msginit --input=imagewriter.pot --locale=de_DE -o de.po

# to create the actual messagefiles use:
#msgfmt --output-file=de/LC_MESSAGES/usb-imagewriter.mo de.po 
