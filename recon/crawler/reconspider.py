from __future__ import with_statement

from ConfigParser import ParsingError
import datetime
import django
import os
from scrapy import signals
import scrapy
from scrapy.crawler import Crawler
from scrapy.exceptions import CloseSpider
from scrapy.http import Request, HtmlResponse
from scrapy.selector import Selector
from scrapy.signalmanager import SignalManager
from scrapy.utils.project import get_project_settings
from scrapy.xlib.pydispatch import dispatcher
import sys
from twisted.internet import reactor
from urlparse import urlparse
import logging
from django.conf import settings
import requests

from items import CitationItem
from recon.models import SearchList, ReconTopic, Citation, WatchList
from readability.readability import Document
import recon.tasks

sys.path.append(settings.PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recon_site.settings")
django.setup()


class ReconSpider(scrapy.Spider):

    name = "reconcrawler"

    def __init__(self, topic_id=1, full_mode=False, *args, **kwargs):
        # mode - True - full scrap - includes the full site of starting urls, and full site of
        # allowed urls
        # mode - False - quick scrap - includes only the paths specified under allowed urls,
        # and does NOT include the full site of starting urls, unless it is added as an
        # allowed domain in allowed_domains

        super(ReconSpider, self).__init__(*args, **kwargs)
        self.topic_id = topic_id
        self.full_mode = full_mode  # default is QuickScrap
        self.logger = logging.getLogger('logs.crawler.' + str(self.topic_id))
        self.watch_list = WatchList.objects.filter(
            topic_fk_id=self.topic_id).values_list(
            'id',
            'url')
        self.search_list = SearchList.objects.filter(  # what it is looking for
            topic_fk_id=self.topic_id, is_url=1).values_list('id', 'term')
        self.keyword_list = SearchList.objects.filter(
            topic_fk_id=self.topic_id,
            is_url=0).values_list(
            'id',
            'term')

        self.allowed_domains = self._getAllowedDomains()

        #self.start_urls = self._getWatchList()

    def start_requests(self):
        # scrapy.Spider.start_requests(self)
        for watch_id, url in self.watch_list:
            request = scrapy.Request(url, callback=self.parse)
            temp = urlparse(url)
            allowed_url = temp.scheme + '://' + temp.netloc
            if not self.full_mode:
                allowed_url += temp.path.rsplit('/', 1)[0]
            request.meta['item'] = {
                "watch_id": watch_id,
                "allowed_url": allowed_url}
            self.logger.info("Start URL:" + allowed_url)
            yield request

    def parse(self, response):
        """
        (Response) -> Nonetype

        takes a response object, finds the links within the object, and
        follows the links if they match a target list or keyword.
        """

        task = ReconTopic.objects.get(id=self.topic_id)
        if task.crawl_status == task.STOP:
            self.logger.info('Force stop crawler')
            raise CloseSpider('Force closed')
        if not isinstance(response, scrapy.http.response.html.HtmlResponse):
            return
        # looks for the existence of a keyword in the response object
        item = response.meta['item']
        watch_id = item['watch_id']
        allowed_url = item['allowed_url']
        page_url = response.url
        print 'Crawling : ' + page_url
        self.logger.info('Crawling : ' + page_url)
        textbody = self._getResponseText(response)
        page_title = response.xpath('//title/text()').extract()[0]

        for search_id, keyword in self.keyword_list:
            if keyword in textbody and not self._citationExists(
                    page_url, keyword):
                self._warcRecord(page_url)
                item = self._addCitation(
                    page_url,
                    page_title,
                    keyword,
                    search_id,
                    watch_id)
                self.logger.info(
                    'Found citation to keyword: ' +
                    item['links_to'])
                yield item
                # yield item

        for link_url in response.xpath('//a/@href').extract():
            # if this page is within the links we are looking for, and its not
            # yet in the database, add it
            search_id = self._findLink(link_url)
            if search_id and not self._citationExists(page_url, link_url):
                self._warcRecord(link_url)
                self._warcRecord(page_url)
                item = self._addCitation(
                    page_url,
                    page_title,
                    link_url,
                    search_id,
                    watch_id)
                self.logger.info(
                    'Found citation to website: ' +
                    item['links_to'])
                yield item

            # now, if we find a hyperlink from the page
            abs_url = self._getAbsoluteUrl(response.url, link_url)

            if abs_url:  # follow all links
                if abs_url.startswith(allowed_url):
                    request = scrapy.Request(abs_url, callback=self.parse)
                    request.meta['item'] = {
                        "watch_id": watch_id,
                        "allowed_url": allowed_url}
                    #print( '\033[1;47m crawl: %s\033[1;m' % abs_url)
                    yield request

    def _getAllowedDomains(self):
        """
           (None) -> List
           Returns a list of all urls which the spider will be allowed to crawl.
           For websites starting with www, it returns the url without the www,
           so site names such as live.aljerra.com can be allowed as well.
           """
        l = []
        for watch_id, url in self.watch_list:
            l.append(urlparse(url).hostname)
        return l

    def _getResponseText(self, response):
        '''
        (reponse) -> Text
        Returns text within the body of an HttpResponse object.
        '''
        readability = Document(response.body)
        content = readability.title() + readability.summary()
        return content

    def _getAbsoluteUrl(self, page_url, link_url):
        """
        (str, str) -> str
        Return the aboslute url, constructed from domain names and
        relative urls.
        """
        sch = urlparse(page_url).scheme
        if link_url.startswith("https://") or link_url.startswith("http://"):
            abs_url = link_url
        elif link_url.startswith("//"):
            abs_url = sch + ":" + link_url
        # relative url which should be concatenated with domain name
        elif link_url.startswith("/"):
            hs = urlparse(page_url).hostname
            abs_url = str(sch) + "://" + str(hs) + link_url
        # relative url which should be taken at previous level
        elif link_url.startswith(".."):
            ls = link_url.split('/')
            back_one_level = ls.count("..")
            temp = page_url
            for i in range(back_one_level):
                temp = self._doubleDots(temp)
            abs_url = temp + link_url.split('/')[-1]
        elif link_url.startswith("."):
            abs_url = page_url + link_url[2:]
        elif link_url and link_url[0].isalpha():
            abs_url = page_url + link_url
        else:
            abs_url = ""
        return abs_url

    def _citationExists(self, page_url, ref):
        """
        (string, string) -> Bool
        Returns True if a citation matches the url and links to
        meaning this citation already exists in the database
        used for both keywords and references
        """
        if Citation.objects.filter(url=page_url, links_to=ref):
            return True
        return False

    def _warcRecord(self, url):
        """
           (str) -> None
           Connects to the front end and set up a link for a warc archieve of a
           particular item.
        """
        recon.tasks.create_warc.delay(url)

    def _addCitation(
            self, page_url, page_title, links_to, search_id, watch_id):
        """
        (str, str, str) -> CitationItem
        Returns a newly created citationItem with information regarding its
        url, title, linking status, and timestamp
        """
        """"
        item = Citation.objects.create(  # crawled citation - link
            crawled_timestamp=datetime.datetime.now(),
            url=page_url,  # where we found it
            url_title=page_title,
            links_to=links_to,  # al jerra
            topic_fk_id=self.topic_id,
            watch_fk_id=watch_id,
            search_fk_id=search_id
            
        return item
        )
        """

        item = CitationItem()
        item["url"] = page_url
        item["url_title"] = page_title
        item["links_to"] = links_to
        item["topic_fk"] = ReconTopic.objects.get(id=self.topic_id)
        item["search_fk"] = SearchList.objects.get(id=search_id)
        item["watch_fk"] = WatchList.objects.get(id=watch_id)
        item["crawled_timestamp"] = datetime.datetime.now()
        item.save()
        return item

    def _findLink(self, link_url):
        """
        (str) -> Bool
        for each link, determines whether current link is within a list of
        target urls. Returns true iff this link is within a list of target
        domains
        """
        for id, domain in self.search_list:
            if domain in link_url:
                return id
        return None

    def _doubleDots(self, url):
        """
        (str)->str
        takes an absolute url, and returns the previous level of the url
        >>>_doubleDots("http://www.aljazeera.com/programmes/surprisingeurope/")
        http://www.aljazeera.com/programmes/
        >>>_doubleDots("http://www.aljazeera.com/programmes/surprisingeurope.html")
        http://www.aljazeera.com/

        """
        index_last_slash = url.rfind('/')
        index_sec_last_slash = url.rfind('/', 0, index_last_slash - 1)
        #print("result double dot: ", url[0:index_sec_last_slash + 1])
        return url[0:index_sec_last_slash + 1]


def run(topic_id):
    topic = ReconTopic.objects.get(id=topic_id)
    if topic:
        spider = ReconSpider(topic_id)
        settings = get_project_settings()
        crawler = Crawler(settings)
        crawler.signals.connect(reactor.stop, signal=signals.spider_closed)
        crawler.configure()
        crawler.crawl(spider)
        crawler.start()
        reactor.run()
    else:
        print "Invalid topic id"


def main():
    logger = logging.getLogger('logs.crawler.1')
    logger.setLevel(logging.INFO)
    file_path = os.path.join(settings.PROJECT_ROOT, 'logs/crawler/')
    file_handler = logging.FileHandler(file_path + '1.log')
    logger.addHandler(file_handler)
    logger.info('Started')
    run(1)
    logger.info('Finished')

if __name__ == "__main__":
    main()
