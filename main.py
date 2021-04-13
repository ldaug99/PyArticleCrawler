# Imports
import signal, time, os
import json
import traceback
from urllib.parse import urlparse

# Include classes and subfolders
from src.newspapers.bt import BT

# Crawler class definition
class Crawler:
    NEWSPAPERS = [
        BT
    ]

    CRAWL_DELAY = 20 # Delay in milliseconds between each page download

    QUEUE_STORE_FILE = '.queue'

    class URLStatus:
        PENDING = 0
        DOWNLOADED = 1
        UNSUPPORTED = 2
        UNAVALIABLE = 3
        INVALID = 4
        ISINDEX = 5
        FAILED = 6

        TEXT_STATUS = {
            PENDING: 'Pending download',
            DOWNLOADED: 'Downloaded',
            UNSUPPORTED: 'The newspaper is unsupported',
            UNAVALIABLE: 'The URL is inavaliable',
            INVALID: 'The URL is invalid',
            ISINDEX: 'The page is an index',
            FAILED: 'Download failed',
        }

    class UnsupportedNewspaper(Exception):
        pass

    class QueueIsEmpty(Exception):
        pass

    def __init__(self, outFileName = 'articles.json', storeQueue = True):
        self._downloadedArticles = 0
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
            # # Instantiate the newspaper to the front page
            # np = newspaper(newspaper.NEWSPAPER_URL)
            # Add the article
            self.addArticle(newspaper.NEWSPAPER_URL)
            # # Get related articles
            # for articleURL in np.getLinkedArticles():
            #     # Add the article
            #     self.addArticle(articleURL)

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
        # Get the length of the queue
        queueLength = len(self._queue)
        # Keep incrementing the queueIndex, until the next element in the queue is found
        while self._queueIndex < queueLength:
            # Get the queue entry
            queueEntry = self._queue[self._queueIndex]
            # Increment the queueIndex
            self._queueIndex += 1
            # If the article is already downloaded mark if
            if queueEntry['status'] == Crawler.URLStatus.DOWNLOADED:
                self._downloadedArticles += 1
            # Check the status of the entry
            if queueEntry['status'] == Crawler.URLStatus.PENDING or queueEntry['status'] == Crawler.URLStatus.UNSUPPORTED:
                # Return the queueEntry
                return queueEntry
        # Raise exception if the queue is exhausted
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
                    articleStatus = Crawler.URLStatus.FAILED
                    numRelatedArticles = 0
                    # Get the newspaper from the URL
                    newspaper = Crawler._getNewspaperFromURL(queueEntry['url'])
                    # Try getting the article from the newspaper
                    try:
                        newspage = newspaper(queueEntry['url'])
                        # Get the articleEntry
                        articleEntry = newspage.getArticleEntry()
                        if articleEntry:
                            # Save the article
                            Crawler._saveEntryToOutput(self._outFileName, articleEntry)
                            # Count up in downloaded articles
                            self._downloadedArticles += 1
                            # Update the article status
                            articleStatus = Crawler.URLStatus.DOWNLOADED
                        else:
                            # The page does not contain an article, just get related
                            articleStatus = Crawler.URLStatus.ISINDEX 
                        # Queue related articles
                        numRelatedArticles = self._queueRelatedArticles(newspage.getLinkedArticles())
                        # Mark the entry as downloaded in the queue
                        self._updateQueueEntry(queueEntry, articleStatus)
                    except Crawler.UnsupportedNewspaper:
                        # Marke article as unsupported in queue
                        self._updateQueueEntry(queueEntry, Crawler.URLStatus.UNSUPPORTED)
                    # Print output
                    self._printEndDownloadStatusToTerminal(articleStatus, numRelatedArticles)
                    # Calcualte time until next run
                    millisecToNextRun = Crawler.CRAWL_DELAY - (round(time.time() * 1000) - self._lastRun)
                    # Wait a time to avoid getting blocked by newspaper
                    time.sleep(0 if millisecToNextRun < 0 else millisecToNextRun)
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
        
    def _printEndDownloadStatusToTerminal(self, articleStatus, numRelatedArticles):
        #Crawler.screen_clear()
        print('Article status: ' + Crawler.URLStatus.TEXT_STATUS[articleStatus] )
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
        print("Stop command recieved")
    except Exception:
        print("Unhandled exception")
        traceback.print_exc()
    finally:
        crawler.finalize()
        print("Cleanup completed")
        print('----------- Exiting -----------')
