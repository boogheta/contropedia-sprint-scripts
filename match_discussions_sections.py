#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, re
import csv, json
import htmlentitydefs
from time import mktime, strptime
from datetime import date, datetime
from locale import setlocale, LC_ALL
setlocale(LC_ALL, 'en_GB.utf8')

try:
    datadir = "data/%s" % sys.argv[1]
    os.chdir(datadir)
    with open('discussions.tsv') as csvf:
        discussions = list(csv.DictReader(csvf, delimiter="\t"))
    with open('revisions.tsv') as csvf:
        revisions = list(csv.DictReader(csvf, delimiter="\t"))
    with open('sections.tsv') as csvf:
        section_titles = csvf.read().split('\n')
    with open('threads_metrics.tsv') as csvf:
        metrics = list(csv.DictReader(csvf, delimiter="\t"))
except Exception as e:
    sys.stderr.write("ERROR trying to read data")
    sys.stderr.write("%s: %s" % (type(e), e))
    sys.exit(1)

def safe_utf8_decode(t):
    try:
        return t.decode('utf-8')
    except:
        try:
            return t.decode('iso8859-1')
        except:
            return t
parse_ts = lambda t: date.isoformat(datetime.fromtimestamp(t))
parse_date = lambda d: parse_ts(mktime(strptime(d.split(', ')[1].replace("(UTC)", "").strip(), "%d %B %Y")))
SPACES = ur'[  \s\t\u0020\u00A0\u1680\u180E\u2000-\u200F\u2028-\u202F\u205F\u2060\u3000]'
re_clean_blanks = re.compile(r'%s+' % SPACES)
clean_blanks = lambda x: re_clean_blanks.sub(r' ', x.strip()).strip()
re_entities = re.compile(r'&([^;]+);')
unescape_html = lambda t: clean_blanks(re_entities.sub(lambda x: unichr(int(x.group(1)[1:])) if x.group(1).startswith('#') else unichr(htmlentitydefs.name2codepoint[x.group(1)]), safe_utf8_decode(t)).encode('utf-8'))
re_talk = re.compile(r'\[\[Talk:.*#([^\|]+)\|?.*\]\]')
re_abstract = re.compile(r'(^|\W)(intro(duction)?|abstract|lead|summar(y|ies)|preamble|headers?)(\W|$)', re.I)
clean_thread_name = lambda t: unescape_html(t).replace('_', ' ').strip('"[]()«» !?~<>.').strip("'")
re_clean_lf = re.compile(r'\s*<LF>\s*', re.I)
re_clean_text = re.compile(r'[^\w\d]+')
re_clean_spec_chars = re.compile(r'[^\w\d\s]')
clean_text = lambda t: re_clean_text.sub(' ', re_clean_lf.sub('', unescape_html(t))).lower().strip()
re_text_splitter = re.compile(r"[^\w\d']+")
is_null_col = lambda x: not x or x in ["", "0", "-1"]

# Prepare threads data
thread = None
threads = []
curthread = ""
threadidx = {}
for row in discussions:
    if not row['thread']:
        continue
    idx = len(threads)
    th = clean_thread_name(row['thread'])
    if th != curthread:
        curthread = th
        if thread:
            threads.append(thread)
        thread = {"index": idx,
                  "name": th,
                  "date_min": "",
                  "users": [],
                  "nb_users": 0,
                  "messages": [],
                  "nb_messages": 0,
                  "users_hindex": 0,
                  "max_depth": 0,
                  "tree_hindex": 0,
                  "chains_num": 0,
                  "chains_comments": 0,
                  "fulltext": "",
                  "revisions": [],
                  "article_sections": [],
                  "match": 0}
        threadidx[th.lower()] = idx
    if is_null_col(row["timestamp"]):
        curthread = th
        continue
    dt = parse_ts(int(row['timestamp'])*60)
    if not thread['date_min']:
        thread['date_min'] = dt
    thread['date_max'] = dt
    us = row["author_name"].strip()
    if us not in thread["users"]:
        thread['users'].append(us)
        thread['nb_users'] += 1
    thread['nb_messages'] += 1
    thread['messages'].append(row)
    thread['fulltext'] += " " + clean_text(row["text"])
threads.append(thread)

# Complete threads with David's precomputed metrics
for row in metrics:
    t = clean_thread_name(row['thread']).lower()
    if t in threadidx:
        for f in ["users_hindex", "max_depth", "tree_hindex", "chains_num", "chains_comments"]:
            threads[threadidx[t]][f] = int(row[f])
    else:
        sys.stderr.write("ERROR: could not match one thread from metrics: %s\n" % t)

# Look for revisions referencing a thread as comment
for row in revisions:
    src = re_talk.search(row["rev_comment"])
    if src:
        t = clean_thread_name(src.group(1)).lower()
        if t in threadidx:
            print "MATCH FOUND:", row["rev_id"], t
            threads[threadidx[t]]['revisions'].append(row['rev_id'])
            threads[threadidx[t]]['match'] += 1

# Look for article sections within thread names
sections = {}
allsections = ""
for section in section_titles:
    s = clean_thread_name(section).lower()
    if s not in sections:
        sections[s] = section
    allsections += " | " + s
    if len(s) > 5:
        for t in threads:
            re_match_s = re.compile(r"%s" % re_clean_spec_chars.sub(".", s))
            if 2*len(re_match_s.findall(t['fulltext'])) > t['nb_messages']:
                print "MATCH maybe FOUND:", t['name'], "/", section
                t['article_sections'].append(section)
                t['match'] += 1
for thread in threadidx:
    if thread in sections:
        print "MATCH FOUND:", thread, "/", sections[thread]
        threads[threadidx[thread]]['article_sections'].append(sections[thread])
        threads[threadidx[thread]]['match'] += 1
    else:
        for section in sections:
            n_words = len(re_text_splitter.split(section))
            if section in thread and 3 < len(section) and (n_words > 1 or 10 * n_words > len(re_text_splitter.split(thread))):
                print "MATCH probably FOUND:", thread, "/", sections[section]
                for test in threads[threadidx[thread]]['article_sections']:
                    tmps = clean_thread_name(section).lower()
                    if test in tmps and test != tmps:
                        print " -> probably better than match with « %s », removing it" % test
                        threads[threadidx[thread]]['article_sections'].remove(test)
                        threads[threadidx[thread]]['match'] -= 1
                threads[threadidx[thread]]['article_sections'].append(sections[section])
                threads[threadidx[thread]]['match'] += 1
    if re_abstract.search(thread):
        print "MATCH probably GUESSED:", thread, "/", "abstract"
        threads[threadidx[thread]]['article_sections'].append("asbtract")
        threads[threadidx[thread]]['match'] += 1

matches = sum([1 for t in threads if t['match'] > 0])
print "=================="
print "FOUND %d matches out of %d threads (%s)" % (matches, len(threadidx), str(matches*100/len(threadidx))+"%")
print "=================="
print "MISSINGS:"
for t in threads:
    if not 'max_depth' in t:
        th = clean_thread_name(t['name']).lower()
        print "WARNING Can't find max_depth in %s" % th
    if False and not t['match']:
        print t['name'], t['nb_messages'], t['nb_users']

with open('threads.json', 'w') as jsonf:
    json.dump(threads, jsonf, ensure_ascii=False)

make_csv_line = lambda arr: ",".join(['"'+str(a).replace('"', '""')+'"' if ',' in str(a) else str(a) for a in arr])
headers = ["section", "thread", "controversiality", "min_date", "max_date", "nb_users", "nb_messages", "permalink"]
with open('threads_matched.csv', 'w') as csvf:
    print >> csvf, make_csv_line(headers)
    for t in threads:
        if not t['nb_users']*t['nb_messages']:
            continue
        data = ["", t['name'], t['max_depth'], t['date_min'], t['date_max'], t['nb_users'], t['nb_messages'], "http://en.wikipedia.org/wiki/..."]
        if len(t['article_sections']):
            for s in t['article_sections']:
                data[0] = s
                print >> csvf, make_csv_line(data)
        else:
            print >> csvf, make_csv_line(data)

