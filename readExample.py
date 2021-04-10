# Imports
import json

with open('articles.txt', "r") as outfile:
    # Load the current data from the file
    entries = json.load(outfile)
    # Add new data to the entry
    print(json.dumps(entries, indent=3))
