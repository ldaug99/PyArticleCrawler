# Imports
from .newspaper import Newspaper as Newspaper
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# !!! This class should be customized to the specific newspaper
# An example newspaper class definition
class Examplenewspaper(Newspaper):
    NEWSPAPER_NAME = 'B.T.' # Newspaper name to apper in output file # CHANGE ME!
    NEWSPAPER_URL = 'https://www.bt.dk' # Newspaper URL # CHANGE ME!
    EXCLUDE_SUBPATHS = [ # Paths of newspaper to avoid when crawling
        '/rabatkode/',
        '/content/',
        '/cookiedeklaration'
    ] # CHANGE ME!

    # Class constructor, leave unchanged
    def __init__(self, articleUrl):
        # Call the super constructor
        super(type(self), self).__init__(
            self.NEWSPAPER_NAME,
            self.NEWSPAPER_URL,
            self.EXCLUDE_SUBPATHS,
            articleUrl
        )

    """Returns the title of the article.

    This function should return the title of the web article as plain text.
    """
    def getTitle(self):
        # Get the title from the title class, strip it of newlines and return the title
        return self._articleSoup.find(class_ = 'article-title').text.strip()

    """Returns the content of the article.

    This function should return the content of the web article as plain text.
    """
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

    """Returns the metadata of the article.

    This function should return article metadata, such as catagory, or None if no metadata is desired.
    """
    def getMetaInfo(self):
        return None

    """Returns a list of related article links.

    This function should return a list of article links related to the current article.
    """
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
