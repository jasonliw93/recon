from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.views.generic import TemplateView
admin.site.site_header = 'RECON - CSCC01 Team 3'

urlpatterns = patterns('',
                       url(r'', include('recon.urls')),
                       url(r'^admin/', include(admin.site.urls)),
                       url(r"^account/", include("account.urls")),
                       )

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
