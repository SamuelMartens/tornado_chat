from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns



urlpatterns = patterns('',
    url(r'^messages/', include('privatemessages.urls')),
    url(r'^admin/', include(admin.site.urls)),

)

urlpatterns += patterns('tornado_chat.views',
    url(r'^$','log_in_chat' ),
    url(r'^registration/$', 'reg'),


)

urlpatterns+=staticfiles_urlpatterns()
