#!/bin/bash
# To run on the wikitools server

page=$(echo $1 | sed 's/ /_/g')
escpage=$(echo $page | sed 's/\(["'"'"']\)/\\\1/g')
echo "$escpage"
pageid=$(sql en "select page_id from page where page_title='$escpage' and page_namespace=0" | grep -v "^page_id")
if [ -z "$pageid" ]; then
	echo "No page found in Wikipedia en DB with this title « $page »"
	exit 1
fi

mkdir -p "data/$page"

sql en "select * from revision where rev_page=$pageid" > "data/$page/revisions.tsv"

sql en "select page_id from page where (page_title LIKE '$escpage/%' OR page_title = '$escpage') AND page_namespace % 2 = 1" > "data/$page/discussions_pageids.tsv"

