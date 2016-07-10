from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    won = ndb.IntegerProperty(default=0)
    total_played = ndb.IntegerProperty(default=0)
    win_ratio = ndb.FloatProperty(default=0.0)

    def to_form(self):
        """Returns a UserForm representation of the User.
        Args:
            None.
        Returns:
            UserForm: Form representation of the user.
        """
        form = UserForm()
        form.name = self.name
        form.email = self.email
        form.won = self.won
        form.total_played = self.total_played
        form.win_ratio = self.win_ratio
        return form


class UserForm(messages.Message):
    """User Form"""
    name = messages.StringField(1, required=True)
    email = messages.StringField(2)
    won = messages.IntegerField(3, required=True)
    total_played = messages.IntegerField(4, required=True)
    win_ratio = messages.FloatField(5)


class UserForms(messages.Message):
    """Container for multiple User Forms"""
    items = messages.MessageField(UserForm, 1, repeated=True)
