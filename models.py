"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email =ndb.StringProperty()
    won = ndb.IntegerProperty(default=0)
    total_played = ndb.IntegerProperty(default=0)
    win_ratio = ndb.FloatProperty(default=0.0)

    def to_form(self):
        """Returns a UserForm representation of the User"""
        form = UserForm()
        form.name = self.name
        form.email = self.email
        form.won = self.won
        form.total_played = self.total_played
        return form


class Game(ndb.Model):
    """Game object"""
    answer = ndb.PickleProperty(required=True)
    user_answer = ndb.PickleProperty()
    attempts = ndb.IntegerProperty(required=True, default=6)
    attempts_remaining = ndb.IntegerProperty(required=False)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    move_history = ndb.PickleProperty()

    @classmethod
    def new_game(cls, user, answer, attempts):
        """Creates and returns a new game"""
        if attempts is None:
            attempts = 6
        elif attempts <= 0:
            raise ValueError('Attempts has to be over 0.')
        attempts_remaining = attempts
        game = Game(user=user,
                    attempts=attempts,
                    game_over=False)
        game.answer = list(answer)
        game.user_answer = [''] * len(game.answer)
        game.attempts_remaining=attempts_remaining
        game.move_history = []
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.attempts = self.attempts
        form.attempts_remaining = self.attempts_remaining
        form.game_over = self.game_over
        form.message = message
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(
                user=self.user, date=date.today(), won=won,
                attempts_used=self.attempts-self.attempts_remaining,
                attempts=self.attempts,
                answer=self.answer)
        score.put()


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    attempts_used = ndb.IntegerProperty(required=True)
    attempts = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name,
                         date=str(self.date),
                         won=self.won,
                         attempts_used=self.attempts_used,
                         attempts=self.attempts)


class UserForm(messages.Message):
    """User Form"""
    name = messages.StringField(1, required=True)
    email = messages.StringField(2)
    won = messages.IntegerField(3, required=True)
    total_played = messages.IntegerField(4, required=True)


class UserForms(messages.Message):
    """Container for multiple User Forms"""
    items = messages.MessageField(UserForm, 1, repeated=True)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    attempts = messages.IntegerField(2, required=True)
    attempts_remaining = messages.IntegerField(3, required=True)
    game_over = messages.BooleanField(4, required=True)
    message = messages.StringField(5, required=True)
    user_name = messages.StringField(6, required=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    answer = messages.StringField(2, required=True)
    attempts = messages.IntegerField(3, default=6)


class GameForms(messages.Message):
    """Multiple GameForm container"""
    items = messages.MessageField(GameForm, 1, repeated=True)


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


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)


class GameHistory(messages.Message):
    """Game history"""
    move = messages.StringField(1, required=True)

