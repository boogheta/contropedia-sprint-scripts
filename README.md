## Scripts made during the Contropedia sprint (Amsterdam 02/14)

The main script from which everything else runs is `generate_article_threads_data.sh`:

```bash
bash generate_article_threads_data.sh Global_warming
```

To work on the 20 EMAPS samples:
```bash
for id in $(cat pageids.txt); do
  bash generate_article_threads_data.sh "$id"
done
head -n 1 data/Global_warming/threads_matched.csv > data/threads_matched.csv
cat data/*/threads_matched.csv | grep -v "^article_title" >> data/threads_matched.csv
```

