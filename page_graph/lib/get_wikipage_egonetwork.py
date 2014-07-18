#!/usr/bin/env python

import uuid, json, os
import networkx
from networkx.readwrite import json_graph
from helpers import add_network_node, add_network_edge, format_edges, query_controversiality_db
from collect_wikipage_data import clean_page, collect_page_data, get_page_in_cache

# TODO
# - filter network:
#  * currently only nodes implied in reciprocal links are returned
#  * change to filter on out_degree instead ?
#  * add filter on controversiality ?

class WikipageNetwork(object):

    pages_cache = os.path.join("cache", "pages")

    def __init__(self, token=None, title="Global_warming", language="en", cache_redirs={}):
        if not os.path.isdir("cache"):
            os.makedirs("cache")
        if not os.path.isdir(self.pages_cache):
            os.makedirs(self.pages_cache)
        self.cache_redirs = cache_redirs
        self.index_pages = {}
        self.contro_pages = {}
        self.done_pages = []
        self.max_contro = 0
        self.curid = 0
        if token:
            self.token = token
            self.reload_network()
        else:
            self.token = uuid.uuid1()
            self.init_network(clean_page(title), language)

    def add_page(self, page, pool):
        page = clean_page(page)
        self.add_node(page)
        if page not in self.done_pages:
            out_links, in_links = collect_page_data(page, self.language, self.pages_cache, self.root_api_url, self.cache_redirs)
            for lk in out_links:
                self.add_edge(page, lk)
            for lk in in_links:
                self.add_edge(lk, page)
            self.done_pages.append(page)
            self.save()
        filtered_net = self.return_filtered_network()
        nodes = [p['label'] for p in filtered_net['nodes']]
        change = False
        for p in nodes:
            page_file = get_page_in_cache(p, self.language, self.pages_cache)
            if page_file:
                with open(page_file) as f:
                    out_links = json.load(f)["out"]
                for lk in out_links:
                    change = True
                    self.add_edge(p, lk)
            else:
                pool.apply_async(collect_page_data, [p, self.language, self.pages_cache, self.root_api_url, self.cache_redirs])
       # if change:
       #     filtered_net = self.return_filtered_network()
        return {
            'token': self.token,
            'max_contro': self.max_contro,
            'graph': filtered_net
        }

    def init_network(self, title, language):
        self.title = title
        self.language = language
        self.root_api_url = "https://%s.wikipedia.org/w/api.php?action=query&format=json" % language
        self.network = networkx.DiGraph()
        self.add_node(title)
        self.networkfile = os.path.join("cache", "%s.json" % self.token)

    def get_jsonfile(self):
        return os.path.join("cache", "%s-metas.json" % self.token)

    def reload_network(self):
        with open(self.get_jsonfile()) as f:
            data = json.load(f)
        self.init_network(data["title"], data["language"])
        self.curid = data["lastid"] + 1
        self.done_pages = data["pages"]
        self.index_pages = data["index"]
        self.contro_pages = data["contro"]
        self.max_contro = data["max_contro"]
        with open(self.networkfile) as f:
            self.network = json_graph.node_link_graph(json.load(f), True)

    def save(self):
        with open(self.get_jsonfile(), "w") as f:
            json.dump({
                "title": self.title,
                "language": self.language,
                "lastid": self.curid,
                "pages": self.done_pages,
                "index": self.index_pages,
                "max_contro": self.max_contro,
                "contro": self.contro_pages
            }, f)
        with open(self.networkfile, "w") as f:
            json.dump(json_graph.node_link_data(self.network), f)

    def add_node(self, page):
        extrafields = [('label', self.index_pages), ('controversiality', self.contro_pages)]
        if page not in self.index_pages:
            contro = query_controversiality_db(self.language, page)
            self.max_contro = max(contro, self.max_contro)
            self.contro_pages[page] = contro
            add_network_node(self.network, self.curid, {"label": page, "controversiality": self.contro_pages[page]})
            self.index_pages[page] = self.curid
            self.curid += 1
            return self.curid - 1
        return self.index_pages[page]

    def add_edge(self, frompage, topage):
        idf = self.add_node(frompage)
        idt = self.add_node(topage)
        add_network_edge(self.network, idf, idt)

    def return_filtered_network(self):
        filtered_net = networkx.Graph()
        add_network_node(filtered_net, 0, {'label': self.title, 'co': self.contro_pages[self.title]})
        for nfrom, nto in self.network.edges_iter():
            if self.network.has_edge(nto, nfrom):
                node = self.network.node[nto]
                add_network_node(filtered_net, nto, {"label": node['label'], "co": node['controversiality']})
                node = self.network.node[nfrom]
                add_network_node(filtered_net, nfrom, {"label": node['label'], "co": node['controversiality']})
                add_network_edge(filtered_net, nfrom, nto)
        result = json_graph.node_link_data(filtered_net)
        return {"nodes": result["nodes"], "edges": format_edges(filtered_net)}


if __name__ ==  '__main__':
    net = WikipageNetwork(None, "Global_warming", "en")
    filtered_net = net.add_page("Global_warming")
    cache_redirs = net.cache_redirs
    token = net.token
    net2 = WikipageNetwork(token, cache_redirs=cache_redirs)
    new_filtered_netw = net2.add_page("Climate_change")
