#!/bin/bash

infile=$1
s=""
headdone=false
cat "$1"        |
  tr '\r' ' '   |
  while read l; do
    l=$(echo "$l" | sed 's/<LF>\s*/<LF>/g')
    if echo "$l" | grep -P "\t=+[^\t]+=+$" > /dev/null; then
      s=$(echo "$l" | perl -pe 's/^.*\t=+([^\t].*?)=+$/\1/')
    fi
    if ! $headdone; then
      echo -e "$l\tthread_title"
      headdone=true
    else
      echo -e "$l\t$s"
    fi
  done
