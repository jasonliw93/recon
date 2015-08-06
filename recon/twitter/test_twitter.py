from django.contrib.auth.models import User
from django.test import TestCase
import os
import sys

import tweepy

from recon.models import SearchList, ReconTopic, TwitterHandle, TwitterCitation
from recon.twitter.twitter_scraper import TwitterScraper
sys.path.append(os.path.realpath("../.."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recon_site.settings")


# Create your tests here.
# import datetime

# Necessary information
consumer_key = "SiPoSIi2Gxj8MC1bUwW8GK8RY"
consumer_secret = "3Edk35IzRxCoNK5ILLmOG7ZcwcWPMTzTornMgKshaJqQI7Dsul"
access_token = "2893945126-MfKO0YLE5wNbeJhlyxCfYhhQAdJrMNYJbxS8uTv"
access_token_secret = "GfhSRj9z6lAkTsjI8f8xksU4sz2DaR9ANbuAD6W4SqpSB"

# setup
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)


class TwitterTest(TestCase):

    def setUp(self):
        User.objects.create_user(
            username='twittertester',
            email='tester@test.com',
            password='helloworld')
        ReconTopic.objects.create(
            topic="twitter_test",
            user=User.objects.get(
                username='twittertester'))
        TwitterHandle.objects.create(
            handle="TestRecon",
            topic_fk_id=1)
        SearchList.objects.create(  # Domain is the Israeli sites #domains of the start urls
            term="http://www.nytimes.com",
            is_url=1,
            topic_fk_id=1)
        SearchList.objects.create(  # keyword
            term="no link",
            is_url=0,
            topic_fk_id=1)
        self.twitter = TwitterScraper(1)

    def tearDown(self):
        self.twitter = None

    # Test 1: Test _expand_url(self, url) function
    def test_expand_url_normal(self):
        url = "http://t.co/EgwENSBYWK"
        full_url = self.twitter._expand_url(url).encode('utf-8')

        self.assertEquals(
            "http://stream.aljazeera.com/story/201411121150-0024338",
            full_url)

    def test_expand_url_none(self):
        url = "www.google.com"

        self.assertEquals(None, self.twitter._expand_url(url))

    def test_expand_url_empty(self):
        url = ""

        self.assertEquals(None, self.twitter._expand_url(url))

    # Test2: test function _check_match(self, source_website, url)
    def test_check_match_true(self):
        source = "time.com"
        url = "http://time.com/3513196/ebola-congress/"
        self.assertTrue(self.twitter._check_match(source, url))

    def test_check_match_false(self):
        source = ""
        url = "http://google.com"
        self.assertFalse(self.twitter._check_match(source, url))

    # Test 3: user_exists(self, user_ID)
    def test_user_exists_true(self):
        user = "TheKingJeet"
        self.assertTrue(self.twitter._user_exists(user))

    # def test_user_exists_empty(self):
        # user = ""
        # self.assertFalse(self.twitter._user_exists(user))

    # def test_user_exists_false(self):
        # user = "lsdfkdsklfdjslkfjsdfjslkfdjf"
        # self.assertFalse(self.twitter._user_exists(user))

    # Test4: get_tweet_text(self, tweet), tweet is json
    def test_get_tweet_text(self):
        tweet = self.twitter.get_last_N_tweets("TheKingJeet", 4)
        tweet_info = tweet[3]  # dictionary format
        self.assertEquals(
            self.twitter.get_tweet_text(tweet_info)[0],
            "this is a tweet")

    def test_get_tweet_hashtags(self):
        tweet = self.twitter.get_last_N_tweets("TheKingJeet", 3)
        tweet_info = tweet[2]
        self.assertEquals(
            self.twitter.get_tweet_text(tweet_info)[0],
            "This is a #tweet with #many #hashtags")

    # Test 5: test get_tweet_link(self, tweet), tweet is dictionary format
    def test_get_tweet_link_empty(self):
        tweet = self.twitter.get_last_N_tweets("TheKingJeet", 3)
        tweet_info = tweet[2]

        self.assertEquals(self.twitter.get_tweet_link(tweet_info), [])

    def test_get_tweet_link_one_link(self):
        tweet = self.twitter.get_last_N_tweets("TheKingJeet", 1)
        tweet_info = tweet[0]
        link = self.twitter.get_tweet_link(tweet_info)[0]

        domain = "google.ca"
        self.assertTrue(self.twitter._check_match(domain, link))

    def test_get_tweet_link_multiple_links(self):
        tweet = self.twitter.get_last_N_tweets("TheKingJeet", 2)
        tweet_info = tweet[1]
        self.assertEquals(self.twitter.get_tweet_link(tweet_info), ['http://time.com/3581310/youtube-music-key-beta-paid-streaming-service/',
                                                                    'https://docs.djangoproject.com/en/dev/intro/tutorial01/'])

    # test 6: test tweet_date(tweet), tweet is dictionary
    def test_tweet_date_correct(self):
        tweet = self.twitter.get_last_N_tweets("TheKingJeet", 1)
        tweet_info = tweet[0]
        date = self.twitter.get_tweet_date(tweet_info)
        self.assertEquals(date.year, 2014)
        self.assertEquals(date.month, 11)
        self.assertEquals(date.day, 13)

    def test_tweet_date_correct(self):
        tweet = self.twitter.get_last_N_tweets("TheKingJeet", 1)
        tweet_info = tweet[0]
        date = self.twitter.get_tweet_date(tweet_info)
        self.assertEquals(date.year, 2014)
        self.assertEquals(date.month, 11)
        self.assertFalse(date.day == 12)

    # Test 7: add_info_to_database(self, tweet_handle, n=20)
    def test_add_to_database_TestRecon_link(self):
        self.twitter.add_info_to_database("TestRecon", 2)
        citation = TwitterCitation.objects.filter(
            tweet='one link to target website http://t.co/pHaAJS7wDS')[0]
        self.assertEquals(
            citation.tweet,
            'one link to target website http://t.co/pHaAJS7wDS')
        self.assertEquals(
            citation.handle_fk,
            TwitterHandle.objects.get(
                handle="TestRecon"))
        self.assertTrue('nytimes.com' in citation.links_to)

    def test_add_to_database_testrecon_keyword(self):
        self.twitter.add_info_to_database("TestRecon", 2)
        citation = TwitterCitation.objects.filter(links_to="no link")[0]
        self.assertEquals(
            citation.tweet,
            'no link to a news website')
        self.assertEquals(
            citation.handle_fk,
            TwitterHandle.objects.get(
                handle="TestRecon"))
        self.assertEquals(
            citation.links_to,
            "no link")
