from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from mock import SAMPLE_GRAPH, SUPPLEMENTARY_GRAPH

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
    return jsonify(**{'graph': SAMPLE_GRAPH if not token else SUPPLEMENTARY_GRAPH, 'token': 'tada'})


# Running server
if __name__ == '__main__':
    app.debug = True
    app.run()
