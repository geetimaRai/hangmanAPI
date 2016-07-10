from datetime import date

from google.appengine.ext import ndb
from models.score import Score
from protorpc import messages


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
        """Creates and returns a new game.
        Args:
           user: The user who created the game.
           answer: The answer for the game.
           attempts: The maximum number of attempts allowed.
        Returns:
           Game: A new Game object with the initialized values.
        """
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
        game.attempts_remaining = attempts_remaining
        game.move_history = []
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game.
        Args:
           message: The message to be displayed to the user.
        Returns:
           GameForm: Form representation of the game.
        """
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
        the player lost. Creates a Score object and stores it in the datastore.
        Args:
           won: Indicates whether the player wins or loses.
        """
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(
                user=self.user, date=date.today(), won=won,
                attempts_used=self.attempts - self.attempts_remaining,
                attempts=self.attempts)
        score.put()


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


class GameHistory(messages.Message):
    """Game history"""
    move = messages.StringField(1, required=True)
