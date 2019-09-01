#!/usr/bin/python3

import subprocess
from subprocess import Popen,PIPE,call,STDOUT
import os, sys
import getopt
sys.path.append('/usr/lib/mintstick')
from mountutils import *
import parted

def raw_write(source, target):
    do_umount(target)
    bs = 4096
    size=0
    input = open(source, 'rb')
    total_size = float(os.path.getsize(source))
    #print total_size

    # Check if the ISO can fit ... :)
    device = parted.getDevice(target)
    device_size = device.getLength() * device.sectorSize
    if (device.getLength() * device.sectorSize) < float(os.path.getsize(source)):
        input.close()
        print("nospace")
        exit(3)

    increment = total_size / 100;

    written = 0
    output = open(target, 'wb')
    while True:
        buffer = input.read(bs)
        if len(buffer) == 0:
            break
        output.write(buffer)
        size = size + len(buffer)
        written = written + len(buffer)
        print(size/total_size)
        if (written >= increment):
            output.flush()
            os.fsync(output.fileno())
            written = 0

    output.flush()
    os.fsync(output.fileno())
    input.close()
    output.close()
    if size == total_size:
        print("1.0")
        exit (0)
    else:
        print("failed")
        exit (4)

def main():
    # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:t:", ["help", "source=","target="])
    except getopt.error as msg:
        print(msg)
        print("for help use --help")
        sys.exit(2)

    for o, a in opts:
        if o in ("-h", "--help"):
            print("Usage: %s -s source -t target\n" % sys.argv[0])
            print("-s|--source          : source iso path")
            print("-t|--target          : target device path\n")
            print("Example : %s -s /foo/image.iso -t /dev/sdj" % sys.argv[0])
            sys.exit(0)
        elif o in ("-s"):
            source = a
        elif o in ("-t"):
            target = a

    argc = len(sys.argv)
    if argc < 5:
        print("Too few arguments")
        print("for help use --help")
        exit(2)

    raw_write(source, target)

if __name__ == "__main__":
    main()
