from django.shortcuts import render

# Create your views here.
from django.http import Http404
from django.db.models import Max

from .models import *
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from voteapp.forms import MultiVoteForm, WriteInForm
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views

from django.utils import timezone
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
import pdb
from django.contrib.auth.signals import user_logged_in, user_logged_out

def home(request):

    """
    Gets the template for the homepage and displays it

    :param request: HTTP object containing django state
    :return: HTTP filled template
    """
    log(request.user, "Load Home Page")
    return render(request, 'voteapp/index.html', {})




def is_eligible(request, election_id):
    """
        Checks that the current user is registered for election with id passed in.
        If eligible returns true,  otherwise return 404 indicating, not registered

    :param request: : HTTP object containing django state
    :param election_id: ID of election model object to test users eligigibility
    :return: True if eligible or an HTTP error

    """

    if request.user.election_set.filter(id=election_id): #make sure user is elegible to vote
        return True
    else:
        raise Http404("You are not registered for this election.")


@login_required(login_url='/voteapp/login/')# redirects to login page if not logged in
def eligible_elections(request):
    """
        Creates a list of the elections that the logged in user is registered for.

    :param request: HTTP object containing django state and current user
    :return: HTTP filled template showing eligible elections
    """

    template_name = 'voteapp/elections.html'
    context_object_name = 'election_list' #variable to accesse in template
    current_user = request.user
    elections = current_user.election_set.all()
    return render(request, template_name, {context_object_name: elections})



def get_ballot_options(request, ballot):
    """
        This function returns a dictionary used for creating dynamic forms, it contains:


    :param request: HTTP object containing django state and current user
    :param ballot: ballot object (from models), it is connected to one election and has one ballot question
    :return: dictionary used to create dynamic forms:
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
    """
        Creates a write in option if it doesn't already exist and saves it to the db.

    :param request: HTTP object containing django state and current user to link to write in object
    :param election_id: id of current election model
    :param ballot_id: id of current ballot model
    :param write_in: text of write in option to be added
    :return: None (new write in obejct is written to db)

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
        log(request.user, "Added Write in option: {}".format(str(wio)))


def save_vote(user, ballot_id, clean_data):
    """
        Deletes any previous votes on this ballot(voting item) and then addes vote to DB

    :param user: model of Current user needed to link to vote
    :param ballot_id: id of current ballot model
    :param clean_data: dictionary of dynamic data based on type of form filled out:
                    if ballot type is ranked:
                        key: choice_normal-<id> or write_in-<id> ie: write_in-1
                        value: Rank Chosen (int) 1 through number of options
                    if ballot type is radio:
                        key: 'choice'
                        value: "normal-<id>" or "write_in-<id>" ie: normal-1
                    if ballot type is checkbox:
                        key: choice_normal-<id> or write_in-<id> ie: write_in-1
                        value: True
    :return: None -
        The new vote object created will be added to the db, if it is a write in the option will be set to null,
        if it is a normal option then the custom_option will be set to null
    """

    #if voter has already voted update vote

    #remove any previous votes from this voter
    Votes.objects.filter(ballot=ballot_id).filter(voter=user.id).delete()
    ballot = Ballot.objects.get(id=ballot_id)

    if ballot.type == "ranked":
        for option, value in clean_data.items():
            if value:
                #add vote for each ranked item
                vote = Votes()
                vote.voter = user
                vote.time_stamp = timezone.now()
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
                log(user, "Entered Vote: {}".format(str(vote)))
    elif ballot.type == 'radio':
        for option, value in clean_data.items():
            if value:
                opt_type, id = value.split("-")
                #value is the id of the option selected

                vote = Votes()
                vote.voter = user
                vote.time_stamp = timezone.now()
                vote.value = None
                vote.ballot = ballot
                if opt_type == "normal":
                    vote.custom_option = None
                    vote.option = Option.objects.get(id=id)
                elif opt_type == "write_in":
                    vote.option = None
                    vote.custom_option = WriteInOption.objects.get(id=id)
                vote.save()
                log(user, "Entered Vote: {}".format(str(vote)))
    elif ballot.type == 'checkbox':
        for option, value in clean_data.items():
            print("Option: {}, Value: {}".format(option, value))
            if value:
                opt_type, id = option.split("-")
                #value is the id of the option selected

                vote = Votes()
                vote.voter = user
                vote.time_stamp = timezone.now()
                vote.value = value
                vote.ballot = ballot
                if opt_type == "choice_normal":
                    vote.custom_option = None
                    vote.option = Option.objects.get(id=id)
                elif opt_type == "choice_write_in":
                    vote.option = None
                    vote.custom_option = WriteInOption.objects.get(id=id)
                vote.save()
                log(user, "Entered Vote: {}".format(str(vote)))
def get_next_ballot(election, ballot_id):
    """
        Gets the ballot with the next largest display  order if there is one or returns None

    :param election: election object from models containing current election
    :param ballot_id: id of ballot from models containing current ballot
    :return: next_ballot: the next largest display_order ballot in this election, or None
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

    :param request:         HTTP object containing django state and current user
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
                save_vote(request.user, ballot_id, form.cleaned_data)
                next_ballot = get_next_ballot(election, ballot_id)
                if next_ballot:
                    return HttpResponseRedirect(reverse('voteapp:election_detail_ballot', args=(election_id,str(next_ballot.id))))
                else:
                    return HttpResponseRedirect(reverse('voteapp:election_summary'))


        #get next ballot
        next_ballot = get_next_ballot(election, ballot_id)

        return render(request, 'voteapp/election_detail.html', {'form':form, 'write_in_form':write_in_form, 'election': election, 'ballot': cur_ballot, 'next_ballot':next_ballot, 'show_submit':True})


def get_tally_object():
    """
        Creates a dictionary containing the tabulations of all the elections.
        For a ballot of type ranked:
            The following step is taken as many times needed to get an option with the majority of all votes or only two options.
                The option with the fewest top rank from each voter is added to an ignore list, such that if it is the top rank the next highest ranking option is the one submitted

                When all options tie, they are all considered winners and sent to output
                When there is a tie amongst the lower ranking options they are all ignored

        For other ballot types:
            each vote for each ballot is added up and placed into the tally object
    :return:
    """
    tally= {}


    for election in Election.objects.all():

        elec_ballots = election.ballot_set.all().order_by('display_order')
        ballots = {}
        for ballot in elec_ballots:
            votes = ballot.votes_set.all()
            if ballot.type == 'ranked':
                tie = False

                voter_list = {} #build voter_list
                for vote in votes:
                    if vote.voter.id not in voter_list:
                        voter_list[vote.voter.id] = {}
                    if vote.custom_option:
                        voter_list[vote.voter.id][vote.value] = 'custom_'+str(vote.custom_option.id)
                    else:
                        voter_list[vote.voter.id][vote.value] = 'option_'+str(vote.option.id)

                #voter list is made, now count results
                num_voters = len(voter_list)
                ignore_list = []

                while True:

                    result_count = {}
                    for v_id, v_data in voter_list.items():
                        #go through each ranked option and add the lowest rank option that isn't in ignore list
                        ranks = []
                        for rank, rank_info in v_data.items():
                            if rank_info not in ignore_list:
                                ranks.append(rank)
                        if len(ranks):
                            opt_vote = v_data[min(ranks)]
                            if opt_vote not in result_count:
                                result_count[opt_vote] = 1
                            else:
                                result_count[opt_vote] += 1

                    cur_winner_count = 0
                    cur_winner = None
                    cur_loser_count = num_voters


                    for option, count in result_count.items():
                        if count > cur_winner_count:
                            cur_winner_count = count
                            cur_winner = option

                        if count < cur_loser_count:
                            cur_loser_count = count

                    if cur_winner_count == num_voters:
                        #unanimous
                        break

                    if cur_winner_count == cur_loser_count:#this could happen with a multi-way tie
                        tie = True
                        print("There was a tie in rank tabulation")
                        break

                    has_more_than_half = float(cur_winner_count)/float(num_voters) > .5

                    #end loop when only two options remain or option has more than half of votes
                    if len(result_count) <= 2 or has_more_than_half:
                        break # a winner has been found

                    #add all results with count <= cur_loser_count to ignore list, this should take care of any loser ties
                    #pdb.set_trace()
                    for option, count in result_count.items():
                        if count <= cur_loser_count:
                            ignore_list.append(option)


                #when code reaches here there should be either a tie or a cur_winner
                if tie:
                    # dispaly all winners
                    ballot_output = {}
                    for option, count in result_count.items():
                        type, id = option.split("_")
                        name = "Error"
                        if type == "custom":
                            name = WriteInOption.objects.get(id=id).option_text
                        elif type == "option":
                            name = Option.objects.get(id=id).option_text
                        ballot_output[option] = {'count':result_count[option], 'name':name}

                    ballots[ballot.id] = {'ballot':ballot, 'ballot_tally':ballot_output,'ranked':"Tie" }
                else:
                    type, id = cur_winner.split("_")
                    name = "Error"
                    if type == "custom":
                        name = WriteInOption.objects.get(id=id).option_text
                    elif type == "option":
                        name = Option.objects.get(id=id).option_text
                    ballots[ballot.id] = {'ballot':ballot, 'ballot_tally':cur_winner_count, 'ranked':"Win", 'name': name }

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
        tally[election.id] = {"election":election, 'ballots':ballots, 'result_count':result_count}
    return tally

def election_summary(request):
    """
    This function counts up all the votes and adds them to a dictionary to be passed into the html template to display
    the results of all the elections.

    If the ballot type is ranked it will be proccessed differently in order to determin based on Instant Runoff and sent in
    a variable to the template to be displayed.

    :param request: HTTP object containing django state and current user
    :return: HTTP object with template file populated with dict containing tally (all tally information)
    """
    log(request.user, "Viewed election results")
    return render(request, 'voteapp/election_summary.html', {'tally':get_tally_object()})



def logout_view(request):
    """
        Logs out current user

    :param request: HTTP object containing django state and current user
    :return: None
    """
    log(request.user, "Logout")
    auth_views.logout(request)


def log(user, action):
    """

    :param user: user model object for current user
    :param action: text describing action taken
    :return: None - logged to db
    """
    if user.is_authenticated:
        lh = LogHistory.objects.create(time_stamp=timezone.now(), voter=user, action=action)
        lh.save()


def view_logs(request):
    """
        View system logs

    :param request: HTTP object containing django state and current user
    :return: None
    """
    if request.user.is_staff:
        all_logs = LogHistory.objects.all().order_by('-time_stamp')[0:60]
        log(request.user, "Viewed logs")
        return render(request, 'voteapp/view_logs.html', {'logs':all_logs})

    raise Http404("Only staff is allowed to see the logs.")



def send_log_data_on(sender, user, request, **kwargs):
    log(user, "Log on")

def send_log_data_out(sender, user, request, **kwargs):
    log(user, "Log out")

user_logged_in.connect(send_log_data_on)
user_logged_out.connect(send_log_data_out)
