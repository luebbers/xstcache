#!/bin/bash
#
# \file xstcache_stats.sh
#
# Display statistics about current xstcache usage
#
# \author Enno Luebbers <luebbers@reconos.de>
# \date   28.03.2008
#
#---------------------------------------------------------------------------
# This file is part of xstcache (http://github.com/luebbers/xstcache).
#
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


CACHEPATH="$HOME/.xstcache"

# count hits an misses
HITS=`grep "^hit :" $CACHEPATH/log | wc -l`
MISSES=`grep "^miss:" $CACHEPATH/log | wc -l`

# count entries
ENTRIES=`ls -1 $CACHEPATH | wc -l`

# count sizes
SIZE=`du -sh $CACHEPATH | awk '{ print $1 }'`

# count saved time
SAVED=$[`grep "^saved" ${CACHEPATH}/log | awk '{print $2}' | tr '\n' '+' | sed "s/\+$//"`]
SAVED_H=$[${SAVED}/3600]
SAVED_M=$[${SAVED}/60 - (${SAVED_H} * 60)]
SAVED_S=$[${SAVED} - (${SAVED_H} * 3600) - (${SAVED_M} * 60)]

echo "xstcache statistics:"
echo
echo "      Cache entries: $ENTRIES"
echo "      Cache size:    $SIZE"
echo "      Cache hits:    $HITS"
echo "      Cache misses:  $MISSES"
echo "      Time saved:    ${SAVED_H}h ${SAVED_M}m ${SAVED_S}s"
