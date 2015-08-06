# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.contrib.djangoitem import DjangoItem
from scrapy.item import Item, Field

from recon.models import Citation


class CitationItem(DjangoItem):
    django_model = Citation


class Page(Item):
    url = Field()
    title = Field()
    size = Field()
    referer = Field()
    newcookies = Field()
    body = Field()
