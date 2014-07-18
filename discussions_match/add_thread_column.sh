#!/bin/bash

infile=$1
s=""
headdone=false
cat "$1"        |
  tr '\r' ' '   |
  while read l; do
    # Cleanup bad tabulations left inside some comments
    l=$(echo "$l" | sed 's/<LF>\s*/<LF>/g')
    # Find thread title within corresponding lines 
    if echo "$l" | grep -P "\t=+[^\t]+=+$" > /dev/null; then
      s=$(echo "$l" | perl -pe 's/^.*\t=+([^\t].*?)=+$/\1/')
    fi
    # Add it as a column whenever required
    if ! $headdone; then
      echo -e "$l\tthread_title"
      headdone=true
    else
      echo -e "$l\t$s"
    fi
  done
