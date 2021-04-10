# Imports
import signal, time, os
import requests
import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from abc import ABC, abstractmethod

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
        if self.getNewspaperUrl() not in self._articleUrl:
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
        return {
            'newspaper': self.getNewspaperName(),
            'url': self.getArticleUrl(),
            'metainfo': self.getMetaInfo(),
            'title': self.getTitle(),
            'content': self.getContent()
        }

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

class Crawler:
    NEWSPAPERS = [
        BT
    ]

    CRAWL_DELAY = 2 # Delay in seconds between each page download

    QUEUE_STORE_FILE = '.queue'

    class URLStatus:
        PENDING = 0
        DOWNLOADED = 1
        UNSUPPORTED = 2
        UNAVALIABLE = 3
        INVALID = 4

    class UnsupportedNewspaper(Exception):
        pass

    class QueueIsEmpty(Exception):
        pass

    def __init__(self, outFileName = 'articles.txt', storeQueue = True):
        self._lastRun = 0
        self._doRun = False
        self._storeQueue = storeQueue
        # Try loading a saved queue if saveQueue is enabled
        if self._storeQueue:
            self._loadQueue()
        else:
            # Instantiate variable to store queue
            self._queue = []
        # Store the queue index of the current task
        self._queueIndex = 0
        # Save the output file name
        self._outFileName = outFileName

    def curlAllNewspapers(self):
        # For each of the newspages, get the front page and get all related articles
        for newspaper in Crawler.NEWSPAPERS:
            # Instantiate the newspaper to the front page
            np = newspaper(newspaper.NEWSPAPER_URL)
            # Get related articles
            for articleURL in np.getLinkedArticles():
                # Add the article
                self.addArticle(articleURL)

    def addArticle(self, articleURL):
        # Validate that the link is not already in the queue
        if not self._isLinkInQueue(articleURL):
            # Add the article
            self._queueLink(articleURL)
            # Return true to indicate success
            return True
        else:
            # Link already in queue, return false to indicate failure
            return False

    def run(self):
        # Set do run
        self._doRun = True
        # Start the task
        self._task()

    def stop(self):
        # Set do run
        self._doRun = False

    def finalize(self):
        # Stop running
        self.stop()
        # Save the queue if enabled
        if self._storeQueue:
            self._saveQueue()
        
    @staticmethod
    def _getNewspaperFromURL(url):
        # Parse the link
        parsedUrl = urlparse(url)
        # Look-up the netloc and compare to known newspapers
        for newspaper in Crawler.NEWSPAPERS:
            # If netlock matches newspaper URL, return the newspaper
            if parsedUrl.netloc == newspaper.getNetloc():
                return newspaper
        # If loop did not return a newspaper, newspaper is unsupported
        return Crawler._unsupportedNewspaper        

    def _loadQueue(self):
        try:
            with open(Crawler.QUEUE_STORE_FILE, "r") as queueFile:
                # Load queue
                self._queue = json.load(queueFile)
        except FileNotFoundError: # If the file exists, an exception is thrown
            self._queue = []

    def _saveQueue(self):
        try:
            # Try creating the file
            with open(Crawler.QUEUE_STORE_FILE, "x") as queueFile:
                # Dump the new data
                json.dump(self._queue, queueFile)
        except FileExistsError: # If the file exists, override the file
            with open(Crawler.QUEUE_STORE_FILE, "w") as queueFile:
                # Dump the new data
                json.dump(self._queue, queueFile)

    def _queueLink(self, url):
        # Add the url to the queue
        self._queue.append({
            'url': url,
            'status': Crawler.URLStatus.PENDING
        })

    def _updateQueueEntry(self, queueEntry, status):
        # Find the queue entry
        entryIndex = self._queue.index(queueEntry)
        # Update the status
        self._queue[entryIndex]['status'] = status

    def _getNextInQueue(self):
        # Make sure at least one entry was queue
        if len(self._queue) > 0 and self._queueIndex < len(self._queue):
            # Get the queue entry
            queueEntry = self._queue[self._queueIndex]
            # Increment the queueIndex
            self._queueIndex += 1
            # Check the status of the entry
            if queueEntry['status'] == Crawler.URLStatus.PENDING or queueEntry['status'] == Crawler.URLStatus.UNSUPPORTED:
                # Return the queueEntry
                return queueEntry
            else:
                # Run the function again
                return self._getNextInQueue()
        else:
            # Raise exception
            raise Crawler.QueueIsEmpty()

    def _task(self):
        while True:
            if self._doRun:
                try:
                    # Store run time
                    self._lastRun = time.time()
                    # Get the next link to download
                    queueEntry = self._getNextInQueue()
                    # Print output
                    self._printPreDownloadStatusToTerminal(queueEntry['url'])
                    downloaded = False
                    numRelatedArticles = 0
                    # Get the newspaper from the URL
                    newspaper = Crawler._getNewspaperFromURL(queueEntry['url'])
                    # Try getting the article from the newspaper
                    try:
                        newspage = newspaper(queueEntry['url'])
                        # Save the article
                        Crawler._saveEntryToOutput(self._outFileName, newspage.getArticleEntry())
                        # Queue related articles
                        numRelatedArticles = self._queueRelatedArticles(newspage.getLinkedArticles())
                        # Mark the entry as downloaded in the queue
                        self._updateQueueEntry(queueEntry, Crawler.URLStatus.DOWNLOADED)
                        # Mark download successfull
                        downloaded = True
                    except Crawler.UnsupportedNewspaper:
                        # Marke article as unsupported in queue
                        self._updateQueueEntry(queueEntry, Crawler.URLStatus.UNSUPPORTED)
                    # Print output
                    self._printEndDownloadStatusToTerminal(downloaded, numRelatedArticles)
                    # Calcualte time until next run
                    secToNextRun = Crawler.CRAWL_DELAY - (round(time.time()) - self._lastRun)
                    # Wait a time to avoid getting blocked by newspaper
                    time.sleep(0 if secToNextRun < 0 else secToNextRun)
                    # Run the task again
                    self._task()
                except Crawler.QueueIsEmpty:
                    Crawler._printQueueEmpty()
                    # Stop running the task
                    self._doRun = False

    def _queueRelatedArticles(self, relatedArticles): # This is ! efficient
        # Keep track of queue items
        queuedItems = 0
        # For each related articles, queue it
        for articleLink in relatedArticles:
            if not self._isLinkInQueue(articleLink):
                self._queueLink(articleLink)
                queuedItems += 1
            else:
                continue
        return queuedItems

    def _isLinkInQueue(self, link):
        # Search through the queue
        for queueEntry in self._queue:
            # If the link is present return true
            if link == queueEntry['url']:
                return True
        # Link not in queue, return false
        return False

    def _printPreDownloadStatusToTerminal(self, url):
        #Crawler.screen_clear()
        print('----------- Periodic run -----------')
        print('Queue index: ' + str(self._queueIndex))
        print('Queue length: ' + str(len(self._queue)))
        print('Downloading article: ' + url)
        
    def _printEndDownloadStatusToTerminal(self, downloaded, numRelatedArticles):
        #Crawler.screen_clear()
        print('Article status: ' + 'Downloaded' if downloaded else 'Not downloaded' )
        print('Queueing new articles: ' + str(numRelatedArticles))
        print('New queue length: ' + str(len(self._queue)))
        print('----------- End run -----------')

    @staticmethod
    def _printQueueEmpty():
        print('----------- Periodic run -----------')
        print('Queue exhausted. Stopping.')
        print('----------- End run -----------')

    @staticmethod
    def _unsupportedNewspaper(*kwargs):
        raise Crawler.UnsupportedNewspaper()

    @staticmethod
    def _saveEntryToOutput(outFileName, articleEntry):
        # Open the output file
        try:
            # Try creating the file
            with open(outFileName, "x") as outfile:
                # Dump the new data
                json.dump([articleEntry], outfile)
        except FileExistsError: # If the file exists, an exception is thrown
            with open(outFileName, "r+") as outfile:
                # Load the current data from the file
                entries = json.load(outfile)
                # Add new data to the entry
                entries.append(articleEntry)
                # Reset the file pointer
                outfile.seek(0)
                # Dump the new data
                json.dump(entries, outfile)

# On keyboard interrupt or shutdown
def signal_handler(signal, frame):
    print('----------- Exiting -----------')
    print("Terminat signal recieved")
    raise ExitProgram()

# Program exit exception
class ExitProgram(Exception):
    pass

# Main
if __name__ == '__main__':
    # Attatch listener for shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # Create an instance of the crawler class
    crawler = Crawler()
    #crawler.addArticle('https://www.bt.dk/samfund/han-vandt-danmarkshistoriens-naeststoerste-lottogevinst-nu-fortaeller-han-hvordan')
    #crawler.addArticle('https://www.bt.dk/royale/efter-royalt-skilsmissedrama-nu-reagerer-prins-louis-ekshustru')
    crawler.curlAllNewspapers()
    # Monitor program status
    try:
        crawler.run()
    except ExitProgram:
        print("Program killed, running cleanup")
        crawler.finalize()
    finally:
        print("Cleanup completed")
        print('----------- Exiting -----------')
