#!/usr/bin/env python

import uuid, requests, re, json, os
import networkx as nx
from networkx.readwrite import json_graph

# TODO
# add read controversiality in sqlite)

class WikipageNetwork(Object):

    regex_links = re.compile(r'href="/wiki/([^"]+)"')
    link_filters = ['File', 'User', 'Category', 'Help', 'Portal', 'Talk',
        'Wikipedia', 'Template', 'Template_talk', 'Special',
        'Category', 'Book']

    def __init__(self, title="Global_warming", language="en", token=None, cache_redirs={}):
        self.cache_redirs = cache_redirs
        if token:
            self.token = token
            self.reload_network()
        else:
            self.token = uuid.uuid1()
            self.init_network(title, language)
            self.add_page(title)

    def init_network(title, language):
        self.title = title
        self.language = language
        self.root_api_url = "https://%s.wikipedia.org/w/api.php?action=query&format=json" % language
        self.done_pages = [title]
        self.network = nx.DiGraph()
        self.add_node(title)
        self.networkfile = os.path.join("cache", "%s.json" % self.token)

    def get_jsonfile():
        return os.path.join("cache", "%s-metas.json" % self.token)

    def reload_network():
        with open(self.get_jsonfile()) as f:
            data = json.load(f)
        self.init_network(data["title"], data["language"])
        self.done_pages = data["nodes"].keys()
        with open(self.networkfile) as f:
            self.network = json.load(f)

    def save():
        with open(self.get_jsonfile()) as f:
            json.dump({
                "title": self.title,
                "language": self.language,
                "pages": self.done_pages
            })
        with open(self.networkfile) as f:
            json.dump(json_graph.node_link_data(self.network), f)

    def add_node(page):
        if page not in self.network:
            self.network.add_node(title, controversiality=0)

    def add_link(frompage, topage):
        pass

    def explore_node(title):
        get_outlinks(title)
        get_inlinks(title)

    def add_page(title):
        explore_node(title)
        self.save()
        return self.return_filtered_network()

    def return_filtered_network():
        pass

    def filter_link(link):
        for filter in self.link_filters:
            if link.startswith("%s:" % filter):
                return True
        return False

    def solve_redirects(pages):
        tosolve = []
        for p in list(pages):
            if p not in self.cache_redirs:
                tosolve.append(p)
            else:
                pages.remove(p)
                pages.append(self.cache_redirs[p])
        redir_api_url = "%s&redirects&titles=%s" % (root_api_url, "|".join(tosolve))
        data = json.loads(requests.post(redir_api_url).text)
        if "normalized" in data["query"]:
            for redir in data["query"]["normalized"]:
                pages.remove(redir["from"])
                pages.append(redir["to"])
                self.cache_redirs[redir["from"]] = redir["to"]

    def get_outlinks(page):
        out_links = []
        if page in self.done_pages:
            return
        url = "https://%s.wikipedia.org/wiki/%s" % (self.language, page)
        page = requests.get(url).text
        for link in self.regex_links.findall(page):
            if filter_link(link) or link in out_links:
                continue
            out_links.append(link)
        solve_redirects(out_links)
        return out_links

    def get_inlinks(page):
        if page in self.done_pages:
            return
        api_url = "%s&list=backlinks&blredirect&blfilterredir=nonredirects&bllimit=500&bltitle=%s" % (root_api_url, title)
        cur_api_url = api_url
        while cur_api_url:
            data = json.loads(requests.get(cur_api_url).text)
            for link in data["query"]["backlinks"]:
                lk = link["title"]
                if filter_link(lk) or lk in in_links:
                    continue
                in_links.append(lk)
            if "query-continue" in data:
                cur_api_url = "%s&blcontinue=%s" % (api_url, data["query-continue"]["backlinks"]["blcontinue"])
            else:
                cur_api_url = ""
        return in_links

if __name__ ==  __main__:
    net = WikipageNetwork()
    print len(net.in_links), len(net.out_links)
