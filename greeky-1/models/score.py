"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    attempts_used = ndb.IntegerProperty(required=True)
    attempts = ndb.IntegerProperty(required=True)

    def to_form(self):
        """Returns a ScoreForm representation of the Score.
        Args:
            None.
        Returns:
            ScoreForm: Form representation of the score.
        """
        return ScoreForm(user_name=self.user.get().name,
                         date=str(self.date),
                         won=self.won,
                         attempts_used=self.attempts_used,
                         attempts=self.attempts)


class GetHighScoresForm(messages.Message):
    """Used to return a list of top scoring users"""
    number_of_results = messages.IntegerField(1, required=False, default=6)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    attempts_used = messages.IntegerField(4, required=True)
    attempts = messages.IntegerField(5, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)

