## Scripts made during the Contropedia sprint (Amsterdam 02/14)

These build the data on discussions for a single wikipedia article.

The main script from which everything else runs is `generate_article_threads_data.sh`:

This works using 4 data sources in addition to Wikipedia's API:
- Eric's MySQL contropedia database, which needs to be loaded locally, under the name contropedia and with a user/password set inside a db.inc file to be adapted from db.inc.example
- David's data results on discussions which samples are included in this repo and located in the data directory:
 * top20_discussions_compact_text.csv
 * top20_thread_metrics_tree_string.csv
 * top20_thread_titles.csv
(these currently only include data on the 20 samples, hence the name. If new names are used in the end this will need to be changed inside the generate shell script)

```bash
bash generate_article_threads_data.sh Global_warming
```

To work on the 20 EMAPS samples:
```bash
for id in $(cat pageids.txt); do
  echo "WORKING ON $id"
  bash generate_article_threads_data.sh "$id"
  echo
  echo
done
# Assemble threads data into big ones for multiple articles if needed as such:
head -n 1 data/Global_warming/threads_matched.csv > data/threads_matched.csv
cat data/*/threads_matched.csv | grep -v "^article_title" >> data/threads_matched.csv
head -n 1 data/Global_warming/actors_matched.csv > data/actors_matched.csv
cat data/*/actors_matched.csv | grep -v "^article_title" >> data/actors_matched.csv
```

PS: Some links pointing to the english wikipedia are currently hardcoded and will need to be adapted for international handling.
