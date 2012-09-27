#!/bin/sh
#
#    Copyright 2007-2009 Canonical Ltd.
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

LIBFILES="imagewriter.py find_devices.py raw_write.py"
DATAFILES="imagewriter.xml"


if [ "$1" = "uninstall" ]; then
    rm -rf /usr/lib/imagewriter
    rm -rf /usr/share/imagewriter
    rm -r /usr/share/applications/imagewriter.desktop
    rm -f /usr/bin/imagewriter
    rm -rf /usr/share/polkit-1/actions/org.linuxmint.im.policy
else
    cp share/applications/imagewriter.desktop /usr/share/applications/
    cp share/applications/imagewriter-kde.desktop /usr/share/applications/
    cp share/polkit/org.linuxmint.im.policy /usr/share/plokit-1/actions
    cp imagewriter /usr/bin/
    mkdir -p /usr/lib/imagewriter
    mkdir -p /usr/share/imagewriter

    for item in $LIBFILES; do
        cp lib/$item /usr/lib/imagewriter/
    done

    for item in $DATAFILES; do
        cp share/usb-imagewriter/$item /usr/share/imagewriter/
    done
fi
