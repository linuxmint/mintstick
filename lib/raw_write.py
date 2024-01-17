#!/usr/bin/python3

import os, sys
import argparse
sys.path.append('/usr/lib/mintstick')
from mountutils import do_umount
import parted
import syslog

def raw_write(source, target):
    syslog.syslog(f"Writing '{source}' on '{target}'")
    try:
        do_umount(target)
        bs = 4096
        size=0
        input = open(source, 'rb')
        total_size = float(os.path.getsize(source))

        # Check if the ISO can fit ... :)
        device = parted.getDevice(target)
        device_size = device.getLength() * device.sectorSize
        if device_size < float(os.path.getsize(source)):
            input.close()
            print("nospace")
            exit(3)

        increment = total_size / 100

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
    except Exception as e:
        syslog.syslog("An exception occured")
        syslog.syslog(str(e))
        print("failed")
        exit (4)

def main():
    # parse command line options
    try:
        parser = argparse.ArgumentParser(description="Format USB",
                                         prog="mint-stick-write",
                                         epilog="Example : mint-stick-write -s /foo/image.iso -t /dev/sdj")
        parser.add_argument("-s", "--source", help="Source iso path", type=str, required=True)
        parser.add_argument("-t", "--target", help="Target device path", type=str, required=True)
        args = parser.parse_args()
    except Exception as e:
        print(e)
        sys.exit(2)

    raw_write(args.source, args.target)

if __name__ == "__main__":
    main()
