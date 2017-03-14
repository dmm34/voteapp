from django.utils import timezone

from django.utils import timezone
from django.test import TestCase, RequestFactory

from .views import *
from .models import *

from django.urls import reverse
import random


def create_voter(name, email, password):
    """
    Creates a voter
    """
    user = User.objects.create_user(
            username='jacob', email='jacob@…', password='top_secret')

    return User


class GetTallyOptionsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.election = Election.objects.create(name="Coolest", vote_deadline=(timezone.now() + timezone.timedelta(days=10)) )
        self.election.save()
        self.ballot = Ballot.objects.create(
            ballot_title = "Which is the coolest?",
            how_to_vote = "RANKED CHOICE (INSTANT RUNNOFF)",
            ballot_question = "",
            ballot_details= "Rank in order of choice",
            election = self.election,
            type = "ranked",
            required_num = 0,
            max_num = 9999,
            allow_custom = True,
            display_order = 10)
        self.ballot.save()

        disp_order = 10
        self.options = ["LL Cool J", "Neptune", "Ice", "Snow", "Justin Timberlake"]
        for opt_text in self.options:
            option = Option.objects.create(
                ballot_item = self.ballot,
                option_text = opt_text,
                display_order = disp_order,
            )
            disp_order += 10
            option.save()

        self.user_list = []
        num_users = 100
        for i in range(num_users):

            name = 'test_user_'+str(i)
            user = User.objects.create_user(username=name, first_name=name, password='secret')
            self.user_list.append(user)
            self.election.voters.add(user) #add all users to election

    def create_votes(self, method):

        #form data is dif based on type of ballot:
        #if ballot type is ranked:
        #   key: choice_normal-<id> or write_in-<id> ie: write_in-1
        #   value: Rank Chosen (int) 1 through number of options

        if method == 'same':
            #all the same vote
            options = Option.objects.all()
            form_data = {}
            count = 1
            for option in options:
                form_data['choice_normal-{}'.format(option.id)] = count
                count +=1

            for user in self.user_list: #everyone has the same vote rank
                save_vote(user, self.ballot.id, form_data)
                #votes = Votes.objects.all()
                #for vote in votes:
                #    print(vote)
                #print("***************************")

        if method == 'random':
            #all random votes

            options = Option.objects.all()

            opt_vals = list(range(1,len(options)+1))

            for user in self.user_list: #everyone has the same vote rank
                form_data = {}
                i=0
                random.shuffle(opt_vals)
                for option in options:
                    form_data['choice_normal-{}'.format(option.id)] = opt_vals[i]
                    i+=1
                save_vote(user, self.ballot.id, form_data)

        if method == 'tie':
            #all random votes

            options = Option.objects.all()

            opt_vals = list(range(1,len(options)+1))

            for user in self.user_list: #everyone has the same vote rank
                if user.id < 5:
                    #first 4 vote for 3 with backup up of 1
                    form_data = {}
                    form_data['choice_normal-3'] = 1
                    form_data['choice_normal-1'] = 2
                elif user.id % 2 == 0:
                    #half of remaining vote for 1 and then 3
                    form_data = {}
                    form_data['choice_normal-1'] = 1
                    form_data['choice_normal-2'] = 2
                else:
                    #half of remaining vote for 2 and then 3
                    form_data = {}
                    form_data['choice_normal-1'] = 1
                    form_data['choice_normal-2'] = 2
                save_vote(user, self.ballot.id, form_data)


    def test_tally_ranked_with_tied_low_rank(self):
        """
        Should return a tally object with
        """

        self.create_votes('same')
        votes = Votes.objects.all()

        tally = get_tally_object()

        self.assertIs(tally[1]['ballots'][1]['ballot_tally'], len(self.user_list))


    def test_tally_ranked_with_tie(self):
        # run a test with half option1 and half option2 and 1 other with option

        self.create_votes('tie')
        #pdb.set_trace()

        tally = get_tally_object()

        print(tally)
        self.assertIs()
