from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
import urlparse
# Create your models here.


class ReconTopic(models.Model):

    def list_name(self):
        return

    def __unicode__(self):
        return(self.topic)

    def get_crawl_status(self):
        for choice in self.STATUS_CHOICES:
            if self.crawl_status == choice[0]:
                return choice[1]

    def get_twitter_status(self):
        for choice in self.STATUS_CHOICES:
            if self.twitter_status == choice[0]:
                return choice[1]
    READY = 0
    RUNNING = 1
    STOP = 2
    STATUS_CHOICES = (
        (READY, 'Ready'),
        (RUNNING, 'Running'),
        (STOP, 'Stop'),
    )
    topic = models.CharField(max_length=200, unique=True)
    user = models.ForeignKey(User)
    crawl_status = models.IntegerField(choices=STATUS_CHOICES, default=READY)
    twitter_status = models.IntegerField(choices=STATUS_CHOICES, default=READY)


class SearchList(models.Model):
    CHOICES = (
        (0, 'No'),
        (1, 'Yes'),
    )

    def clean(self):
        # Don't allow draft entries to have a pub_date.
        if self.is_url == 1:
            validate = URLValidator()
            try:
                url_fields = list(urlparse.urlsplit(self.term))
                if not url_fields[0]:
                    # If no URL scheme given, assume http://
                    url_fields[0] = 'http'
                if not url_fields[1]:
                    # Assume that if no domain is provided, that the path segment
                    # contains the domain.
                    url_fields[1] = url_fields[2]
                    url_fields[2] = ''
                    # Rebuild the url_fields list, since the domain segment may now
                    # contain the path too.
                url = urlparse.urlunsplit(url_fields)
                validate(url)
                self.term = url
            except ValidationError as e:
                raise ValidationError(e)

    def name(self):
        return self.term

    def __unicode__(self):
        return('[' + str(self.topic_fk) + ']' + self.term)

    term = models.CharField(max_length=200)
    is_url = models.IntegerField(choices=CHOICES, default=1)
    topic_fk = models.ForeignKey(ReconTopic)


class WatchList(models.Model):

    def name(self):
        return self.url

    def __unicode__(self):
        return('[' + str(self.topic_fk) + ']' + self.url)

    url = models.URLField(max_length=200)
    topic_fk = models.ForeignKey(ReconTopic)


class Citation(models.Model):

    def __unicode__(self):
        return('[' + str(self.topic_fk) + ']' + self.url_title + ' --> ' + self.links_to)

    def has_hyperlink(self):
        return (self.links_to.startswith("http"))

    topic_fk = models.ForeignKey(ReconTopic)
    watch_fk = models.ForeignKey(WatchList)
    search_fk = models.ForeignKey(SearchList)
    url = models.URLField(max_length=200)
    url_title = models.CharField(max_length=200)
    links_to = models.CharField(max_length=200)
    publish_timestamp = models.DateTimeField(null=True)
    crawled_timestamp = models.DateTimeField(null=True)


class TwitterHandle(models.Model):

    def __unicode__(self):
        return(self.handle)

    def name(self):
        return self.handle
    handle = models.CharField(max_length=18)
    topic_fk = models.ForeignKey(ReconTopic)
    tweet_count = models.IntegerField(default=20)


class TwitterCitation(models.Model):

    def __unicode__(self):
        return('[' + str(self.topic_fk) + ']' + str(self.handle_fk) + "->" + self.links_to)

    topic_fk = models.ForeignKey(ReconTopic)
    handle_fk = models.ForeignKey(TwitterHandle)
    search_fk = models.ForeignKey(SearchList)
    links_to = models.CharField(max_length=200)
    tweet = models.CharField(max_length=200)
    datetime = models.DateTimeField()
