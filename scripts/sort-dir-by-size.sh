#!/bin/bash 
 
if [ $# != 2 ]; then 
	echo "Incorrect number of arguments !" >&2 
	echo "USAGE: sortdirbysize [DIRECTORY] <first n directories>" 
fi 
du --block-size=1M --max-depth 1 $1 | sort -rn | head -$2
