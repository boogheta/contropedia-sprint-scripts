tar xzvf all_articles_controversiality.csv.tar.gz
cat all_articles_pages.csv  | awk -F "\t" '{print $2"|"$10}' > controversialities.csv
sqlite3 controversialities.db < load_sqlite3.sql
