#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

import webapp2
from google.appengine.api import mail, app_identity
from api import HangmanApi

from models import User, Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email who has
        games in progress. Email body includes a count of active
        games and their urlsafe keys
        Called every everyday at 9:00 AM"""
        games = Game.query(Game.game_over == False)
        for game in games:
            user = User.query(User.key == game.user).get()
            subject = 'This is a reminder!'
            body = 'Hello {}, This is a reminder to play your game in progress!'.format(user.name)
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