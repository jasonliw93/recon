from __future__ import with_statement

from django import forms
import django
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext, loader

from recon.forms import ReconTopicForm, SearchListForm, WatchListForm, TwitterHandleForm
from recon.models import Citation, ReconTopic, WatchList, TwitterHandle, SearchList, TwitterCitation
from recon.tasks import task_start_crawl, task_start_twitter
import os
from django.conf import settings
import json
from django.db.models import Count, Max


# Create your views here.


def custom_proc(request):
    topic_list = ReconTopic.objects.filter(
        user_id=request.user.id).order_by('-topic')
    return {
        'topic_list': topic_list,
    }


def topic_context(topic_id):
    topic = ReconTopic.objects.get(id=topic_id)
    return {
        'topic_title': topic.topic,
        'topic_id': topic_id,
        'explain': ''
    }


def tail(fname):
    with open(fname, "r") as f:
        f.seek(0, 2)           # Seek @ EOF
        fsize = f.tell()        # Get Size
        f.seek(max(fsize - 1024, 0), 0)  # Set pos @ last n chars
        lines = f.readlines()       # Read to end

    return ''.join(lines[-10:])


def get_crawl_log(request, topic_id):
    file_path = os.path.join(settings.PROJECT_ROOT, 'logs/crawler/')
    file = file_path + str(topic_id) + ".log"
    log_text = tail(file_path + str(topic_id) + ".log")
    return HttpResponse(log_text)


def get_crawl_log_twitter(request, topic_id):
    file_path = os.path.join(settings.PROJECT_ROOT, 'logs/twitter/')
    file = file_path + str(topic_id) + ".log"
    log_text = tail(file_path + str(topic_id) + ".log")
    return HttpResponse(log_text)


def site_home(request):
    return render(request, 'recon/home.html')


@login_required(login_url='/account/login/')
def topic_home(request, topic_id):
    topic = ReconTopic.objects.get(id=topic_id)
    #template = loader.get_template('recon/recon_base.html')
    context = {
        'topic_title': topic.topic,
        'topic_id': topic_id,
    }
    return render(request, 'recon/recon_base.html', context)


@login_required(login_url='/account/login/')
def new_topic(request, template_name='recon/form.html'):
    form = ReconTopicForm(request.POST or None)
    form.fields['topic'].label = 'Name'
    if not request.user.is_superuser:
        form.fields['user'].initial = request.user.id
        form.fields['user'].widget = forms.HiddenInput()
    if form.is_valid():
        new_topic = form.save()
        return redirect('dashboard', topic_id=new_topic.id)
        # return HttpResponseRedirect(reverse(topic_home,
        # args=(new_topic.id,)))
    data = {'form': form}
    return render(request, template_name, data)


@login_required(login_url='/account/login/')
def networkgraph(request, topic_id):
    data = topic_context(topic_id)
    return render(request, 'recon/network_graph.html', data)


def get_network_graph_data(request, topic_id):
    data = get_nodes_edge_data(topic_id)
    tojson = {"nodes": data[0] + data[1], "links": data[2]}
    print(tojson)
    json_data = json.dumps(tojson)
    return HttpResponse(json_data)


def get_nodes_edge_data(topic_id):
    data1 = []
    data2 = []
    edge_data = []
    i = 0
    # Get nodes that represent the watch list items
    set1 = Citation.objects.filter(
        topic_fk_id=topic_id).values_list(
        'watch_fk',
        flat=True).distinct()
    for item in set1:
        x = WatchList.objects.get(id=item).url
        data1.append(
            {'name': x, 'size': 10, 'group': 0, 'index': i, 'id': item})
        i += 1
    # Get nodes that represent the search list items
    set2 = Citation.objects.filter(
        topic_fk_id=topic_id).values_list(
        'search_fk',
        flat=True).distinct()
    max_cited = Citation.objects.filter(
        topic_fk_id=topic_id).values('search_fk').annotate(
        the_count=Count('search_fk')).aggregate(
            Max('the_count'))['the_count__max']
    if max_cited == 0:
        max_cited = 1
    for item in set2:
        item = SearchList.objects.get(id=item)
        y = float(
            Citation.objects.filter(
                search_fk_id=item.id,
                topic_fk_id=topic_id).count()) / max_cited * 83.0 + 7.0
        x = item.term
        data2.append({'name': x,
                      'size': y,
                      'group': i * 4,
                      'index': i,
                      'id': item.id})
        i += 1
    # Get data for edges in the graph
    max_edge = Citation.objects.filter(
        topic_fk_id=topic_id).values(
        'watch_fk',
        'search_fk').annotate(
            the_count=Count('search_fk')).aggregate(
                Max('the_count'))['the_count__max']
    if max_edge == 0:
        max_edge = 1
    for item1 in data1:
        for item2 in data2:
            z = Citation.objects.filter(
                search_fk_id=item2['id'],
                watch_fk_id=item1['id'],
                topic_fk_id=topic_id).count()
            if z != 0:
                x = item1['index']
                y = item2['index']
                edge_data.append({'source': x, 'target': y, 'value': z})
                print({'source': x, 'target': y, 'value': z})
        #z = float(Citation.objects.filter(watch_fk_id=item.watch_fk, search_fk_id=item.search_fk, topic_fk_id=topic_id).count())/max_edge*10.0+1

    return [data1, data2, edge_data]


@login_required(login_url='/account/login/')
def tw_networkgraph(request, topic_id):
    data = topic_context(topic_id)
    return render(request, 'recon/twitter_network_graph.html', data)


def tw_get_network_graph_data(request, topic_id):
    data = tw_get_nodes_edge_data(topic_id)
    tojson = {"nodes": data[0] + data[1], "links": data[2]}
    print(tojson)
    json_data = json.dumps(tojson)
    return HttpResponse(json_data)


def tw_get_nodes_edge_data(topic_id):
    data1 = []
    data2 = []
    edge_data = []
    i = 0
    # Get nodes that represent the watch list items
    set1 = TwitterCitation.objects.filter(
        topic_fk_id=topic_id).values_list(
        'handle_fk',
        flat=True).distinct()
    for item in set1:
        x = TwitterHandle.objects.get(id=item).handle
        data1.append(
            {'name': x, 'size': 10, 'group': 0, 'index': i, 'id': item})
        i += 1
    # Get nodes that represent the search list items
    set2 = TwitterCitation.objects.filter(
        topic_fk_id=topic_id).values_list(
        'search_fk',
        flat=True).distinct()
    max_cited = TwitterCitation.objects.filter(
        topic_fk_id=topic_id).values('search_fk').annotate(
        the_count=Count('search_fk')).aggregate(
            Max('the_count'))['the_count__max']
    if max_cited == 0:
        max_cited = 1
    for item in set2:
        item = SearchList.objects.get(id=item)
        y = float(
            TwitterCitation.objects.filter(
                search_fk_id=item.id,
                topic_fk_id=topic_id).count()) / max_cited * 83.0 + 7.0
        x = item.term
        data2.append({'name': x,
                      'size': y,
                      'group': i * 4,
                      'index': i,
                      'id': item.id})
        i += 1
    # Get data for edges in the graph
    max_edge = TwitterCitation.objects.filter(
        topic_fk_id=topic_id).values(
        'handle_fk',
        'search_fk').annotate(
            the_count=Count('search_fk')).aggregate(
                Max('the_count'))['the_count__max']
    if max_edge == 0:
        max_edge = 1
    for item1 in data1:
        for item2 in data2:
            z = TwitterCitation.objects.filter(
                search_fk_id=item2['id'],
                handle_fk_id=item1['id'],
                topic_fk_id=topic_id).count()
            if z != 0:
                x = item1['index']
                y = item2['index']
                edge_data.append({'source': x, 'target': y, 'value': z})
                print({'source': x, 'target': y, 'value': z})
    return [data1, data2, edge_data]


def barchart(request, topic_id):
    data = topic_context(topic_id)
    data['json_data'] = get_bar_chart_data(topic_id)
    return render(request, 'recon/bar_chart.html', data)


def get_bar_chart_data(topic_id):
    data = []
    set = SearchList.objects.filter(topic_fk_id=topic_id)
    for item in set:
        y = Citation.objects.filter(
            search_fk_id=item.id,
            topic_fk_id=topic_id).count()
        x = item.term
        data.append({'name': x, 'count': y})
    json_data = json.dumps(
        data)
    return json_data


def barchart_twitter(request, topic_id):
    data = topic_context(topic_id)
    #data['json_data'] = serializers.serialize('json', Citation.objects.all())

    data['json_data'] = get_bar_chart_data_twitter(topic_id)
    # return HttpResponse(data['json_data'])
    return render(request, 'recon/bar_chart.html', data)


def get_bar_chart_data_twitter(topic_id):
    data = []
    set = SearchList.objects.filter(topic_fk_id=topic_id)
    for item in set:
        y = TwitterCitation.objects.filter(
            search_fk_id=item.id,
            topic_fk_id=topic_id).count()
        x = item.term
        data.append({'name': x, 'count': y})
    json_data = json.dumps(
        data)
    return json_data


@login_required(login_url='/account/login/')
def citation(request, topic_id, template_name='recon/citation.html'):
    url_list = Citation.objects.filter(topic_fk_id=topic_id).values_list(
        'url',
        flat=True).distinct()
    citation_list = []
    for url in url_list:
        url_citation_list = []
        for item in Citation.objects.filter(url=url, topic_fk_id=topic_id):
            url_citation_list.append(item)
        citation_list.append(url_citation_list)
    data = topic_context(topic_id)
    data['citation_list'] = citation_list
    return render(request, template_name, data)


@login_required(login_url='/account/login/')
def twitter_citation(
        request, topic_id, template_name='recon/twitter_citation.html'):
    citation_list = TwitterCitation.objects.filter(topic_fk_id=topic_id)
    data = topic_context(topic_id)
    data['citation_list'] = citation_list
    return render(request, template_name, data)


def get_list_context(topic_id, list_name):
    data = topic_context(topic_id)
    data['list_name'] = list_name
    data['template'] = 'recon/list.html'
    if list_name == "watch":
        data['object_list'] = WatchList.objects.filter(topic_fk_id=topic_id)
        data['title'] = "Manage Site Watch List"
        data[
            'explain'] = "This page contains sites/webpages that you want to look for references FROM"
    elif list_name == "handle":
        data['object_list'] = TwitterHandle.objects.filter(
            topic_fk_id=topic_id)
        data['title'] = "Manage Twitter Handle List"
        data['template'] = 'recon/twitter_handle_list.html'
        data[
            'explain'] = "This page contains twitter accounts that you want to look for references FROM"
    elif list_name == "domain":
        data['object_list'] = SearchList.objects.filter(
            topic_fk_id=topic_id,
            is_url=1)
        data['title'] = "Manage Search Domain List"
        data[
            'explain'] = "This page contain web links you want to search for in any source (twitter account or website)"
    elif list_name == "keyword":
        data['object_list'] = SearchList.objects.filter(
            topic_fk_id=topic_id,
            is_url=0)
        data['title'] = "Manage Search Keyword List"
        data[
            'explain'] = "This page contain keywords you want to search for in any source (twitter account or website)"

    return data


@login_required(login_url='/account/login/')
def list(request, topic_id, list_name):
    data = get_list_context(topic_id, list_name)
    template_name = data['template']
    return render(request, template_name, data)


@login_required(login_url='/account/login/')
def get_form(request, list_name, item=None):  # get_form(list_name, item=None):
    if list_name == "watch":
        return WatchListForm(request.POST or None, instance=item)
    elif list_name == "handle":
        return TwitterHandleForm(request.POST or None, instance=item)
    elif list_name == "domain":
        form = SearchListForm(request.POST or None, instance=item)
        form.fields['term'].label = 'Url'
        form.fields['is_url'].initial = 1
        form.fields['is_url'].widget = forms.HiddenInput()
        return form
    elif list_name == "keyword":
        form = SearchListForm(request.POST or None, instance=item)
        form.fields['term'].label = 'Keyword'
        form.fields['is_url'].initial = 0
        form.fields['is_url'].widget = forms.HiddenInput()
        return form
    else:
        return None


def get_item(list_name, id):
    if list_name == "watch":
        return get_object_or_404(WatchList, id=id)
    elif list_name == "handle":
        return get_object_or_404(TwitterHandle, id=id)
    elif list_name == "domain":
        return get_object_or_404(SearchList, id=id)
    elif list_name == "keyword":
        return get_object_or_404(SearchList, id=id)
    else:
        return None


@login_required(login_url='/account/login/')
def create(request, topic_id, list_name, template_name='recon/form.html'):
    form = get_form(request, list_name)
    form.fields['topic_fk'].initial = topic_id
    form.fields['topic_fk'].widget = forms.HiddenInput()
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse(list, args=(topic_id, list_name)))
    data = topic_context(topic_id)
    data['form'] = form
    return render(request, template_name, data)


@login_required(login_url='/account/login/')
def update(request, topic_id, list_name, id, template_name='recon/form.html'):
    item = get_item(list_name, id)
    form = get_form(request, list_name, item)
    form.fields['topic_fk'].initial = topic_id
    form.fields['topic_fk'].widget = forms.HiddenInput()
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse(list, args=(topic_id, list_name)))
    data = topic_context(topic_id)
    data['form'] = form
    return render(request, template_name, data)


@login_required(login_url='/account/login/')
def delete(request, topic_id, list_name, id,
           template_name='recon/confirm_delete.html'):
    item = get_item(list_name, id)
    if request.method == 'POST':
        item.delete()
        return HttpResponseRedirect(reverse(list, args=(topic_id, list_name)))
    data = topic_context(topic_id)
    data['object'] = item
    return render(request, template_name, data)


@login_required(login_url='/account/login/')
def crawler(request, topic_id, template_name='recon/crawler.html'):
    topic = ReconTopic.objects.get(id=topic_id)
    state = topic.crawl_status
    if request.POST:
        if '_start' in request.POST:
            task_start_crawl.delay(topic_id)
            return redirect('crawler', topic_id=topic_id)
        elif '_stop' in request.POST:
            topic.crawl_status = topic.STOP
            topic.save()
            return redirect('crawler', topic_id=topic_id)
    data = topic_context(topic_id)
    data['status'] = topic.get_crawl_status
    data['state'] = state
    data['title'] = "Web Crawler"
    return render(request, template_name, data)


@login_required(login_url='/account/login/')
def twitter_crawler(
        request, topic_id, template_name='recon/twitter-crawler.html'):
    topic = ReconTopic.objects.get(id=topic_id)
    state = topic.twitter_status
    if request.POST:
        if '_start' in request.POST:
            task_start_twitter.delay(topic_id)
            return redirect('twitter_crawler', topic_id=topic_id)
        elif '_stop' in request.POST:
            topic.twitter_status = topic.STOP
            topic.save()
            return redirect('twitter_crawler', topic_id=topic_id)
    data = topic_context(topic_id)
    data['status'] = topic.get_twitter_status
    data['state'] = state
    data['title'] = "Twitter Crawler"
    return render(request, template_name, data)


def recon_frame(request, topic_id, warc_url,
                template_name='recon/recon_frame.html'):
    data = topic_context(topic_id)
    data['warc_url'] = warc_url
    return render(request, template_name, data)
