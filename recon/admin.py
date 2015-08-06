from django.contrib import admin

from recon.models import ReconTopic, SearchList, Citation, WatchList, TwitterHandle, TwitterCitation
admin.site.register(ReconTopic)
admin.site.register(SearchList)

admin.site.register(WatchList)
admin.site.register(Citation)

admin.site.register(TwitterHandle)
admin.site.register(TwitterCitation)

# Register your models here.
