from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.contrib import admin
from . import views
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm

app_name = 'voteapp'

urlpatterns = [
    # ex: /voteapp/
    url(r'^$', views.home, name='index'),

    # ex: /voteapp/elections
    url(r'^elections/$', views.eligible_elections, name='elections'),

    # ex: /voteapp/election5/
    url(r'^election(?P<election_id>[0-9]+)/$', views.election_detail, name='election_detail'),

    # ex: /voteapp/election5/ballot1
    url(r'^election(?P<election_id>[0-9]+)/ballot(?P<ballot_id>[0-9]+)/$', views.election_detail, name='election_detail_ballot'),

     # ex: /voteapp/results
    url(r'^results/$', views.election_summary, name='election_summary'),

    # ex: /voteapp/view_logs
    # ex: /voteapp/results
    url(r'^view_logs/$', views.view_logs, name='view_logs'),

    # ex: /voteapp/register
    url(r'^register/$', CreateView.as_view(template_name='voteapp/register.html', form_class=UserCreationForm, success_url='/'), name='register'),

    url(r'^login/$', auth_views.login, {'template_name': 'voteapp/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'template_name': 'voteapp/logout.html'}, name='logout'),
    url(r'^admin/', admin.site.urls),
]
