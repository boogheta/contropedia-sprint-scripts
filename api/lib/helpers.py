def parse_wikipedia_url(url):
    lang = url.split('//')[-1].split('.')[0]
    title = url.split('/')[-1]
    return lang, title
