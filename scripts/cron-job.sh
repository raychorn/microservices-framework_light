#!/bin/bash

size=`df  | grep 'xvdc' | awk '{print $5}' | sed 's/.$//'`
echo $size
if [[ $size -ge 80 ]]; then
    docker system prune -a -f
fi
