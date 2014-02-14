#!/bin/bash

PATH=$PATH:$(pwd)/phantomjs-1.9.7-linux-i686/bin

page=$(echo $1 | sed 's/ /_/g')
mkdir -p "data/$page/versions/" "data/$page/screenshots/"

baseurl="https://en.wikipedia.org/w/index.php?title=$page&oldid="
# Download text and screenshots for each revisions
for revid in $(cat "data/$page/revisions.tsv" | awk -F "\t" '{print $1}' | grep -v "^rev_id"); do
  revid=$(printf "%08d" $revid)
  ct=0
  while [ $ct -lt 3 ] && [ ! -s "data/$page/versions/$revid.html" ]; do
    echo "Download HTML for rev $revid of $page"
    curl -f -s -L "$baseurl$revid" > "data/$page/versions/$revid.html"
    ct=$(($ct+1))
  done
  ct=0
  while [ $ct -lt 3 ] && [ ! -s "data/$page/screenshots/$revid.png" ]; do
    echo "Download PNG screenshot for rev $revid of $page"
    phantomjs wikiphantom.js "$page" "$revid"
    ct=$(($ct+1))
  done
done

mencoder "mf://data/$page/screenshots/*.png" -o "data/$page/history.avi" -ovc lavc -lavcopts vcodec=mjpeg -mf fps=10
