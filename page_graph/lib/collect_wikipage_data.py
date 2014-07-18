import os, re, time, json
import requests
from multiprocessing import Process, Manager, Pool
from helpers import chunkize

link_filters = ['File', 'User', 'Category', 'Help', 'Portal', 'Talk',
    'Wikipedia', 'Template', 'Special', 'Draft', 'Wikipedia',
    'Category', 'Book', 'User', 'Aide', 'Fichier']

regex_links = re.compile(r'href="/wiki/([^"]+)"')
regex_anchors = re.compile(r'#.+$')

def clean_page(page):
    page = regex_anchors.sub('', page)
    return page.replace("_", " ")

def filter_link(link):
    if link == u"Main_Page":
        return True
    for filter in link_filters:
        if link.startswith("%s:" % filter):
            return True
        if link.startswith("%s talk:" % filter):
            return True
    return False

def solve_redirects(pages, root_api_url, cache_redirs):
    tosolve = []
    for p in list(pages):
        if p not in cache_redirs:
            tosolve.append(p)
        else:
            pages.remove(p)
            pages.append(cache_redirs[p])
    for chunk in chunkize(tosolve, 250):
        redir_api_args = {
            "redirects": 1,
            "titles": "|".join(chunk)
        }
        temp = requests.post(root_api_url, params=redir_api_args)
        data = json.loads(temp.text)
        if "normalized" in data["query"]:
            for redir in data["query"]["normalized"]:
                pages.remove(redir["from"])
                pages.append(redir["to"])
                cache_redirs[redir["from"]] = redir["to"]

def get_outlinks(page, language, root_api_url, cache_redirs):
    out_links = []
    url = "https://%s.wikipedia.org/wiki/%s" % (language, page)
    htmlcontent = requests.get(url).text
    for link in regex_links.findall(htmlcontent):
        link = clean_page(link)
        if filter_link(link) or link in out_links:
            continue
        out_links.append(link)
    solve_redirects(out_links, root_api_url, cache_redirs)
    return out_links

def get_inlinks(page, root_api_url):
    in_links = []
    api_url = "%s&list=backlinks&blredirect&blfilterredir=nonredirects&bllimit=500&bltitle=%s" % (root_api_url, page)
    cur_api_url = api_url
    while cur_api_url:
        data = json.loads(requests.get(cur_api_url).text)
        for link in data["query"]["backlinks"]:
            lk = link["title"]
            lk = clean_page(lk)
            if filter_link(lk):
                continue
            in_links.append(lk)
        if "query-continue" in data:
            cur_api_url = "%s&blcontinue=%s" % (api_url, data["query-continue"]["backlinks"]["blcontinue"])
        else:
            cur_api_url = ""
    return in_links

def get_cache_file_path(page, language, pages_cache):
    return os.path.join(pages_cache, "%s-%s.json" % (language, page))

def get_page_in_cache(page, language, pages_cache):
    page_file = get_cache_file_path(page, language, pages_cache)
    lastweek = time.time() - 7*24*60*60
    if os.path.exists(page_file) and os.path.getmtime(page_file) > lastweek:
        return page_file
    return None

def collect_page_data(page, language, pages_cache, root_api_url, cache_redirs):
    page_file = get_cache_file_path(page, language, pages_cache)
    if get_page_in_cache(page, language, pages_cache):
        with open(page_file) as f:
            data = json.load(f)
        out_links = data["out"]
        in_links = data["in"]
    else:
        out_links = get_outlinks(page, language, root_api_url, cache_redirs)
        in_links = get_inlinks(page, root_api_url)
        with open(page_file, 'w') as f:
            print "SAVING", page_file
            json.dump({"in": in_links, "out": out_links}, f)
    return (out_links, in_links)


