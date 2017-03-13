from django.shortcuts import render

# Create your views here.
from django.http import Http404
from django.db.models import Max

from .models import Ballot, Election, Option, WriteInOption, Votes
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from voteapp.forms import MultiVoteForm, WriteInForm
from django.shortcuts import redirect
import datetime



def is_eligible(request, election_id):
    """ Checks that the current user is registered for election with id passed in.
        If eligible returns true,  otherwise return 404 indicating, not registered
    """
    if request.user.election_set.filter(id=election_id): #make sure user is elegible to vote
        return True
    else:
        raise Http404("You are not registered for this election.")


@login_required(login_url='/voteapp/login/')# redirects to login page if not logged in
def eligible_elections(request):
    """Creates a list of the elections that the logged in user is registered for."""

    template_name = 'voteapp/index.html'
    context_object_name = 'election_list' #variable to accesse in template
    current_user = request.user
    elections = current_user.election_set.all()
    return render(request, template_name, {context_object_name: elections})



def get_ballot_options(request, ballot):
    """ This function returns a dictionary used for creating dynamic forms, it contains:
        {'type': 'ranked' or 'checkbox' or 'radio',
        'allow_custom': True or False,
        'max_choices': int,
        'option_list':
                [{'type':'normal' or 'write_in',
                  'obj': option_obj or write_in_option_obj (from model)}, ...]
    """

    dynamic_form = {'type': ballot.type, 'allow_custom':ballot.allow_custom, 'max_choices':ballot.max_num}
    dynamic_form['option_list'] = []
    for opt in ballot.option_set.all():

        dynamic_form['option_list'].append({'type':'normal', 'obj':opt})
    if ballot.allow_custom:
        dynamic_form['allow_custom'] = True
        for write_in in request.user.writeinoption_set.filter(ballot_item=ballot.id):

            dynamic_form['option_list'].append({'type':'write_in', 'obj':write_in})

    return dynamic_form



@login_required(login_url='/voteapp/login/')
def add_write_in(request, election_id, ballot_id, write_in):
    """ add_write_in creates a write in option if it doesn't already exist and saves it to the db.

    Inputs:
        request:        object that contains the user needed to link to write in object
        election_id:    id of applicable election object
        ballot_id:      id of applicable ballot (item to vote on)
        write_in:       text containing option written in

    Output: Data stored in DB
    """
    if is_eligible(request, election_id): #authenticate user or return error

        max_display_order = WriteInOption.objects.all().aggregate(Max('display_order'))['display_order__max']
        wio = WriteInOption.objects.filter(option_text=write_in).first()
        if not wio:
            wio = WriteInOption()
            wio.ballot_item = Ballot.objects.get(id=ballot_id)
            wio.option_text = write_in
            wio.display_order =  max_display_order + 10
            wio.save()
        wio.voters.add(request.user)


@login_required(login_url='/voteapp/login/')
def save_vote(request, ballot_id, clean_data):
    """ Deletes any previous votes on this ballot(voting item) and then addes vote to DB

    Inputs:
        request:    object that contains the user needed to link to vote
        ballot_id:  if of  ballot object to be linked to vote
        clean_data: dictionary of dynamic data based on type of form filled out:
                    if ballot type is ranked:
                        key: choice_normal-<id> or write_in-<id> ie: write_in-1
                        value: Rank Chosen (int) 1 through number of options
                    if ballot type is radio:
                        key: 'choice'
                        value: "normal-<id>" or "write_in-<id>" ie: normal-1
                    if ballot type is checkbox:
                        key: choice_normal-<id> or write_in-<id> ie: write_in-1
                        value: True
        The new vote object created will be added to the db, if it is a write in the option will be set to null,
        if it is a normal option then the custom_option will be set to null
    """
    #if voter has already voted update vote

    #remove any previous votes from this voter
    Votes.objects.filter(ballot=ballot_id).filter(voter=request.user.id).delete()
    ballot = Ballot.objects.get(id=ballot_id)

    if ballot.type == "ranked":
        for option, value in clean_data.items():
            if value:
                #add vote for each ranked item
                vote = Votes()
                vote.voter = request.user
                vote.time_stamp = datetime.datetime.now()
                vote.value = value
                vote.ballot = ballot
                if "choice_normal" in option:
                    id = option.split("-")[1]
                    vote.custom_option = None
                    vote.option = Option.objects.get(id=id)
                else:
                    id = option.split("-")[1]
                    vote.option = None
                    vote.custom_option = WriteInOption.objects.get(id=id)
                vote.save()
    elif ballot.type == 'radio':
        for option, value in clean_data.items():
            if value:
                opt_type, id = value.split("-")
                #value is the id of the option selected

                vote = Votes()
                vote.voter = request.user
                vote.time_stamp = datetime.datetime.now()
                vote.value = None
                vote.ballot = ballot
                if opt_type == "normal":
                    vote.custom_option = None
                    vote.option = Option.objects.get(id=id)
                elif opt_type == "write_in":
                    vote.option = None
                    vote.custom_option = WriteInOption.objects.get(id=id)
                vote.save()

    elif ballot.type == 'checkbox':
        for option, value in clean_data.items():
            print("Option: {}, Value: {}".format(option, value))
            if value:
                opt_type, id = option.split("-")
                #value is the id of the option selected

                vote = Votes()
                vote.voter = request.user
                vote.time_stamp = datetime.datetime.now()
                vote.value = value
                vote.ballot = ballot
                if opt_type == "choice_normal":
                    vote.custom_option = None
                    vote.option = Option.objects.get(id=id)
                elif opt_type == "choice_write_in":
                    vote.option = None
                    vote.custom_option = WriteInOption.objects.get(id=id)
                vote.save()

def get_next_ballot(election, ballot_id):
    """ Determines what the next ballot for the current election is and returns it or None if this is the last one
    Inputs:
        election:   object containing model for current election
        ballot_id:  int represending id of ballot object in model db

    Output:
        next_ballot: object containing next ballot to display or None
    """

    ballots = election.ballot_set.all().order_by('display_order')
    get_next = False
    next_ballot = None

    for ballot in ballots:
        if get_next:
            next_ballot = ballot
            break
        if str(ballot.id) == str(ballot_id):
            get_next = True
            print("Setting get_next to true")


    return next_ballot


@login_required(login_url='/voteapp/login/')
def election_detail(request, election_id, ballot_id=None):
    """
    The main control of app is in this function. It gets the election and ballot objects from db based on the
    url (election1/ballot3/) the number following it is the id param passed in (this is done in urls.py).  If ballot_id
    is None it shows a list of the ballots in the election and a start button.

    If a write in option was added it adds it to the database and then reloads this function to display with new option.

    All the relevant normal options and write in options are retreived and then passed into the MultiVoteForm to create dynamic
    forms based on the type of ballot it is.  When the form is submitted this same function is called and loaded with the
    same form elements and the data from request.POST (the chosen values) and after being cleaned and validated are added
    as a vote to the db.

    If its a valid posting then the next ballot is retrieved and this form is called again with the new ballot ID.  If there
    is not another ballot it is redirected to the election_summary page showing the results of the election.

    :param request:         contains user information from django
    :param election_id:     id of current election model in db
    :param ballot_id:       id of current ballot model in db
    :return:                HTTP object with dictionary and template files for displaying next object
    """
    form = None
    cur_ballot = None
    next_ballot = None
    write_in_form = None
    added_option = False

    if is_eligible(request, election_id): #authenticate user
        election = get_object_or_404(Election, pk=election_id)

        if ballot_id:
            cur_ballot = get_object_or_404(Ballot, pk=ballot_id)


            if cur_ballot.allow_custom:
                write_in_form = WriteInForm(request.POST or None)

                write_in_form.is_valid()
                if 'Add' in request.POST: #Add button was pushed
                    added_option = True
                    if write_in_form.cleaned_data['write_in_form']:
                        add_write_in(request,election_id,ballot_id, write_in_form.cleaned_data['write_in_form'])

                write_in_form = WriteInForm() #clear out field

            ballot_options = get_ballot_options(request, cur_ballot)
            form = MultiVoteForm(request.POST or None, extra=ballot_options, label_suffix="")
            if not added_option and request.method == "POST" and form.is_valid():
                save_vote(request, ballot_id, form.cleaned_data)
                next_ballot = get_next_ballot(election, ballot_id)
                if next_ballot:
                    return HttpResponseRedirect(reverse('voteapp:election_detail_ballot', args=(election_id,str(next_ballot.id))))
                else:
                    return HttpResponseRedirect(reverse('voteapp:election_summary'))


        #get next ballot
        next_ballot = get_next_ballot(election, ballot_id)

        return render(request, 'voteapp/election_detail.html', {'form':form, 'write_in_form':write_in_form, 'election': election, 'ballot': cur_ballot, 'next_ballot':next_ballot, 'show_submit':True})


def election_summary(request):
    """
    This function counts up all the votes and adds them to a dictionary to be passed into the html template to display
    the results of all the elections.

    If the ballot type is ranked it will be proccessed differently in order to determin based on Instant Runoff and sent in
    a variable to the template to be displayed.

    :param request: containse user information
    :return: HTTP object with template file and data to populate it
    """
    tally= {}


    for election in Election.objects.all():

        elec_ballots = election.ballot_set.all().order_by('display_order')
        ballots = {}
        for ballot in elec_ballots:
            votes = ballot.votes_set.all()
            if ballot.type == 'ranked':
                pass
            else:

                ballot_output = {}
                for vote in votes:
                    if vote.custom_option:
                        if 'custom_'+str(vote.custom_option.id) not in ballot_output:
                            ballot_output['custom_'+str(vote.custom_option.id)] = {'count':1, 'name':vote.custom_option.option_text}
                        else:
                            ballot_output['custom_'+str(vote.custom_option.id)]['count'] += 1

                    else:
                        if vote.option.id not in ballot_output:
                            ballot_output[vote.option.id] = {'count':1, 'name':vote.option.option_text}
                        else:
                            ballot_output[vote.option.id]['count'] += 1

                ballots[ballot.id] = {'ballot':ballot, 'ballot_tally':ballot_output }
        tally[election.id] = {"election":election, 'ballots':ballots}
    return render(request, 'voteapp/election_summary.html', {'tally':tally})



def logout_view(request):
    logout(request)
