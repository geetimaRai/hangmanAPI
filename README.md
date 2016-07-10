#Hangman Game API

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
2.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
3.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.


##Game Description:
Hangman is a simple guessing game in which the player needs to fill in the blanks for letters
in the word to be guessed. The word to guess is represented by a row of dashes,
representing each letter of the word. Each game begins with a word and a maximum
number of 'attempts'. 'Guess Letters' are sent to the `make_move` endpoint which
will reply with either: 'wrong', 'you win', or 'game over' (if the maximum
number of attempts is reached).
If the guessing player suggests a letter which occurs in the word, the `make_move` endpoint
writes it in all its correct positions. If the suggested letter or number does not
occur in the word, the endpoint displays the number of attempts the user has remaining.
Each game can be retrieved or played by using the path parameter `urlsafe_game_key`.

##Score Keeping:
Each player has a win_ratio field, which is the ratio of the total number of games the
user has won so far to the total number of games the user has played. A player with a
higher win_ratio is ranked above a player with a lower win_ratio. In case 2 players have
the same win_ratio, the player with fewer games played wins.


##How To Play:
1. Visit the API Explorer - by default localhost:8080/_ah/api/explorer.
2. Go to the `create_user` endpoint and add the user.
3. Go to the `new_game` endpoint and create a new game. The default value for attempts_remaining is 6.
4. Go to the `make_move` endpoint and use the `urlsafe_game_key` to enter a single letter.
   If you do not enter any letter or enter multiple letters, the game shows an error message.
   If you enter a letter occurring in the word, you'll see the message with the letters you have got right
   so far in their respective positions.
   If you enter a letter not appearing in the word, you'll see a message with the attempts remaining.
5. Once you have all the letters right, or are out of attempts, whichever occurs first, the game ends and
   you win or lose respectively.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique.
    Raises a ConflictException if a User with that user_name or email already exists.
    Raises a BadRequestException if the email or the user_name is not entered.

 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, answer, attempts
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. answer must not be empty,
    else BadRequestException is raised. Also adds a task to a task queue to update
    the average moves remaining for active games.

 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.

 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, move
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.
    Raise BadRequestException if the player enters multiple characters.

 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).

 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms.
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.

 - **get_average_attempts**
    - Path: 'games/average_attempts'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average number of attempts remaining for all active games
    from a previously cached memcache key.

 - **get_user_games**
    - Path: 'user/{user_name}/games'
    - Method: GET
    - Parameters: user_name
    - Returns: GameForms
    - Description: This returns all of a User's active games. Each game has an ancestor User,
    and hence all the games with the user with user_name are queried.
    Raises BadRequestException if no user with user_name is found in the datastore.

 - **cancel_game**
    - Path: 'game/{urlsafe_game_key}/cancel'
    - Method: DELETE
    - Parameters: urlsafe_game_key
    - Returns: StringMessage
    - Description: This endpoint deletes a game in progress.
     Raises ForbiddenException if the game is already over.
     Raises NotFoundException if no such game is found in the datastore.

 - **get_high_scores**
    - Path: 'scores/high_scores'
    - Method: GET
    - Parameters: number_of_results
    - Returns: ScoreForms
    - Description: Generate a list of high scores in descending order, like a leader-board!
    Accept an optional parameter number_of_results that limits the number of results returned.
    Raises NotFoundException if no scores are found for any users.

 - **get_user_rankings**
    - Path: 'users/rankings'
    - Method: GET
    - Parameters: None
    - Returns: UserForms
    - Description: Return a list of users in descending order of wins to total number
    of games played ratio. In case of a tie, the player with fewer games played wins.
    Raises NotFoundException if no scores are found for any users.


 - **get_game_history**
    - Path: 'game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameHistory
    - Description: View a 'history' of moves for each game. The history shows the user moves for the game.
    Raises NotFoundException if no such game is found.

##Models Included:
 - **User**
    - Stores unique user_name, email address, total games won, total games played, win ratio.
    win_ratio helps in fetching user rankings for `get_user_rankings` endpoint.

 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    `move_history` stores the history of moves for each game.
    `answer` stores all the correct letters that the players enters while playing the game.

 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.

##Forms Included:
 - **UserForm**
     - Representation of a User's information (name, email, won, total_played).
 - **UserForms**
      - Multiple UserForm container.
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts, attempts_remaining,
    game_over flag, message, user_name).
 - **NewGameForm**
     - Used to create a new game (user_name, answer, attempts)
 - **GameForms**
     - Multiple GameForm container.
 - **GetHighScoresForm**
    - Representation of high scores (number_of_results).
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    attempts_used, attempts).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **StringMessage**
    - General purpose String container.
 - **GameHistory**
    - History of moves of a game.
