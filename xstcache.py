#!/usr/bin/pyhton
#
# \file xstcache.py
#
# A cache for Xilinx synthesis tool runs
#
# Inspired by ccache.
# USAGE:
#
# 0. Make sure the real xst executable is in you PATH
# 1. Copy xstcache.py and xstcache_stats.sh to a directory of your choice 
#    (say /usr/local/xstcache)
# 2. Create a symbolic link to 'xst':
#       cd /usr/local/xstcache
#       ln -s xstcache.py xst
# 3. Prepend /usr/local/xstcache to your PATH:
#       export PATH/usr/local/xstcache:$PATH    # for bash
# 4. Run your EDK toolchain aus usual, e.g.:
#       cd $MY_EDK_PROJECT
#       make -f system.make netlist
#
# The actual cache is stored by default in $HOME/.xstcache
# If something goes wrong or you want to start over, just delete that
# directory.
#
# \author Enno Luebbers <luebbers@reconos.de>, Andreas Agne <agne@upb.de>
# \date   28.03.2008
#
#---------------------------------------------------------------------------
# Copyright (c) 2006-2010
# Enno Luebbers <luebbers@reconos.de>, Andreas Agne <agne@upb.de>
# 
# All rights reserved.
# 
# xstcache is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
# 
# xstcache is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# 
# You should have received a copy of the GNU General Public License along
# with xstcache.  If not, see <http://www.gnu.org/licenses/>.
#---------------------------------------------------------------------------
#

import sys, os, subprocess, re, string, select, signal, hashlib, shutil, time

loglevel = 666
cachepath = os.environ.get('HOME') + '/.xstcache'


def log(level, str):
    if loglevel >= level:
        f = open(cachepath + '/log', 'a')
        print >> f, str
        f.close()


def getInputFiles(args):
    """
Finds all files that would be used by an XST process with the command line
arguments 'args'.
Returns a list with all files.
"""

    infiles = []
    intrigger = False

    for a in args:
        if intrigger:
            intrigger = False
            # this file is relevant for checksumming
            infiles.append(a)

            # if the file is a .scr, read it and
            # feed it into getInputFiles() again
            if re.search('\.scr$', a):
                f = open(a)
                content = f.read()
                f.close()
                content = content.split()
                infiles += getInputFiles(content)

            # if the file is a .prj, parse it for
            # vhdl/verilog files
            elif re.search('\.prj$', a):
                f = open(a)
                lines = f.readlines()
                f.close()

                for l in lines:
                    components = l.split()
                    if len(components) == 3:
                        infiles.append(components[-1])

            continue

        if a == '-ifn':
            intrigger = True  # next arg is interesting
            continue

    return infiles
    

def generateChecksum(files, args):
    """
Generates a checksum over all files in 'files'.
"""
    contents = args[:]
    for name in files:
        f = open(name)
        contents.append(f.read())
        f.close()
    text = string.join(contents, '\n')

    return hashlib.md5(text).hexdigest()



def runXST(me, args):
    """
Runs the 'real' XST tool and captures stdout, stderr, and the return value.
Returns retval, stdout, stderr. The latter are lists of strings.
"""

    # remove ourselves from PATH
    oldpath = os.environ.get('PATH')

    # find out own directory
#    mypath = re.sub('/[^/]*$', '', me);
    mypath = os.path.dirname(me)

    # change PATH
    newpath = re.sub(mypath +  '/?:?', '', oldpath)

#    print "ME: " + me
#    print "MYPATH: " + mypath
#    print "OLD: " + oldpath
#    print "NEW: " + newpath

    # find XST executable
    paths = newpath.split(':')
    for p in paths:
        if os.path.isdir(p):
            files = os.listdir(p)
            if 'xst' in files:
                xstpath = p + "/xst"
                log(2, "Found XST executable: " + xstpath)
                break

    # run XST
    start = time.time()
    command = "strace -e trace=open -f -o /tmp/xstcache.log " + xstpath + ' ' + string.join(args, ' ')
    log(2, "Executing: " + command)
    p = subprocess.Popen(command, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

    # capture stdout and stderr
    ins = [p.stdout, p.stderr]
    out = []
    err = []
    try:
        while p.returncode == None:
            i,o,e = select.select(ins, [], [])
            for x in i:
                if x is p.stdout:
                    line = p.stdout.readline()
                    if line != '':
                        print line,
                        out.append(line)
                if x is p.stderr:
                    line = p.stderr.readline()
                    if line != '':
                        print >> sys.stderr, line,
                        err.append(line)
            p.poll()
        retval = p.returncode
    except KeyboardInterrupt:
        print "caught CTRL+C, killing subprocess"
        os.kill(p.pid, signal.SIGTERM)
        sys.exit(-1)
    finally:
        p.stdout.close()
        p.stderr.close()
	
    elapsed = time.time() - start

    return retval, out, err, elapsed



def saveCache(chksum, retval, out, err, outfiles, elapsed):
    """
Save all produced files by an xst run to a cache dir.
"""
    targetdir = cachepath + '/' + chksum
    if os.path.exists(targetdir):
        print >> sys.stderr, 'ERROR: cache dir ' + targetdir + ' already exists.'
        sys.exit(-1)

    log(2, "Creating " + targetdir)
    os.mkdir(targetdir)

    # save return value
    log(2, "Saving retval to " + targetdir + '/retval')
    retvalfile = open(targetdir + '/retval', 'w')
    retvalfile.write(str(retval))
    retvalfile.close()
    
    # save output files
    for ofn in outfiles:
        if os.path.exists(ofn):
            dst = targetdir + '/' + os.path.basename(ofn)
            log(2, "Copying " + ofn + " to " + dst)
            shutil.copyfile(ofn, dst)

    # save stdout
    log(2, "Saving stdout to " + targetdir + '/stdout')
    stdoutfile = open(targetdir + '/stdout', 'w')
    stdoutfile.write(string.join(out, ''))
    stdoutfile.close()

    # save stderr
    log(2, "Saving stderr to " + targetdir + '/stderr')
    stderrfile = open(targetdir + '/stderr', 'w')
    stderrfile.write(string.join(err, ''))
    stderrfile.close()

    # save list of output files
    log(2, "Saving list of output files to " + targetdir + '/outfiles')
    o = open(targetdir + '/outfiles', 'w')
    o.write(string.join(outfiles, '\n'))
    o.close()

    # save elapsed time during XST run for statistics
    log(2, "Saving elapsed time (" + str(elapsed) + ") to " + targetdir + '/elapsed')
    e = open(targetdir + '/elapsed', 'w')
    e.write(str(elapsed))
    e.close()
    
    return True


def isCached(chksum):
    return os.path.exists(cachepath + '/' + chksum)


def emulateXST(chksum):
    """
Emulates an XST run, recreating 'outfiles' and grabbing stdout and stderr
as well as the retval from the cache entry 'chksum'.
"""
    if not isCached(chksum):
        print >> sys.stderr, 'No cache entry under ' + chksum
        sys.exit(-2)
    
    start = time.time()

    targetdir = cachepath + '/' + chksum

    outfiles = open(targetdir + "/outfiles", "r").readlines()
    outfiles = map(lambda x: x.strip(), outfiles)
    
    # restore output files
    for ofn in outfiles:
        src = targetdir + '/' + os.path.basename(ofn)
        if os.path.exists(src):
            log(2, "Copying " + src + " to " + ofn)
            shutil.copyfile(src, ofn)

    # print stderr
    log(2, "Printing stderr")
    stderrfile = open(targetdir + '/stderr')
    print >> sys.stderr, stderrfile.read(),
    stderrfile.close()

    # print stdout
    log(2, "Printing stdout")
    stdoutfile = open(targetdir + '/stdout')
    print stdoutfile.read(),
    stdoutfile.close()

    # return retval
    retvalfile = open(targetdir + '/retval')
    retval = retvalfile.read()
    retvalfile.close()

    # read elapsed time of original run
    e = open(targetdir + '/elapsed')
    elapsed_orig = float(e.read())
    e.close()

    elapsed_emu = time.time() - start
    saved = elapsed_orig - elapsed_emu
    
    return retval, saved

def isOutfile(fname):
	ext = [".edn",".ngo",".ngc",".srp"]
	for e in ext:
		if fname.endswith(e): return True
	return False
   
def findOutfiles(trace):
	lines = open(trace,"r").readlines()
	creat = filter(lambda x: ("O_CREAT" in x) and not ("/tmp" in x), lines)
	outfiles = map(lambda x: x.split("\"")[1], creat) #" # jedit
	outfiles = filter(lambda x: isOutfile(x), outfiles)
	return outfiles
	
if __name__ == "__main__":

    if not os.path.exists(cachepath):
        os.mkdir(cachepath)
        log(1, 'cache path at ' + cachepath + ' does not exist. Created.')
 
    log(2, "-------------")
    log(2, "xstcache: invoked from " + os.getcwd() + " with cmdline arguments:")
    for s in sys.argv[1:]:
        log(2, s)
    log(2, "-------------")
    
    infiles = getInputFiles(sys.argv[1:])
    
    log(3, "infiles:")
    for infile in infiles:
        log(3, infile)
    
    # Prevent the input file names from being included in the hash (only
    # the content matters)
    args = []
    for a in sys.argv[1:]:
	if not a in infiles: args.append(a)

    chksum = generateChecksum(infiles, args)

    if isCached(chksum):
        log(1, "hit : " + chksum)
        retval, saved = emulateXST(chksum)
        log(1, "saved " + str(int(saved)) + " seconds")
        log(2, "Returning " + str(retval))
        sys.exit(int(retval))
    else:
        log(1, "miss: " + chksum)
        retval, out, err, elapsed = runXST(sys.argv[0], sys.argv[1:])
        outfiles = findOutfiles("/tmp/xstcache.log")
	log(3, "outfiles:")
        for outfile in outfiles:
            log(3, outfile)
        saveCache(chksum, retval, out, err, outfiles, elapsed)


