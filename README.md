# VoteApp
VoteApp is a simple voting application that allows users to vote online. It is built on django which contains a great back end for creating elections, ballots, and choices.

###Getting Started
Your election details can be entered and configured by going to the folder /admin/ and logging in to djangos back end.

####Elections 
First you need to create an election.  Users that are registered may then be assigned to an election through the Django backend by an admin.  Automation of the registration could be implemented fairly easily but is not part of the system currently.  
Elections need a name, an ending date, and the users selected that are eligible to vote in it.

####Ballot
Once an election has been created one or more ballots should be created. A ballot needs to have a Title. 
The fields How to vote, Ballot question, and Ballot details are optional and can be used to describe how to vote. The ballot must be tied to an election and can be chosen in the drop down next to Election:
There are currently implemented three types, radio, checkbox, and ranked.  One of those three words must be placed in this box to tell the program how to display your options. 
Required num is not implemented
The program checks for Max Num on checkbox and ranked ballots and will throw an error if the number here is exceeded.
Allow custom will allow your voters to write in the name of their own candidate or choice. (Only visible to them) Must be spelled the same amongst voters in order to tabulate correctly.
Display order tells the software the order to show the ballots in (smallest numbers first).

####Options
The ballot that the option applies to must be selected from the drop down box. 
The Option text feild should have a description that represents the option, a name or a choice. 
The display order tells the program what order to show the options in (smallest numbers first).

Once the Election, Ballots, and Options are filled out, you can go vote!

###Voting
Go to /voteapp/ to see the home page.  It will give you the option to Register or Login. Registering will add you as a user to the system but you  will still need an admin to give you access to an election to be able to vote in it.
Without logging in you still have access to the Results of all the elections on the system by clicking on Results on the menu bar.

After logging in you will be able to see the Elections you are eligible for and vote on the ballots within it.
If your user account has staff priviledges you will be able to see the View Logs menu item that shows all the history for each user.

I hope you enjoy the program!

