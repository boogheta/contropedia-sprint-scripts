#!/usr/bin/env python

import uuid, re, json, os
import requests
import networkx
from networkx.readwrite import json_graph
from helpers import add_network_node, add_network_edge

# TODO
# cache results of one page with timestamp
# add read controversiality in sqlite)
# filter network:
#  - currently only nodes implied in reciprocal links are returned
#  - change to filter on out_degree instead ?
#  - add filter on controversiality ?

chunkize = lambda a, n: [a[i:i+n] for i in xrange(0, len(a), n)]

class WikipageNetwork(object):

    regex_links = re.compile(r'href="/wiki/([^"]+)"')
    regex_anchors = re.compile(r'#.+$')
    link_filters = ['File', 'User', 'Category', 'Help', 'Portal', 'Talk',
        'Wikipedia', 'Template', 'Special', 'Draft', 'wikipedia',
        'Category', 'Book', 'User']

    def __init__(self, token=None, title="Global_warming", language="en", cache_redirs={}):
        if not os.path.isdir("cache"):
            os.makedirs("cache")
        self.curid = 0
        self.cache_redirs = cache_redirs
        self.index_pages = {}
        self.contro_pages = {}
        self.done_pages = []
        if token:
            self.token = token
            self.reload_network()
        else:
            self.token = uuid.uuid1()
            self.init_network(self.clean_page(title), language)

    def add_page(self, page):
        page = self.clean_page(page)
        self.add_node(page)
        self.get_outlinks(page)
        self.get_inlinks(page)
        self.done_pages.append(page)
        self.save()
        return {
            'token': self.token,
            'graph': self.return_filtered_network()
        }

    def clean_page(self, page):
        page = self.regex_anchors.sub('', page)
        return page.replace("_", " ")

    def init_network(self, title, language):
        self.title = title
        self.language = language
        self.root_api_url = "https://%s.wikipedia.org/w/api.php?action=query&format=json" % language
        self.network = networkx.DiGraph()
        self.add_node(title)
        self.networkfile = os.path.join("cache", "%s.json" % self.token)

    def get_jsonfile(self):
        return os.path.join("cache", "%s-metas.json" % self.token)

    def reload_network(self, ):
        with open(self.get_jsonfile()) as f:
            data = json.load(f)
        self.init_network(data["title"], data["language"])
        self.done_pages = data["pages"]
        self.index_pages = data["index"]
        self.contro_pages = data["index"]
        with open(self.networkfile) as f:
            self.network = json_graph.node_link_graph(json.load(f), True)

    def save(self):
        with open(self.get_jsonfile(), "w") as f:
            json.dump({
                "title": self.title,
                "language": self.language,
                "pages": self.done_pages,
                "index": self.index_pages,
                "contro": self.contro_pages
            }, f)
        with open(self.networkfile, "w") as f:
            json.dump(json_graph.node_link_data(self.network), f)

    def add_node(self, page):
        extrafields = [('label', self.index_pages), ('controversiality', self.contro_pages)]
        if page not in self.index_pages:
            contro = 0
            #contro = sqlite.get value
            self.contro_pages[page] = contro
            add_network_node(self.network, self.curid, extrafields)
            self.index_pages[page] = self.curid
            self.curid += 1
            return self.curid
        return self.index_pages[page]

    def add_edge(self, frompage, topage):
        idf = self.add_node(frompage)
        idt = self.add_node(topage)
        add_network_edge(self.network, idf, idt)

    def return_filtered_network(self):
        extrafields = [('label', self.index_pages), ('co', self.contro_pages)]
        filtered_net = networkx.Graph()
        for nfrom, nto in self.network.edges_iter():
            if self.network.has_edge(nto, nfrom):
                add_network_node(filtered_net, nto, extrafields)
                add_network_node(filtered_net, nfrom, extrafields)
                add_network_edge(filtered_net, nfrom, nto)
        result = json_graph.node_link_data(filtered_net)
        return {"nodes": result["nodes"], "edges": result["links"]}

    def filter_link(self, link):
        if link == u"Main_Page":
            return True
        for filter in self.link_filters:
            if link.startswith("%s:" % filter):
                return True
            if link.startswith("%s talk:" % filter):
                return True
        return False

    def solve_redirects(self, pages):
        tosolve = []
        for p in list(pages):
            if p not in self.cache_redirs:
                tosolve.append(p)
            else:
                pages.remove(p)
                pages.append(self.cache_redirs[p])
        for chunk in chunkize(tosolve, 300):
            redir_api_args = {
                "redirects": 1,
                "titles": "|".join(chunk)
            }
            temp = requests.post(self.root_api_url, params=redir_api_args)
            data = json.loads(temp.text)
            if "normalized" in data["query"]:
                print pages
                for redir in data["query"]["normalized"]:
                    print redir
                    pages.remove(redir["from"])
                    pages.append(redir["to"])
                    self.cache_redirs[redir["from"]] = redir["to"]

    def get_outlinks(self, page):
        out_links = []
        if page in self.done_pages:
            return
        url = "https://%s.wikipedia.org/wiki/%s" % (self.language, page)
        htmlcontent = requests.get(url).text
        for link in self.regex_links.findall(htmlcontent):
            link = self.clean_page(link)
            if self.filter_link(link) or link in out_links:
                continue
            out_links.append(link)
        self.solve_redirects(out_links)
        for link in out_links:
            self.add_edge(page, link)

    def get_inlinks(self, page):
        if page in self.done_pages:
            return
        api_url = "%s&list=backlinks&blredirect&blfilterredir=nonredirects&bllimit=500&bltitle=%s" % (self.root_api_url, page)
        cur_api_url = api_url
        while cur_api_url:
            data = json.loads(requests.get(cur_api_url).text)
            for link in data["query"]["backlinks"]:
                lk = link["title"]
                lk = self.clean_page(lk)
                if self.filter_link(lk):
                    continue
                self.add_edge(lk, page)
            if "query-continue" in data:
                cur_api_url = "%s&blcontinue=%s" % (api_url, data["query-continue"]["backlinks"]["blcontinue"])
            else:
                cur_api_url = ""

if __name__ ==  '__main__':
    net = WikipageNetwork(None, "Global_warming", "en")
    filtered_net = net.add_page("Global_warming")
    cache_redirs = net.cache_redirs
    token = net.token
    net2 = WikipageNetwork(token, cache_redirs=cache_redirs)
    new_filtered_netw = net2.add_page("Climate_change")
