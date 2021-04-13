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
        '/cookiedeklaration',
        '/mine-sider/',
        '/podcast',
        '/btvideo',
        '/tip',
        '/#',
        '/e-avis',
        '/api',
        '/reset_password',
        '/logout',
        '/login',
        '/faa-adgang',
        '/showMore',
        '/image_gallery/',
        '/tracking/image_gallery/',
        '/search'
    ]

    def __init__(self, articleUrl):
        # Call the super constructor
        super(type(self), self).__init__(
            self.NEWSPAPER_NAME,
            self.NEWSPAPER_URL,
            self.EXCLUDE_SUBPATHS,
            articleUrl
        )

    def getTitle(self):
        # Get the title from the title class, strip it of newlines and return the title
        articleTitle = self._articleSoup.find(class_ = 'article-title')
        # Validate that the article title was found, else the page is an index page
        if articleTitle:
            return articleTitle.text.strip()
        else:
            return None

    def getContent(self):
        # Get the article content
        articleContent = self._articleSoup.find(class_='article-content')
        # Validate that the article content was found, else the page is an index page
        if articleContent:
            # Get the article content
            contentArray = articleContent.find_all('p')
            # Create a temporaty variable for the article content
            articleContentText = ""
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
                articleContentText += content.text.strip() + " "
            # Return the article content
            return articleContentText
        else:
            return None

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
            # All links that start with a slash are local pages, add https://www.bt.dk to these
            try:
                # Try finding the leading slash
                articleUrl.index('/', 0, 1)
                # If the leading slash was found, append the newspaper url
                articleUrl = BT.NEWSPAPER_URL + articleUrl
            except:
                pass
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
