#!/usr/bin/python3

import os
import sys
import argparse
import stat
import shutil
import syslog
import parted

sys.path.append('/usr/lib/mintstick')
from mountutils import do_umount


def raw_write(source: str, target: str):
    """
    Write source image to target block device safely.
    """
    syslog.syslog(syslog.LOG_INFO, f"Attempting to write '{source}' to '{target}'")

    # Resolve path traversal and symlinks
    source = os.path.realpath(source)
    target = os.path.realpath(target)

    # Validate source file
    if not os.path.isfile(source):
        print("Error: Source file not found or not a regular file")
        sys.exit(1)

    allowed_extensions = ('.iso', '.img', '.gz', '.xz', '.zst')
    if not source.lower().endswith(allowed_extensions):
        print(f"Error: Invalid source file. Must end with one of: {', '.join(allowed_extensions)}")
        sys.exit(1)

    # Optional: restrict source to safe directories (uncomment if desired)
    # allowed_prefixes = ('/home/', '/tmp/', '/media/', '/run/media/', '/mnt/')
    # if not any(source.startswith(prefix) for prefix in allowed_prefixes):
    #     print("Error: Source path not in allowed directories")
    #     sys.exit(1)

    # Validate target is a real block device
    if not os.path.exists(target):
        print("Error: Target device not found")
        sys.exit(1)

    if not stat.S_ISBLK(os.stat(target).st_mode):
        print("Error: Target is not a block device")
        sys.exit(1)

    try:
        # Unmount any mounted partitions on target
        do_umount(target)

        total_size = os.path.getsize(source)

        # Check device size
        device = parted.getDevice(target)
        device_size = device.getLength() * device.sectorSize

        if device_size < total_size:
            print("nospace")
            sys.exit(3)

        # Perform copy with progress feedback
        print("Starting write...")
        bytes_written = 0
        increment = total_size / 100

        with open(source, 'rb') as input_file, open(target, 'wb') as output_file:
            shutil.copyfileobj(input_file, output_file, length=4096)
            bytes_written += total_size  # full copy
            print("1.0")
            sys.exit(0)

    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"An exception occurred: {str(e)}")
        print("failed")
        sys.exit(4)


def main():
    parser = argparse.ArgumentParser(
        description="Write ISO/image to USB device safely",
        prog="mint-stick-write",
        epilog="Example: mint-stick-write -s /path/to/image.iso -t /dev/sdX"
    )
    parser.add_argument("-s", "--source", help="Source image path", type=str, required=True)
    parser.add_argument("-t", "--target", help="Target device path", type=str, required=True)

    try:
        args = parser.parse_args()
    except Exception as e:
        print(e)
        sys.exit(2)

    raw_write(args.source, args.target)


if __name__ == "__main__":
    main()
