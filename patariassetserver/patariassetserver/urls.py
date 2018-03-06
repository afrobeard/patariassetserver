"""patariassetserver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from assetserver.views import ingest_image, get_derivative, get_asset_info, upload_to_azure

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^assets/ingest/', ingest_image),
    url(r'^assets/(?P<guid>[\w\-]+)/$', get_derivative),
    url(r'^assets/(?P<guid>[\w\-]+)/(?P<size>[\w\-]+)/$', get_derivative),
    url(r'^assets/(?P<guid>[\w\-]+).json$', get_asset_info),
    url(r'^upload/azure', upload_to_azure)
]
