#!/bin/bash

page=$(echo $1 | sed 's/ /_/g')
datadir="data/$page"
mkdir -p "$datadir/.cache"

function escapeit {
  perl -e 'use URI::Escape; print uri_escape shift();print"\n"' $1 |
   sed 's/\s/_/g' |
   md5sum | sed 's/\s.*$//';
}
function download {
  cache="$datadir/.cache/$(escapeit $1)"
  if [ ! -s "$cache" ]; then
    echo "DOWNLOAD $1" >&2
    touch "$cache"
    ct=0
    while [ $ct -lt 3 ]; do
      curl -f -s -L "$1" > "$cache.tmp"
      if [ -s "$cache.tmp" ]; then
        mv "$cache.tmp" "$cache"
        break
      fi
    done
  fi
  cat "$cache"
}

# Download the list of all revisions of the page from the API
rootapiurl="https://en.wikipedia.org/w/api.php?action"
revs_url="$rootapiurl=query&prop=revisions&titles=$page&rvprop=ids|user|timestamp|comment|sha1&rvlimit=500&rvdir=newer&format=xml&rvstartid="
# cleanup cache for latest revision list
lastid=0
for file in $(ls $datadir/.cache/*startid%3D* 2> /dev/null | grep -v ".tmp$"); do
  revid=$(echo $file | sed 's/^.*startid%3D//')
  if [ $revid -gt $lastid ]; then
    lastid=$revid
  fi
done
rm -f "$datadir/.cache/"$(escapeit "$revs_url$lastid")
run=true
nextid=0
pageid=
echo -e "rev_id\trev_user\trev_timestamp\trev_hash\trev_comment" > "$datadir/revisions.tsv"
while $run; do
  download "$revs_url$nextid" | sed 's/<rev/\n<rev/g' > "$datadir/revisions.tmp"
  if grep '<revisions rvcontinue="' "$datadir/revisions.tmp" > /dev/null; then
    nextid=$(grep '<revisions rvcontinue="' "$datadir/revisions.tmp" | sed 's/^.*rvcontinue="\([0-9]\+\)".*$/\1/')
  else
    run=false
  fi
  grep '<rev revid="' "$datadir/revisions.tmp"  |
    sed 's/^.*revid="//'                        |
    sed 's/" \/>$//'                            |
    sed 's/" parentid.*user="/\t/'              |
    sed 's/" anon="[^"]*"/"/'                   |
    sed 's/" [^"]\+"/\t/g' >> "$datadir/revisions.tsv"
  if [ -z "$pageid" ]; then
    pageid=$(grep '<page pageid="' "$datadir/revisions.tmp" | head -n 1 | sed 's/^.*pageid="\([0-9]\+\)".*$/\1/')
  fi
  rm "$datadir/revisions.tmp"
done

revisions_ids=$(cat "$datadir/revisions.tsv" | grep -v -P "^rev_id\t" | awk -F "\t" '{print $1}' | tr '\n' ' ' | sed 's/ $//')
revisions_list=$(echo "$revisions_ids" | tr ' ' ',')

# Download list of sections in each revision of the page from the API
if [ ! -s "$datadir/sections.tsv" ]; then
  rm -f "$datadir/sections.tmp"
  for revid in $revisions_ids; do
    download "https://en.wikipedia.org/w/api.php?action=parse&oldid=$revid&prop=sections|revid&format=json"   |
      sed 's/","number/\n/g'     |
      grep -v ']}}'              |
      sed 's/^.*"line":"//'      |
      sed 's/^\(.*\)$/\L\1/' >> "$datadir/sections.tmp"
  done
  sort -u "$datadir/sections.tmp" > "$datadir/sections.tsv"
  rm "$datadir/sections.tmp"
fi

if [ ! -s "$datadir/revisions_sections.tsv" ]; then
  echo "SELECT to_revision_id as revision_id, raw_element as section_name FROM element_edit WHERE to_revision_id IN ($revisions_list) GROUP BY to_revision_id, raw_element" | mysql -u root -p contropedia > "$datadir/revisions_sections.tsv"
fi

# Extract discussions from David's data
head -n 1 data/top20_discussions_compact_text.csv | iconv -f "iso8859-1" -t "utf8" > "$datadir/discussions.tsv"
grep -P "^([^\t]+\t){5}$pageid\t" data/top20_discussions_compact_text.csv | iconv -f "iso8859-1" -t "utf8" >> "$datadir/discussions.tsv"
#Add missing thread_title column
if ! head -n 1 "$datadir/discussions.tsv" | grep -P "\tthread_title$" > /dev/null; then
  ./add_thread_column.sh "$datadir/discussions.tsv" > "$datadir/discussions.tsv.new"
  mv -f "$datadir/discussions.tsv.new" "$datadir/discussions.tsv"
fi

# Extract discussions metrics from David's data
head -n 1 data/top20_thread_metrics_tree_string.csv | iconv -f "iso8859-1" -t "utf8" > "$datadir/threads_metrics.tsv"
grep -P "^$pageid\t" data/top20_thread_metrics_tree_string.csv | iconv -f "iso8859-1" -t "utf8" >> "$datadir/threads_metrics.tsv"

# Extract thread permalinks from David's data
head -n 1 data/top20_thread_titles.csv | iconv -f "iso8859-1" -t "utf8" > "$datadir/threads_links.tsv"
grep -P "^$pageid\t" data/top20_thread_titles.csv | iconv -f "iso8859-1" -t "utf8" >> "$datadir/threads_links.tsv"

# Extract actors from Eric's data
if [ ! -s "$datadir/actors.tsv" ]; then
  echo "SELECT e.canonical FROM element e LEFT JOIN element_edit ee ON ee.element_id = e.id LEFT JOIN section s ON ee.section_id = s.id LEFT JOIN revisions r ON ee.to_revision_id = r.id LEFT JOIN article_revisions ar ON ar.revision_id = r.id LEFT JOIN article a ON ar.article_id = a.id WHERE a.title = '$page' GROUP BY canonical ORDER BY canonical" | mysql -u root -p contropedia > "$datadir/actors.tsv"
fi

# Match discussions with article sections and assemble all data into $datadir/threads_matched.csv
python match_discussions_sections.py "$page"

# Collect HTML and screenshots for all revisions webpages 
# bash get_page_revisions.sh $page

