from django.db import models

from django.utils import timezone
from django.contrib.auth.models import User



class Election(models.Model):
    name = models.CharField(max_length=200)
    vote_deadline = models.DateTimeField('vote_deadline')
    voters = models.ManyToManyField(User)

    def get_ballots(self):
        return self.ballot_set.order_by('display_order')

    def __str__(self):
        return self.name



class Ballot(models.Model):
    ballot_title = models.TextField(max_length=500)
    how_to_vote = models.TextField(max_length=500, blank=True)
    ballot_question = models.TextField(max_length=500, blank=True)
    ballot_details= models.TextField(max_length=500, blank=True)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    type = models.TextField(default="radio", max_length=200)
    required_num = models.IntegerField(default=0)
    max_num = models.IntegerField(default=1)
    allow_custom = models.BooleanField(default=False)
    display_order = models.IntegerField(default=10)


    def get_options(self):
        return self.option_set.order_by('display_order')

    def get_option_range(self):
        if self.type == 'ranked':
            return list(range(1, len(self.option_set.all())+1)).insert(0, " ")
        else:
            return range(1, len(self.option_set.all())+1)

    def __str__(self):
        return self.ballot_title


class Option(models.Model):

    ballot_item = models.ForeignKey(Ballot, on_delete=models.CASCADE)
    option_text = models.TextField(max_length=200)
    display_order = models.IntegerField(default=10)

    def __str__(self):
        return self.option_text


class WriteInOption(models.Model):
    ballot_item = models.ForeignKey(Ballot, on_delete=models.CASCADE)
    option_text = models.TextField(max_length=200)
    display_order = models.IntegerField(default=100)
    voters = models.ManyToManyField(User)

    def __str__(self):
        return self.option_text

class Votes(models.Model):
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE,default=None, null=True, blank=True)
    ballot = models.ForeignKey(Ballot, on_delete=models.CASCADE)
    custom_option = models.ForeignKey(WriteInOption, on_delete=models.CASCADE,default=None,  null=True, blank=True)
    time_stamp = models.DateTimeField()
    value = models.CharField(max_length=20, default=None,  null=True, blank=True)


    def __str__(self):
        output = "Voter: {}, Ballot ID: {}, Option ID: {}, Custom Option ID: {}, Time: {}, Value: {}".format(self.voter, self.ballot, self.option, self.custom_option, self.time_stamp, self.value)
        return output


class LogHistory(models.Model):
    time_stamp = models.DateTimeField()
    voter=models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=200)

    def __str__(self):
        ouput = "{}: User {}, {}".format(self.time_stamp, self.voter.username, self.action)
        return ouput



