from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.contrib import admin
from . import views

app_name = 'voteapp'

urlpatterns = [
    # ex: /voteapp/
    url(r'^$', views.eligible_elections, name='index'),


    # ex: /voteapp/election5/
    url(r'^election(?P<election_id>[0-9]+)/$', views.election_detail, name='election_detail'),

    # ex: /voteapp/election5/ballot1
    url(r'^election(?P<election_id>[0-9]+)/ballot(?P<ballot_id>[0-9]+)/$', views.election_detail, name='election_detail_ballot'),


     # ex: /voteapp/results
    url(r'^results/$', views.election_summary, name='election_summary'),

    url(r'^login/$', auth_views.login, {'template_name': 'voteapp/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'template_name': 'voteapp/logout.html'}, name='logout'),
    url(r'^admin/', admin.site.urls),
]
