# Imports
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod

# Newspaper class definition
class Newspaper(ABC):
    
    class URLDoesNotMatchNewspaper(Exception):
        pass

    def __init__(self, newspaperName, newspaperUrl, exclude_subpaths, articleUrl):
        # Store the variables
        self._newspaperName = newspaperName
        self._newspaperUrl = newspaperUrl
        self._exclude_subpaths = exclude_subpaths
        self._articleUrl = articleUrl
        # Validate that the URL is from the respective newspaper
        if self.getNetloc() not in self._articleUrl:
            raise Newspaper.URLDoesNotMatchNewspaper()
        # Parse the HTML soup
        self._articleSoup = Newspaper._getPageSoup(self._articleUrl)

    def getNewspaperName(self):
        return self._newspaperName

    def getNewspaperUrl(self):
        return self._newspaperUrl

    def getArticleUrl(self):
        return self._articleUrl

    @abstractmethod
    def getTitle(self):
        pass

    @abstractmethod
    def getContent(self):
        pass

    @abstractmethod
    def getMetaInfo(self):
        pass

    @abstractmethod
    def getLinkedArticles(self):
        pass

    def getArticleEntry(self):
        # Get the article title and content
        title = self.getTitle()
        content = self.getContent()
        # Return the articleEntry or null if the title or content is None
        if title and content:
            return {
                'newspaper': self.getNewspaperName(),
                'url': self.getArticleUrl(),
                'metainfo': self.getMetaInfo(),
                'title': title,
                'content': content
            }
        else:
            return None

    @staticmethod
    @abstractmethod
    def getNetloc():
        pass

    @staticmethod
    def _getArticleSubPath(articlePath):
        try:
            # Get the index of the last / to isolate catagory
            subPathIndex = articlePath.index('/',1)
            # Return the catagory
            return articlePath[0:subPathIndex + 1]
        except ValueError:
            # Slash not found
            return None

    @staticmethod
    def _getPageSoup(articleUrl):
        # Download the webpage
        req = requests.get(articleUrl)
        # Get the HTML
        html = req.content
        # Parse the HTML soup
        return BeautifulSoup(html, 'html.parser')

    @classmethod
    def getNetloc(_class):
        # Parse self url
        return urlparse(_class.NEWSPAPER_URL).netloc
