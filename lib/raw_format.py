#!/usr/bin/python

import commands
from subprocess import Popen,PIPE,call,STDOUT
import os, sys
import getopt
import parted
sys.path.append('/usr/lib/mintstick')
from mountutils import *

def raw_format(device_path, fstype):
  
    do_umount(device_path)
    
    # First erase MBR and partition table , if any
    os.system ("dd if=/dev/zero of=%s bs=512 count=1 >/dev/null 2>&1" % device_path)
    
    device = parted.getDevice(device_path)
    
    # Create a default partition set up                        
    disk = parted.freshDisk(device, 'msdos')
    disk.commit()
    regions = disk.getFreeSpaceRegions()
    
    if len(regions) > 0:
        #print "Build partition"
        # Define size
        region = regions[-1]      
        start = parted.sizeToSectors(1, "MiB", device.sectorSize)
        #print "start %s" % start
        end = device.getLength() - start - 1024
        #print end
        
        # Alignment
        cylinder = device.endSectorToCylinder(end)
        end = device.endCylinderToSector(cylinder)
        try:
            geometry = parted.Geometry(device=device, start=start, end=end)
        except:
            print "Geometry error - Can't create partition"
            sys.exit(5)
        
        # fstype
        fs = parted.FileSystem(type=fstype, geometry=geometry)
        
        # Create partition
        partition = parted.Partition(disk=disk, type=parted.PARTITION_NORMAL, geometry=geometry, fs=fs)
        constraint = parted.Constraint(exactGeom=geometry)
        disk.addPartition(partition=partition, constraint=constraint)
        disk.commit()
        
        # Format partition according to the fstype specified
        if fstype == "fat32":
            os.system("mkdosfs -F 32 %s >/dev/null 2>&1" % partition.path)
        elif fstype == "ext4":
            os.system("mkfs.ext4 %s >/dev/null 2>&1" % partition.path) 
    sys.exit(0)





def main():
    # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:f:", ["help", "device=","filesystem="])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)

    for o, a in opts:
        if o in ("-h", "--help"):
            print "Usage: %s -d device -f filesystem\n"  % sys.argv[0]
            print "-d|--device          : device path"
            print "-f|--filesystem      : filesystem\n"
            print "Example : %s -d /dev/sdj -f fat32" % sys.argv[0]
            sys.exit(0)
        elif o in ("-d"):
            device = a
        elif o in ("-f"):
            if a not in [ "fat32", "ext4" ]:
                print "Specify either fat32 or ext4"
                sys.exit(3)
            fstype = a
    
    argc = len(sys.argv)
    if argc < 5:
      print "Too few arguments"
      print "for help use --help"
      exit(2)
    
    raw_format(device, fstype)
    
if __name__ == "__main__":
    main()
