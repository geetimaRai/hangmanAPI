import endpoints

from protorpc import remote, messages, message_types

from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm,\
    ScoreForms, GameForms, GameHistory, UserForms
from utils import get_by_urlsafe

EMAIL_SCOPE = endpoints.EMAIL_SCOPE

API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)

GET_USER_REQUEST = endpoints.ResourceContainer(
        user_name=messages.StringField(1),)

GET_HIGH_SCORES_REQUEST = endpoints.ResourceContainer(
        number_of_results=messages.IntegerField(1),)

MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),
        move=messages.StringField(2),)

NEW_GAME_REQUEST = endpoints.ResourceContainer(
        NewGameForm)

USER_REQUEST = endpoints.ResourceContainer(
        user_name=messages.StringField(1),
        email=messages.StringField(2))

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'


@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):
    """Hangman Game API."""

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Creates a User. Requires a unique username"""
        if request.user_name is None:
            raise endpoints.BadRequestException(
                    'You must enter a user name to create a new user!')
        elif User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with username {} already exists!'.format(request.user_name))

        if request.email is None:
            raise endpoints.BadRequestException(
                    'You must enter an email id to create a new user!')
        elif User.query(User.email == request.email).get():
            raise endpoints.ConflictException(
                    'A User with email {} already exists!'.format(request.email))

        # Create a new user with the user_name and email.
        user = User(name=request.user_name, email=request.email)
        # Add the user to the datastore with kind 'User'
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))


    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game."""
        if not request.user_name:
            raise endpoints.BadRequestException(
                    'You must enter a user name to create a new game')

        user = User.query(User.name == request.user_name).get()
        # Raise an exception if the user is not found in the datastore.
        if not user:
            raise endpoints.NotFoundException(
                    'A User with name {} does not exist!'.format(request.user_name))

        if not request.answer:
            raise endpoints.BadRequestException(
                    'You must enter an answer to create a new game!')
        try:
            game = Game.new_game(user.key, request.answer, int(request.attempts))
        except ValueError:
            raise endpoints.BadRequestException('Number of attempts must be greater than 0!')

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Hangman!')


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.game_over is not True:
                return game.to_form('You have {} attempts remaining'.
                                    format(game.attempts_remaining))
            return game.to_form('Game is over!')
        else:
            raise endpoints.NotFoundException('Game not found!')


    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        if game.game_over:
            return game.to_form('Game is over!')

        # Get the user who created the game from the datastore.
        user = User.query(User.name == game.user.get().name).get()

        # Raise an exception if the player enters multiple characters.
        if len(list(request.move)) >= 2 or len(list(request.move)) == 0:
            raise endpoints.BadRequestException(
                    'You must enter a single character!'
            )

        # Check if the user has already entered the character.
        if request.move not in game.answer:
            game.attempts_remaining -= 1
            if game.attempts_remaining == 0:
                game.end_game(False)
                user.total_played += 1
                user.win_ratio=user.won/user.total_played
                message = 'Game Over, You lose!'
            else:
                message = 'Wrong! You have {} attempts remaining!'.format(game.attempts_remaining)
        # Notify the user that they have already entered a character.
        elif request.move in game.user_answer:
            return game.to_form(
                    'You already got the letter {}'.
                        format(request.move)
            )
        else:
            # Store the move in game.user_answer.
            for i, x in enumerate(game.answer):
                if x == request.move:
                    game.user_answer[i] = request.move
            if game.user_answer == game.answer:
                user.won += 1
                user.total_played += 1
                user.win_ratio=user.won/user.total_played
                game.end_game(True)
                message = 'You win!'
            else:
                message = 'Correct! You got {}'.format(game.user_answer)

        # Add game move history.
        game.move_history.append(
                ["Guess: {}, ".format(request.move) + "Result: {}".format(message)]
        )

        # Update the user and game entities in the datastore.
        game.put()
        user.put()

        return game.to_form(message)


    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores."""
        return ScoreForms(items=[score.to_form() for score in Score.query()])


    @endpoints.method(request_message=GET_USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of the User's scores."""
        user = User.query(User.name == request.user_name).get()
        # Raise an exception if a user with the user_name does not exist.
        if not user:
            raise endpoints.NotFoundException(
                    'A user with that name does not exist!')

        # Fetch all the scores for the user from the datastore.
        scores = Score.query(Score.user == user.key)

        return ScoreForms(items=[score.to_form() for score in scores])


    @endpoints.method(request_message=message_types.VoidMessage,
                    response_message=StringMessage,
                    path='games/average_attempts',
                    name='get_average_attempts',
                    http_method='GET'
    )
    def get_average_attempts(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')


    @endpoints.method(request_message=USER_REQUEST,
                        response_message=GameForms,
                        path='user/{user_name}/games',
                        name='get_user_games',
                        http_method='GET'
    )
    def get_user_games(self, request):
        """Return all user's active games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.BadRequestException('The user {} does not exist!.'.format(request.user_name))
        games = Game.query(Game.user == user.key).filter(Game.game_over == False)
        return GameForms(items=[game.to_form('') for game in games])


    @endpoints.method(request_message=GET_GAME_REQUEST,
                    response_message=StringMessage,
                    path='/game/{urlsafe_game_key}/cancel',
                    name='cancel_game',
                    http_method='DELETE'
    )
    def cancel_game(self, request):
        """Cancel a game in progress. """
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.game_over:
                game.key.delete()
                return StringMessage(
                        message='Game with key {} deleted.'.
                            format(request.urlsafe_game_key)
                )
            # Raise an exception if the game is already over.
            else:
                raise endpoints.BadRequestException('Game is already over!')
        else:
            # Raise an exception if no such game is found in datastore.
            raise endpoints.NotFoundException('Game not found!')


    @endpoints.method(request_message=GET_HIGH_SCORES_REQUEST,
                    response_message=ScoreForms,
                    path='scores/high_scores',
                    name='get_high_scores',
                    http_method='GET'
    )
    def get_high_scores(self, request):
        """Generate a list of high scores in descending order, like a leader-board!"""
        number_of_results = 10
        if request.number_of_results is not None:
            number_of_results = int(request.number_of_results)

        # Fetch all the scores in descending order from the datastore.
        # In case of tie in attempts used by the user, the game with more attemps allowed wins.
        scores = Score.query(Score.won == True).order(Score.attempts_used, -Score.attempts).fetch(limit=number_of_results)
        if not scores:
            raise endpoints.NotFoundException(
                    'No scores found for any users!'
            )
        return ScoreForms(items=[score.to_form() for score in scores])


    @endpoints.method(request_message=message_types.VoidMessage,
                    response_message=UserForms,
                    path='users/rankings',
                    name='get_user_rankings',
                    http_method='GET'
    )
    def get_user_rankings(self, request):
        """Get users win rate ranking"""
        users = User.query(User.win_ratio > 0).order(-User.win_ratio, User.total_played)
        # Raise an exception if no users are found.
        if not users:
            raise endpoints.NotFoundException('Cannot find any users!')

        return UserForms(items=[user.to_form() for user in users])


    @endpoints.method(request_message=GET_GAME_REQUEST,
                    response_message=GameHistory,
                    path='game/{urlsafe_game_key}/history',
                    name='get_game_history',
                    http_method='GET'
    )
    def get_game_history(self, request):
        """Return user's move history for the game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return GameHistory(move=str(game.move_history))
        else:
            raise endpoints.NotFoundException('Game {} not Found!'.format(game.name))


    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_attempts_remaining = sum([game.attempts_remaining
                                            for game in games])
            average = float(total_attempts_remaining)/count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves remaining is {:.2f}'.format(average))

api = endpoints.api_server([HangmanApi])
