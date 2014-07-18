from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from lib.helpers import parse_wikipedia_url
from lib.get_wikipage_egonetwork import WikipageNetwork

cache_wikipedia_redirs = {}

# Creating the application
app = Flask(__name__)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/graph', methods=['POST'])
def graph():
    url = request.form['url']
    token = request.form.get('token', None)
    try:
        if not token or 'wikipedia' in url:
            lang, title = parse_wikipedia_url(url)
        else:
            title = url
    except:
        return jsonify(**{'error': "Unable to parse input wikipedia"})
    if token:
        net = WikipageNetwork(token=token, cache_redirs=cache_wikipedia_redirs)
    else:
        net = WikipageNetwork(title=title, language=lang, cache_redirs=cache_wikipedia_redirs)
    try:
        result = net.add_page(title)
    except Exception as e:
        result = {'error': "Unable to process this page's network", 'details': '%s: %s' % (type(e), e)}
    return jsonify(**result)

# Running server
if __name__ == '__main__':
    app.debug = True
    app.run()
