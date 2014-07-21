# Contropedia Exploration API
runs with pyhton 2.7 (never tested with other versions)

## Installation

```bash
# Clone the repo
git clone git@github.com:boogheta/contropedia-sprint-scripts.git

# Go in appropriate folder
cd contropedia-sprint-scripts/page_graph

# Install dependencies (preferably in a python virtualenv, use sudo otherwise)
pip install -r requirements

# Copy the controversiality sqlite database from David's CSV in the page_graph folder

# download or copy within the page_graph directory the csv with metrics on all articles from David named "all_articles_pages.csv"
# then run the script which loads it and indexes it in a sqlite3 db for fast queries (since the CSV is 800Mo)
./bin/make_controversialities_db.sh
```

## Usage

To launch the server, just run `python app.py`.

Then go to `localhost:5000` to access the application.
