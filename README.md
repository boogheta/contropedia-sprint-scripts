## Scripts made during the contropedia sprint (Amsterdam 02/14)

The main script from which everything else runs is ̀ get_page_revisions_infos.sh`:

```bash
bash get_page_revisions_infos.sh Global_warming
```

Or to work on the first 20 EMAPS examples:
```bash
for id in $(cat pageids.txt); do
  bash get_page_revisions_infos.sh "$id"
done
```

