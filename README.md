# Web Article Crawler
A Python Web Article Crawler that grabs the title and text of web articles and places these in a json file.

## Features
- [x] Basic web crawler
- [x] Newspaper: B.T.

## Setup
To install all the required pacakges, run the ```install.py``` script. Most often the script would be run inside a virtual Python enviroment. In such a case, do the following (on Linux):

```
git clone https://github.com/ldaug99/PyArticleCrawler.git
cd PyArticleCrawler
python3 -m venv .
source bin/activate
python3 install.py
```

Then run the script using:

```
python3 main.py
```

## Crawler
The simple web crawler will download the front page of the newspaper, and grab alle article links present on the front page. These article links, will then be added to a queue. After a settable delay the crawler will then grab the next article link form the queue; download the article; grab the article title and content; save theise to a json file; grab related articles; append these to the queue; and then repeat until the queue is exhausted. 

If the program is stopped (shutdown safely by using ```Ctrl+C```) at any point during the article crawling, the queue and progress is saved to a local file. If the program is then started again, it will resume from the last queue. The queue is stored in a file name ```.queue```.

## Newspapers
The crawler handles the article according to the newspaper the article belongs too. The newspaper is recognised based on the newspaper URL. This is performed using an abstract ```Newspaper``` class as well as a specific newspaper class for each of the recognized newspapers. To create a specific newspaper class simply copy the ```examplenewspaper.py``` file and change the ```getTitle```, ```getContent``` and ```getLinkedArticles``` methods to fit the specific newsarticles. Once the specific newspaper class has been created, simply import it in the ```main.py``` and add the imported name to the ```NEWSPAPERS``` variabel in the top of the ```Crawler``` class.

## The output file
All crawled articles's title and content will be written to a JSON array inside the specified file. Per default this fille will be named ```articles.json```. 

To read using this file using Python simply use the following code:

```
# Imports
import json

articles = None

with open('articles.json', "r") as outfile:
    # Load the current data from the file
    articles = json.load(outfile)

# Print the articles
print(json.dumps(articles, indent=3))

```
