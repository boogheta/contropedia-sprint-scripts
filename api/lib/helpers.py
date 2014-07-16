def parse_wikipedia_url(url):
    assert('wikipedia.org/wiki/' in url)
    lang = url.split('//')[-1].split('.')[0]
    title = url.split('/')[-1]
    return lang, title

def add_network_node(network, node, extrafields=[]):
    if node not in network.nodes():
        network.add_node(node)
        for field, values in extrafields:
            if node in values:
                network.node[node][field] = values[node]

def add_network_edge(network, nodefrom, nodeto):
    if not network.has_edge(nodefrom, nodeto):
        network.add_edge(nodefrom, nodeto)
