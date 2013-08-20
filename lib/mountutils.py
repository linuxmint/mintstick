import os, sys
import commands
from subprocess import Popen,PIPE,call,STDOUT

def do_umount(target):
        mounts = get_mounted(target)
        if mounts:
            print 'Unmounting all partitions of '+target+':'
        for mount in mounts:
            print 'Trying to unmount '+mount[0]+'...'       
            try:
                retcode = call('umount '+mount[0], shell=True)
                if retcode < 0:
                    print 'Error, umount '+mount[0]+' was terminated by signal '+str(retcode)
                    sys.exit(6)
                else:
                    if retcode == 0:
                        print mount[0]+' successfully unmounted'
                    else:
                        print 'Error, umount '+mount[0]+' returned '+str(retcode)
                        sys.exit(6)
            except OSError, e:
                print 'Execution failed: '+str(e)
                sys.exit(6)


def get_mounted(target):
        try:
            lines = [line.strip("\n").split(" ") for line in open ("/etc/mtab", "r").readlines()]
            return [mount for mount in lines if mount[0].startswith(target)]
        except:
             print 'Could not read mtab !'
             sys.exit(6)