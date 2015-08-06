import datetime
from django.contrib.auth.models import User
from django.test import TestCase
from scrapy.contrib.djangoitem import DjangoItem
from scrapy.http import HtmlResponse

from items import CitationItem
from recon.crawler.reconspider import ReconSpider
from recon.models import SearchList, ReconTopic, Citation, WatchList


class SpiderTestCase(TestCase):

    def setUp(self):
        User.objects.create_user(
            username='tester',
            email='tester@test.com',
            password='top_secret')
        ReconTopic.objects.create(
            topic="test",
            user=User.objects.get(
                username='tester'))
        SearchList.objects.create(  # Domain is the Israeli sites #domains of the start urls
            term="http://www.testdomain.com",
            is_url=1,
            topic_fk_id=1)
        SearchList.objects.create(  # keyword
            term="testkeyword",
            is_url=0,
            topic_fk_id=1)
        WatchList.objects.create(  # crawl - starting urls
            url="http://www.example.com",
            topic_fk_id=1)
        Citation.objects.create(  # crawled citation - link
            crawled_timestamp=datetime.datetime.now(),
            url="www.example.com",  # where we found it
            url_title="example",
            links_to="www.google.com",  # al jerra
            topic_fk_id=1,
            watch_fk_id=1,
            search_fk_id=1
        )
        self.spider = ReconSpider(topic_id=1)

    def tearDown(self):
        self.spider = None
        self.spider2 = None

    """test getWatchList"""

    """test getResponseText"""

    def test_getResponseText_body_oneline(self):
        body = '<html><body><span>good</span></body></html>'
        response = HtmlResponse(url='http://example.com', body=body)
        self.assertEqual(
            self.spider._getResponseText(response),
            "<body><span>good</span></body>")

    def test_getResponseText_body_moreline_and_space(self):
        body = '<html><body><span>good\nwhats up</span></body></html>'
        response = HtmlResponse(url='http://example.com', body=body)
        self.assertEqual(
            self.spider._getResponseText(response),
            "<body><span>good\nwhats up</span></body>")

    def test_getResponseText_no_body(self):
        response = HtmlResponse(url='http://example.com')
        self.assertEqual(self.spider._getResponseText(response), "")

    """test citationExists"""

    def test_citationExists_True_urlmatch(self):
        self.assertTrue(
            self.spider._citationExists(
                "www.example.com",
                "www.google.com"))

    def test_citationExists_True_keywordmatch(self):
        Citation.objects.create(  # crawled citation - link
            crawled_timestamp=datetime.datetime.now(),
            url="www.example.com",
            url_title="example",
            links_to="testKey",
            topic_fk_id=1,
            watch_fk_id=1,
            search_fk_id=1)
        self.spider = ReconSpider(topic_id=1)
        self.assertTrue(
            self.spider._citationExists(
                "www.example.com",
                "testKey"))

    def test_citationExists_False_urlnomatch(self):
        self.assertFalse(
            self.spider._citationExists(
                "www.yahoo.com",
                "www.google.com"))

    def test_citationExists_False_refnomatch(self):
        self.assertFalse(
            self.spider._citationExists(
                "www.example.com",
                "www.haha.com"))

    def test_citationExists_False_bothnomatch(self):
        self.assertFalse(
            self.spider._citationExists(
                "www.yahoo.com",
                "www.haha.com"))

    def test_citationExists_Blank(self):
        self.assertFalse(self.spider._citationExists("", ""))

    """test add citation"""

    def test_addCitation_returntype(self):
        x = self.spider._addCitation(
            "www.page.ca",
            "THIS IS A PAGE",
            "www.linkto.com", 1, 1)
        self.assertTrue(isinstance(x, DjangoItem))

    def test_addCitation_toPopulatedDB(self):
        # add citation to an already populated database
        self.spider._addCitation(
            "www.page.ca",
            "THIS IS A PAGE",
            "www.linkto.com",
            1, 1)
        self.assertTrue(
            self.spider._citationExists(
                "www.page.ca",
                "www.linkto.com"))

    def test_addCitation_toBlankDB(self):
        # add citation to an empty database
        ReconTopic.objects.create(
            topic="test2",
            user=User.objects.get(
                username='tester'))
        self.spider2 = ReconSpider(topic=2)
        self.assertFalse(
            self.spider2._citationExists(
                "www.page.ca",
                "www.linkto.com"))
        self.spider2._addCitation(
            "www.page.ca",
            "THIS IS A PAGE",
            "www.linkto.com", 1, 1)
        self.assertTrue(
            self.spider2._citationExists(
                "www.page.ca",
                "www.linkto.com"))

    """test findLink """

    def test_findLink_True(self):
        self.assertTrue(self.spider._findLink("http://www.testdomain.com"))

    def test_findLink_False(self):
        self.assertFalse(self.spider._findLink("http://www.nothere.com"))

    def test_findLink_False_Blank(self):
        self.assertFalse(self.spider._findLink(""))

    """test getAbsoluteUrl and helper function"""

    def test_doubleDots_slashend(self):
        # makes sure double dots take the directory back two levels
        expected = "http://www.aljazeera.com/programmes/"
        self.assertEquals(
            self.spider._doubleDots(
                "http://www.aljazeera.com/programmes/surprisingeurope/"),
            expected)

    def test_doubleDots_htmlend(self):
        expected = "http://www.aljazeera.com/"
        self.assertEquals(self.spider._doubleDots(
            "http://www.aljazeera.com/programmes/surprisingeurope.html"), expected)

    def test_getAbsoluteUrl_slashstart(self):
        expected = "http://www.haha.com/takemehere/hi"
        self.assertEqual(
            self.spider._getAbsoluteUrl(
                "http://www.haha.com",
                "/takemehere/hi"),
            expected)

    def test_getAbsoluteUrl_httpsstart(self):
        # starts with https
        expected = "https://www.haha.com/takemehere/hi"
        self.assertEqual(
            self.spider._getAbsoluteUrl(
                "https://www.useless.come",
                "https://www.haha.com/takemehere/hi"),
            expected)

    def test_getAbsoluteUrl_httpstart(self):
        # starts with http
        expected = "http://www.haha.com/takemehere/hi"
        self.assertEqual(
            self.spider._getAbsoluteUrl(
                "http://www.useless.com",
                "http://www.haha.com/takemehere/hi"),
            expected)

    def test_getAbsoluteUrl_doubleslashstart_http(self):
        expected = "http://www.haha.com/takemehere/hi"
        self.assertEqual(
            self.spider._getAbsoluteUrl(
                "http://www.useless.com",
                "//www.haha.com/takemehere/hi"),
            expected)

    def test_getAbsoluteUrl_doubleslashstart_https(self):
        expected = "https://www.haha.com/takemehere/hi"
        self.assertEqual(
            self.spider._getAbsoluteUrl(
                "https://www.useless.com",
                "//www.haha.com/takemehere/hi"),
            expected)

    def test_getAbsoluteUrl_doubledotstart(self):
        expected = "https://www.haha.com/level1/level2_2"
        self.assertEqual(
            self.spider._getAbsoluteUrl(
                "https://www.haha.com/level1/level2/level3.html",
                "../level2_2"),
            expected)

    def test_getAbsoluteUrl_singledotstart(self):
        expected = "https://www.haha.com/level1/level2/level2_2"
        self.assertEqual(
            self.spider._getAbsoluteUrl(
                "https://www.haha.com/level1/level2/",
                "./level2_2"),
            expected)

    def test_getAbsoluteUrl_letterstart(self):
        # test incidences where only the name of a html file is given.
        expected = "https://www.haha.com/level1/level2/about.html"
        self.assertEqual(
            self.spider._getAbsoluteUrl(
                "https://www.haha.com/level1/level2/",
                "about.html"),
            expected)

    def test_getAbsoluteUrl_noLinkUrl(self):
        self.assertEqual(self.spider._getAbsoluteUrl("www.haha.com", ""), "")

    def test_getAbsoluteUrl_noPageUrl(self):
        self.assertEqual(
            self.spider._getAbsoluteUrl(
                "",
                "http://www.haha.com"),
            "http://www.haha.com")
