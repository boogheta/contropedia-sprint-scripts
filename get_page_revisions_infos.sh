#!/bin/bash

mkdir -p data
page=$(echo $1 | sed 's/ /_/g')

# Collect data from the Wikipedia SQL DB on the wikitools machine
if [ ! -d "data/$page" ] || [ ! -z $2 ]; then
  scp -r "wikitools:~/data/$page" data/
fi
if [ ! -s "data/$page/revisions.tsv" ]; then
  echo "No list of revisions found for $page"
  echo "Did you run get_revisions from wikitools yet?"
  exit 1
fi

pageid=$(head -n 2 "data/$page/revisions.tsv" | tail -n 1 | awk -F "\t" '{print $2}')
mkdir -p "data/$page/versions/" "data/$page/screenshots/"

# Extract discussions from David's data
#head -n 1 data/discussions_compact_text_sections.csv | iconv -f "iso8859-1" -t "utf8" > "data/$page/discussions.tsv"
#grep -P "^([^\t]+\t){5}$pageid\t" data/discussions_compact_text_sections.csv | iconv -f "iso8859-1" -t "utf8" >> "data/$page/discussions.tsv"
if ! head -n 1 "data/$page/discussions.tsv" | grep -P "\tthread$" > /dev/null; then
  ./add_thread_column.sh "data/$page/discussions.tsv" > "data/$page/discussions.tsv.new"
  mv -f "data/$page/discussions.tsv.new" "data/$page/discussions.tsv"
fi

