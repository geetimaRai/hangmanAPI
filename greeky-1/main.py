#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import webapp2
from google.appengine.api import (
    mail,
    app_identity,
)

from api import HangmanApi
from models.user import User
from models.game import Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email who has
        games in progress. Email body includes a count of active
        games and their urlsafe keys
        Called every everyday at 9:00 AM"""
        users = User.query()
        for user in users:
            # Get all the unfinished user games.
            games = Game.query(Game.user == user.key, Game.game_over == False)
            if games.count() > 0:
                subject = 'This is a reminder!'
                body = 'Hello {0}, This is a reminder that you have Hangman game in progress! ' \
                       'Let\'s play and have some fun!'\
                    .format(user.name)
                # This will send emails to the users who have pending active games.
                mail.send_mail('noreply@{}.appspotmail.com'.
                               format(app_identity.get_application_id()),
                               user.email,
                               subject,
                               body)


class UpdateAverageMovesRemaining(webapp2.RequestHandler):
    def post(self):
        """Update average moves remaining in memcache."""
        HangmanApi._cache_average_attempts()
        self.response.set_status(204)

app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_average_attempts', UpdateAverageMovesRemaining),
], debug=True)
