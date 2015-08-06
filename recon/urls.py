from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView, ListView, RedirectView
from recon import views

urlpatterns = patterns('',
                       url(r'^$', views.site_home, name='home'),
                       url(r'^topic/(?P<topic_id>\d+)/$',
                           views.networkgraph,
                           name='dashboard'),
                       url(r'^topic/(?P<topic_id>\d+)/data.json$',
                           views.get_network_graph_data,
                           name='get_network_graph_data'),
                       url(r'^topic/(?P<topic_id>\d+)/twitter-network-graph/$',
                           views.tw_networkgraph,
                           name='twitter_network_graph'),
                       url(r'^topic/(?P<topic_id>\d+)/twitter-network-graph/data.json$',
                           views.tw_get_network_graph_data,
                           name='twitter_get_network_graph_data'),

                       url(r'^topic/new/$',
                           views.new_topic,
                           name='new_topic'),
                       url(r'^topic/(?P<topic_id>\d+)/twitter-barchart/$',
                           views.barchart_twitter,
                           name='barchart_twitter'),
                       url(r'^topic/(?P<topic_id>\d+)/barchart/$',
                           views.barchart,
                           name='barchart'),
                       url(r'^topic/(?P<topic_id>\d+)/citation/$',
                           views.citation,
                           name='citation'),
                       url(r'^topic/(?P<topic_id>\d+)/twitter-citation/$',
                           views.twitter_citation,
                           name='twitter_citation'),

                       url(r'^topic/(?P<topic_id>\d+)/(?P<list_name>.+)/manage/$',
                           views.list,
                           name='list'),
                       url(r'^topic/(?P<topic_id>\d+)/(?P<list_name>.+)/manage/new/$',
                           views.create,
                           name='new'),
                       url(r'^topic/(?P<topic_id>\d+)/(?P<list_name>.+)/manage/edit/(?P<id>\d+)/$',
                           views.update,
                           name='edit'),
                       url(r'^topic/(?P<topic_id>\d+)/(?P<list_name>.+)/manage/delete/(?P<id>\d+)/$',
                           views.delete,
                           name='delete'),
                       url(r'^topic/(?P<topic_id>\d+)/crawler/get_crawl_log$',
                           views.get_crawl_log,
                           name='get_crawl_log'),
                       url(r'^topic/(?P<topic_id>\d+)/twitter-crawler/get_crawl_log_twitter$',
                           views.get_crawl_log_twitter,
                           name='get_crawl_log_twitter'),
                       url(r'^topic/(?P<topic_id>\d+)/crawler/$',
                           views.crawler,
                           name='crawler'),
                       url(r'^topic/(?P<topic_id>\d+)/twitter-crawler/$',
                           views.twitter_crawler,
                           name='twitter_crawler'),
                       url(r'^js/', include('djangojs.urls')),
                       url(r'^topic/(?P<topic_id>\d+)/warc/(?P<warc_url>.+)',
                           views.recon_frame,
                           name='crawler'),
                       )