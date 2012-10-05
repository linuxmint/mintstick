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

LIBFILES="mintstick.py find_devices.py raw_write.py"
DATAFILES="mintstick.glade"


if [ "$1" = "uninstall" ]; then
    rm -rf /usr/lib/mintstick
    rm -rf /usr/share/mintstick
    rm -r /usr/share/applications/mintstick.desktop
    rm -f /usr/bin/mintstick
    rm -rf /usr/share/polkit-1/actions/org.linuxmint.im.policy
else
    cp share/applications/mintstick.desktop /usr/share/applications/
    cp share/applications/mintstick-kde.desktop /usr/share/applications/
    cp share/polkit/org.linuxmint.im.policy /usr/share/plokit-1/actions
    cp mintstick /usr/bin/
    mkdir -p /usr/lib/mintstick
    mkdir -p /usr/share/mintstick

    for item in $LIBFILES; do
        cp lib/$item /usr/lib/mintstick/
    done

    for item in $DATAFILES; do
        cp share/mintstick/$item /usr/share/mintstick/
    done
fi
