# esostat

Esolangs.org statistics explorer. Filter languages by any combination of categories.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install flask requests
```

## Usage

```bash
# Fetch data from esolangs.org MediaWiki API (one-time, takes a few minutes)
python fetch.py

# Start the web server
python server.py
# Open http://localhost:5757
```

## Features

- Searchable autocomplete picker for ALL categories (hundreds of them)
- Include/exclude any combination of categories
- Presets for common queries (Turing complete + not stack-based, no joke languages, etc.)
- Category breakdown showing what the matching languages are classified as
- Full language list for any query
