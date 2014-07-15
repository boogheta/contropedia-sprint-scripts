from flask import Flask
from flask import render_template

# Creating the application
app = Flask(__name__)

# Routes
@app.route('/')
def index():
    return render_template('index.html')


# Running server
if __name__ == '__main__':
    app.debug = True
    app.run()
