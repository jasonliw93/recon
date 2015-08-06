from django import forms
from django.core.exceptions import ValidationError
from django.forms import TextInput
from django.utils.translation import ugettext_lazy as _

from recon.models import ReconTopic, SearchList, WatchList, TwitterHandle


class ReconTopicForm(forms.ModelForm):

    class Meta:
        model = ReconTopic
        fields = ['topic', 'user']
        widgets = {
            'topic': TextInput(attrs={'size': '40', 'class': 'myfieldclass'}),
        }


class SearchListForm(forms.ModelForm):

    class Meta:
        model = SearchList
        fields = '__all__'
        widgets = {
            'term': TextInput(attrs={'size': '40', 'class': 'myfieldclass'}),
        }


class WatchListForm(forms.ModelForm):

    class Meta:
        model = WatchList
        fields = '__all__'
        widgets = {
            'url': TextInput(attrs={'size': '40', 'class': 'myfieldclass'}),
        }


class TwitterHandleForm(forms.ModelForm):

    class Meta:
        model = TwitterHandle
        fields = '__all__'
        widgets = {
            'handle': TextInput(attrs={'size': '40', 'class': 'myfieldclass'}),
        }
