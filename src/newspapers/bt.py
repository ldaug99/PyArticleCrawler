# Imports
from .newspaper import Newspaper as Newspaper
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# BT class definition
class BT(Newspaper):
    NEWSPAPER_NAME = 'B.T.'
    NEWSPAPER_URL = 'https://www.bt.dk'
    EXCLUDE_SUBPATHS = [
        '/rabatkode/',
        '/content/',
        '/cookiedeklaration'
    ]

    def __init__(self, articleUrl):
        # Call the super constructor
        super(BT, self).__init__(
            BT.NEWSPAPER_NAME,
            BT.NEWSPAPER_URL,
            BT.EXCLUDE_SUBPATHS,
            articleUrl
        )

    def getTitle(self):
        # Get the title from the title class, strip it of newlines and return the title
        return self._articleSoup.find(class_ = 'article-title').text.strip()

    def getContent(self):
        # Get the article content
        contentArray = self._articleSoup.find(class_='article-content').find_all('p')
        # Create a temporaty variable for the article content
        articleContent = ""
        # Loop through each article element
        for content in contentArray:
            # Skip the entry if it contains the phrase 'Foto: '
            try:
                content.text.index('Foto: ')
                continue
            except: pass
            try:
                content.text.index('Vis mere')
                continue
            except: pass
            # Get the text of the HTML tage, and append it to the article content. Add a space
            articleContent += content.text.strip() + " "
        # Return the article content
        return articleContent

    def getMetaInfo(self):
        return {
            'catagory': self._getCatagory()
        }

    def _getCatagory(self):
        # Parse the link
        parsedUrl = urlparse(self._articleUrl)
        # All BT articles belong to a catagory. The catagory is shown in the link with '/samfund/some-very-clickbate-article'
        try:
            # Get the index of the last / to isolate catagory
            catagoryLastSlash = parsedUrl.path.index('/',1)
            # Return the catagory
            return parsedUrl.path[1:catagoryLastSlash]
        except ValueError:
            # Slash not found
            return None

    def getLinkedArticles(self):
        # Create a temp var to store links
        linkedArticles = []
        # Find all link tags
        for link in self._articleSoup.find_all('a'):
            # Store the article article url
            articleUrl = link.get('href')
            # Parse the link
            parsedUrl = urlparse(articleUrl)
            # Remove all links outside BT
            if parsedUrl.netloc == self.getNetloc():
                # Get the subpath, the part of the link: '/somesubpath/somearticle'
                subpath = self._getArticleSubPath(parsedUrl.path)
                # Remove all links that are in the excluded subpaths
                if not (subpath in self._exclude_subpaths or subpath == None):
                    # Validate that the article is not already in relatedLinks
                    if articleUrl not in linkedArticles:
                        # Append the article link
                        linkedArticles.append(articleUrl)
                    else:
                        # Continue
                        continue
                else:
                    continue
        # Return the related articles
        return linkedArticles

    @staticmethod
    def getNetloc():
        # Parse self url
        return urlparse(BT.NEWSPAPER_URL).netloc
