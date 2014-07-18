#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, re
import csv, json
import urllib, htmlentitydefs
from time import mktime, strptime
from datetime import date, datetime
from locale import setlocale, LC_ALL
setlocale(LC_ALL, 'en_GB.utf8')

# Open required data that was generated via the the generate_article_threads_data.sh
try:
    page_title = sys.argv[1]
    datadir = "data/%s" % page_title
    os.chdir(datadir)
    with open('discussions.tsv') as csvf:
        discussions = list(csv.DictReader(csvf, delimiter="\t"))
    with open('revisions.tsv') as csvf:
        revisions = list(csv.DictReader(csvf, delimiter="\t"))
    with open('sections.tsv') as csvf:
        section_titles = csvf.read().split('\n')
    with open('threads_links.tsv') as csvf:
        links = list(csv.DictReader(csvf, delimiter="\t"))
    with open('threads_metrics.tsv') as csvf:
        metrics = list(csv.DictReader(csvf, delimiter="\t"))
    with open('revisions_sections.tsv') as csvf:
        rev_sec = csvf.read().split('\n')
        rev_sec.pop(0)
    with open('actors.tsv') as csvf:
        actors = csvf.read().split('\n')
        actors.pop(0)
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

# Bunch of small functions and regexp to treat and cleanup dates and text
parse_ts = lambda t: date.isoformat(datetime.fromtimestamp(t))
parse_date = lambda d: parse_ts(mktime(strptime(d.split(', ')[1].replace("(UTC)", "").strip(), "%d %B %Y")))
SPACES = ur'[  \s\t\u0020\u00A0\u1680\u180E\u2000-\u200F\u2028-\u202F\u205F\u2060\u3000]'
re_clean_blanks = re.compile(r'%s+' % SPACES)
clean_blanks = lambda x: re_clean_blanks.sub(r' ', x.strip()).strip()
re_entities = re.compile(r'&([^;]+);')
unescape_html = lambda t: clean_blanks(re_entities.sub(lambda x: unichr(int(x.group(1)[1:])) if x.group(1).startswith('#') else unichr(htmlentitydefs.name2codepoint[x.group(1)]), safe_utf8_decode(t)).encode('utf-8'))
re_talk = re.compile(r'\[\[Talk:.*#([^\|]+)\|?.*\]\]')
re_abstract = re.compile(r'(^|\W)(intro(duction)?|abstract|lead|summar(y|ies)|preamble|headers?)(\W|$)', re.I)
clean_thread_name = lambda t: unescape_html(t).replace('_', ' ').strip('"[]()«»!?~<>.= ').strip("'")
re_clean_lf = re.compile(r'\s*<LF>\s*', re.I)
re_clean_text = re.compile(r'[^\w\d]+')
re_clean_spec_chars = re.compile(r'[^\w\d\s]')
clean_text = lambda t: re_clean_text.sub(' ', re_clean_lf.sub('', unescape_html(t))).lower().strip()
re_text_splitter = re.compile(r"[^\w\d']+")
is_null_col = lambda x: not x or x in ["", "0", "-1"]

# Prepare threads data from all discussions lines
thread = None
threads = []
curthread = ""
threadidx = {}
# Read data from David's discussions file line by line
for row in discussions:
    # Skip lines without a thread title
    if not row['thread_title']:
        continue
    # Store in threads array previous thread object and create a new one whenever reaching a line with a different thread title
    idx = len(threads)
    th = clean_thread_name(row['thread_title'])
    if th != curthread:
        curthread = th
        if thread:
            threads.append(thread)
        thread = {"index": idx,
                  "name": th,
                  "rawname": row['thread_title'].strip('=[] '),
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
                  "timestamped_text": [],
                  "permalink": "",
                  "revisions": [],
                  "article_sections": [],
                  "match": 0}
        threadidx[th.lower()] = idx
    if is_null_col(row["timestamp"]):
        curthread = th
        continue
    # Collect and compute useful metas on the threads
    dt = parse_ts(int(row['timestamp'])*60)
    if not thread['date_min']:
        thread['date_min'] = dt
    else:
        thread['date_min'] = min(thread['date_min'], dt)
    if not thread['date_max']:
        thread['date_max'] = dt
    else:
        thread['date_max'] = max(thread['date_max'], dt)
    us = row["author_name"].strip()
    if us not in thread["users"]:
        thread['users'].append(us)
        thread['nb_users'] += 1
    thread['nb_messages'] += 1
    thread['messages'].append(row)
    # Save a field containing the concatenated cleaned up text from all comments
    thread['fulltext'] += " " + clean_text(row["text"])
    # And one as an array of tuples (text, timestamp) for each comment for use in the actors matching part
    thread['timestamped_text'].append((clean_text(row["text"]), row['timestamp']))
# Save last current thread since we won't find a new one after it
if thread:
    threads.append(thread)

# Complete threads with their permalinks
for row in links:
    t = clean_thread_name(row['thread_title']).lower()
    if t in threadidx:
        threads[threadidx[t]]['permalink'] = "http://en.wikipedia.org/wiki/%s#%s" % (row['talk_page'], urllib.quote(threads[threadidx[t]]['rawname'].replace(' ', '_')).replace('%', '.'))
    else:
        sys.stderr.write("ERROR: could not match one thread from links: %s\n" % t)

# Complete threads with David's precomputed metrics
for row in metrics:
    t = clean_thread_name(row['thread_title']).lower()
    if t in threadidx:
        for f in ["users_hindex", "max_depth", "tree_hindex", "chains_num", "chains_comments"]:
            threads[threadidx[t]][f] = int(row[f])
    else:
        sys.stderr.write("ERROR: could not match one thread from metrics: %s\n" % t)

revisions_sec = {}
# Look for revisions referencing a thread as comment
for row in rev_sec:
    if not row:
        continue
    rev_id, sec_title = row.split('\t')
    rev_id = int(rev_id)
    if not rev_id in revisions_sec:
        revisions_sec[rev_id] = []
    revisions_sec[rev_id].append(sec_title)

#Loop through all revisions and search for a blurry version of the thread title within the revision comment
for row in revisions:
    src = re_talk.search(row["rev_comment"])
    if src:
        t = clean_thread_name(src.group(1)).lower()
        if t in threadidx:
            rev_id = int(row['rev_id'])
            print "MATCH FOUND:", row["rev_id"], t
            threads[threadidx[t]]['revisions'].append(rev_id)
            try:
                threads[threadidx[t]]['article_sections'] += revisions_sec[rev_id]
            except:
                sys.stderr.write('WARNING: revision %s could not be found in the correspondance list of revisions/sections\n' % rev_id)
            threads[threadidx[t]]['match'] += 1


# Look for article sections within thread names and fulltext of all comments
sections = {}
allsections = ""
# First generate a blurry cleaned list of the article's section titles
for section in section_titles:
    s = clean_thread_name(section).lower()
    if s not in sections:
        sections[s] = section
    allsections += " | " + s
    # Try to match the sections titles within the fulltext of each thread's comment, might be imperfect
    # so doing it onlty for long thread names since too short ones will most probably match many false positives
    if len(s) > 5:
        for t in threads:
            try:
                re_match_s = re.compile(r"%s" % re_clean_spec_chars.sub(".?", s))
            except:
                print "ERROR compiling regexp %s %s" % (s, re_clean_spec_chars.sub(".?", s))
                continue
            # Only validate when the word was found in at least half of the thread's comments
            if 2*len(re_match_s.findall(t['fulltext'])) > t['nb_messages']:
                print "MATCH maybe FOUND:", t['name'], "/", section
                t['article_sections'].append(section)
                t['match'] += 1
# Then try to find sections titles within the thread's title
for thread in threadidx:
    # If a thread's title matches a section one, this is definitely a match
    if thread in sections:
        print "MATCH FOUND:", thread, "/", sections[thread]
        threads[threadidx[thread]]['article_sections'].append(sections[thread])
        threads[threadidx[thread]]['match'] += 1
    # Otherwise try some heuristic when finding the section within a thread's title
    # Only take it when the section's name is longer than 3 chars to avoid false positives,
    # And only take it when the section has at least 2 words or a tenth of the number of words in the thread's title
    else:
        for section in sections:
            n_words = len(re_text_splitter.split(section))
            if section in thread and 3 < len(section) and (n_words > 1 or 10 * n_words > len(re_text_splitter.split(thread))):
                print "MATCH probably FOUND:", thread, "/", sections[section]
                for test in threads[threadidx[thread]]['article_sections']:
                    tmps = clean_thread_name(section).lower()
                    # If we find a bigger match than a previous one, we favor this one
                    if test in tmps and test != tmps:
                        print " -> probably better than match with « %s », removing it" % test
                        threads[threadidx[thread]]['article_sections'].remove(test)
                        threads[threadidx[thread]]['match'] -= 1
                threads[threadidx[thread]]['article_sections'].append(sections[section])
                threads[threadidx[thread]]['match'] += 1
    # Quite often threads correspond to the header of a wikipage following a bunch of possible names for it (abstract, summary, etc...)
    # Try to match those
    if re_abstract.search(thread):
        print "MATCH probably GUESSED:", thread, "/", "abstract"
        threads[threadidx[thread]]['article_sections'].append("asbtract")
        threads[threadidx[thread]]['match'] += 1


# IDEAS FOR MATCH IMPROVEMENTS:
# - use userids and timestamps of comments to countermatch with same user's revisions around the same period of time

matches = sum([1 for t in threads if t['match'] > 0])
print "=================="
print "FOUND %d matches out of %d threads (%s)" % (matches, len(threadidx), str(matches*100/len(threadidx))+"%")
print "=================="
for t in threads:
    if not 'max_depth' in t:
        th = clean_thread_name(t['name']).lower()
        print "WARNING Can't find max_depth in %s" % th
    if False and not t['match']:
        print "MISSING:", t['name'], t['nb_messages'], t['nb_users']

#Save the threads data for debug purposes
with open('threads.json', 'w') as jsonf:
    json.dump(threads, jsonf, ensure_ascii=False)

# Save the built data on each article/thread match as a csv
make_csv_line = lambda arr: ",".join(['"'+str(a).replace('"', '""')+'"' if ',' in str(a) else str(a) for a in arr])
headers = ["article_title", "section", "thread", "controversiality", "min_date", "max_date", "nb_users", "nb_messages", "users_hindex", "max_depth", "tree_hindex", "chains_num", "chains_comments", "permalink"]
with open('threads_matched.csv', 'w') as csvf:
    print >> csvf, make_csv_line(headers)
    for t in threads:
        if not t['nb_users']*t['nb_messages']:
            continue
        data = [page_title, "", t['rawname'], "TBD", t['date_min'], t['date_max'], t['nb_users'], t['nb_messages'], t["users_hindex"], t["max_depth"], t["tree_hindex"], t["chains_num"], t["chains_comments"], t['permalink']]
        if len(t['article_sections']):
            for s in t['article_sections']:
                data[1] = s
                print >> csvf, make_csv_line(data)
        else:
            print >> csvf, make_csv_line(data)

# Identify page's actors within threads
make_csv_line = lambda arr: "\t".join([str(a) for a in arr])
headers = ["article_title", "actor", "thread", "thread_permalink", "actor_in_thread_title", "n_matches_in_thread", "comments_timestamps"]
with open('actors_matched.csv', 'w') as csvf:
    print >> csvf, make_csv_line(headers)
    # Iterate on all of the page's actors as identified within Eric's database
    for actor in actors:
        # build a regexp to blurry match words similar to the actor by replacing with ".?" every non alphanumeric (or space) character
        act = clean_thread_name(actor).lower()
        re_actor = re.compile(r"%s" % re_clean_spec_chars.sub(".?", act))
        # SKIP empty actors and single-letter ones such as "d"
        if len(act) < 2: continue
        # Iterate on all threads to search the actor
        for thread in threads:
            # Search for the actor in the thread's title at first
            match_title = 1 if len(re_actor.findall(thread['name'].lower())) else 0
            # Search for the actor in each comment, sum the matches and list the corresponding timestamps
            all_matches = 0
            timestamps = []
            for te, ti in thread["timestamped_text"]:
                n_match = len(re_actor.findall(te.lower()))
                if n_match:
                    all_matches += n_match
                    timestamps.append(ti)
            # If there's at least one match, dump a tsv line
            if (match_title or all_matches) and thread['permalink']:
                print >> csvf, make_csv_line([page_title, actor, thread['rawname'], thread['permalink'], all_matches, match_title, timestamps])

