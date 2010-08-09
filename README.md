xstcache - a cache for Xilinx synthesis tool runs
=================================================

Copyright (c) 2008-2010 
Enno Luebbers <luebbers@reconos.de>, Andreas Agne <agne@upb.de>

Inspired by ccache <http://ccache.samba.org/>.

USAGE:

0. Make sure the real xst executable is in you PATH
1. Copy xstcache.py and xstcache_stats.sh to a directory of your choice 
   (say /usr/local/xstcache)
2. Create a symbolic link to 'xst':
      cd /usr/local/xstcache
      ln -s xstcache.py xst
3. Prepend /usr/local/xstcache to your PATH:
      export PATH/usr/local/xstcache:$PATH    # for bash
4. Run your EDK toolchain aus usual, e.g.:
      cd $MY_EDK_PROJECT
      make -f system.make netlist

The actual cache is stored by default in $HOME/.xstcache
If something goes wrong or you want to start over, just delete that
directory.


