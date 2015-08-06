from datetime import datetime
import django
import httplib
import json
import os
import re
import sys
import urllib2
import urlparse
import time
import requests
import tweepy
from tweepy.cursor import Cursor
from django.conf import settings

sys.path.append(settings.PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recon_site.settings")
django.setup()

from recon.models import SearchList, ReconTopic, TwitterHandle, TwitterCitation
import logging
from django.conf import settings


#from twitter.models import TwitterHandle, TwitterCitation


# Necessary information
consumer_key = "SiPoSIi2Gxj8MC1bUwW8GK8RY"
consumer_secret = "3Edk35IzRxCoNK5ILLmOG7ZcwcWPMTzTornMgKshaJqQI7Dsul"
access_token = "2893945126-MfKO0YLE5wNbeJhlyxCfYhhQAdJrMNYJbxS8uTv"
access_token_secret = "GfhSRj9z6lAkTsjI8f8xksU4sz2DaR9ANbuAD6W4SqpSB"

# setup
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)


class UserDoesNotExist(Exception):
    pass


class ZeroTweetsRequested(Exception):
    pass


class ForceClose(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class TwitterScraper:

    def __init__(self, topicid):
        '''Input: website_list is a list which contains website names in the form "XXX." , user_list is a list of twitter users to get data from
        Output: None unless UserDoesNotExist error is raised.
        '''
        self.logger = logging.getLogger('logs.twitter.' + str(topicid))
        self.website_list = SearchList.objects.filter(topic_fk_id=topicid, is_url=1).values_list(
            'id', 'term')

        self.keyword_list = SearchList.objects.filter(topic_fk_id=topicid, is_url=0).values_list(
            'id', 'term')

        # holds twitter handles
        self.user_list = TwitterHandle.objects.filter(
            topic_fk_id=topicid).values_list(
            'handle', 'tweet_count')
        self.topic = topicid
        # contains list of users from user_list that do not exist

    def run(self):
        try:
            for handle, tweet_count in self.user_list:
                self.logger.info("Twitter Handle:" + handle)
                self.add_info_to_database(handle, tweet_count)
        except ForceClose:
            return
        return

    def _user_exists(self, user_ID):
        '''Checks if twitter id 'user' exists
        Input: 'user' is a string
        Output: A boolean'''
        try:
            user_exist = api.search_users(user_ID)

            if (user_exist != []):
                return True

        except:
            return False

    def get_last_N_tweets(self, user_ID, n=20):
        '''
        (self, str, int) -> list(dict)
        Returns last n tweets of user with twitter handle user_ID in a json format

        >>>self.last_N_tweets("TIME", 1)
        '''

        list_tweets = []

        if (n == 0):
            raise ZeroTweetsRequested(
                "Must request to retrieve 1 or more tweets")
        else:
            result = Cursor(api.user_timeline, id=user_ID).items(n)
            for tweet in result:
                list_tweets.append(tweet._json)

        return list_tweets

    def get_tweet_text(self, tweet):
        '''
        (self, dict) -> list
        Takes a list of dicts (json format) and returns a the text of each tweet in a list of strings.

        >>>self.get_tweet_text(json_list)
        '''
        tweet_text = []

        text = tweet['text'].encode('utf-8')

        tweet_text.append(text)

        return tweet_text

    def get_tweet_link(self, tweet):
        '''
        (self, dict) -> list
        Get tweet info (json format), parse it to get links to website user linked to (if any) and return a list of website urls.
        Returns empty list if no links found in tweet
        '''
        website_list = []

        urls = tweet['entities']['urls']

        for i in urls:
            website = i['expanded_url']

            website = self._expand_url(website)

            if website:

                website_list.append(website.encode('utf-8'))

        return website_list

    def get_tweet_date(self, tweet):
        '''
        (self, dict) -> datetime_t
        Get a dictionary (json format) and returns the date and time the tweet was tweeted.
        '''

        # format of date is "Thu Oct 16 19:30:06 +0000 2014", +0000 is the
        # timezine
        date = tweet['created_at']

        # convert date to datetime format

        d = datetime.strptime(date, '%a %b %d %H:%M:%S +0000 %Y')

        return d

    def _check_match(self, source_website, url):
        '''
        (str, str) -> bool
        Returns if source_website is equal to the url domain

        >>>self._check_match('time.com', 'http://time.com/3513196/ebola-congress/')
        True
        >>>self._check_match('nytimes.com"t', http://time.com/3513196/ebola-congress/')
        False

        '''
        if source_website == "":
            return False

        match = re.search(source_website.lower(), url.lower())
        if match:
            return True

        return False

    def add_tweet_keyword(self, tweet_text, tweet_date, handle_id):
        '''
        (self, list, DateTime, TwitterHandle) -> None
        Get tweet text, date of tweet, handle id of handle that tweeted the tweet. Adds tweet to database
        if tweet contains keyword from self.keyword_list

        '''

        for search_id, keyword in self.keyword_list:
            # checks if keyword matched in tweet is true and checks if tweet already exists in
            # database. If it doesn't then add to database
            if self._check_match(keyword, tweet_text) and not TwitterCitation.objects.filter(
                    handle_fk=handle_id, search_fk_id=search_id, topic_fk_id=self.topic, links_to=keyword, datetime=tweet_date).exists():
                self.logger.info("Found citation to keyword:  " + keyword)
                b = TwitterCitation.objects.create(
                    handle_fk=handle_id,
                    search_fk_id=search_id,
                    topic_fk_id=self.topic,
                    links_to=keyword,
                    tweet=tweet_text,
                    datetime=tweet_date)
                b.save()

    def add_tweet_url(self, tweet_text, tweet_date, handle_id, url):
        '''
        (self, list, DateTime, TwitterHandle, list) -> None
        Saves tweet to database if tweet links to a domain that is in self.website_list
        '''

        for search_id, website in self.website_list:

            if (len(url) >= 1):

                # loop through url
                for tweet_link in url:
                    if self._check_match(website, tweet_link) and not TwitterCitation.objects.filter(
                            handle_fk=handle_id, search_fk_id=search_id, topic_fk_id=self.topic, links_to=tweet_link, datetime=tweet_date).exists():
                        self.logger.info(
                            "Found citation to website:  " +
                            tweet_link)
                        b = TwitterCitation.objects.create(
                            handle_fk=handle_id,
                            search_fk_id=search_id,
                            topic_fk_id=self.topic,
                            links_to=tweet_link,
                            tweet=tweet_text,
                            datetime=tweet_date)
                        b.save()

    def add_info_to_database(self, tweet_handle, n=20):
        '''
        (self, str, int) -> None
        Gets twitter handle, and uses integer n to get last n tweets. If website posted
        in tweet matches website in website_list then add tweet, twitter handle, expanded url
        and date and time tweet was tweeted to sql database
        If item added to database, returns true.==

        '''
        handle_id = TwitterHandle.objects.get(handle=tweet_handle)
        if not handle_id:
            return

        tweet_list = self.get_last_N_tweets(
            tweet_handle, n)  # a list of dictionaries (json format)

        for tweet in tweet_list:
            task = ReconTopic.objects.get(id=self.topic)
            if task.twitter_status == task.STOP:
                self.logger.info('Force stop twitter crawler')
                raise ForceClose('Force closed')
            url = self.get_tweet_link(tweet)  # gets url from tweet
            tweet_date = self.get_tweet_date(tweet)
            tweet_text = self.get_tweet_text(tweet)[0]
            self.logger.info("\tTweet:" + tweet_text)
            self.add_tweet_keyword(tweet_text, tweet_date, handle_id)
            self.add_tweet_url(tweet_text, tweet_date, handle_id, url)

    def _expand_url(self, url):
        '''
        Input: A URL link
        Output: An expanded URL link (ie converts ti.me to time.com)
        Returns a valid, expanded URL.
        If URL not valid, return nothing
        '''

        m = re.match("^https?://", url)
        if m:
            try:
                r = requests.get(url, verify=False)
                return r.url
            except:
                return None
        else:
            return None


def run(topic_id):
    topic = ReconTopic.objects.get(id=topic_id)
    if topic:
        T = TwitterScraper(topic_id)
        T.run()
    else:
        print "Invalid topic id"


def main():
    topic_id = 1
    logger = logging.getLogger('logs.twitter.' + str(topic_id))
    logger.setLevel(logging.INFO)
    file_path = os.path.join(settings.PROJECT_ROOT, 'logs/twitter/')
    file_handler = logging.FileHandler(file_path + str(topic_id) + '.log')
    logger.addHandler(file_handler)
    logger.info('Twitter Crawl Started')
    run(topic_id)
    logger.info('Twitter Crawl Finished')

if __name__ == '__main__':
    main()
