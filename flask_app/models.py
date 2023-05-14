from flask import session, current_app, request
from flask_login import UserMixin, COOKIE_NAME

from . import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    try:
        # As a stop gap to prevent long load times when backend is down,
        # ?serverselectiontimeoutms=2000 is set in uri
        return User.objects(username=user_id).first()
    except Exception:
        # Unable to look up the user. Clear the "remember me" cookie
        # to prevent latency when loading pages
        if '_user_id' in session:
            session.pop('_user_id')
        if '_fresh' in session:
            session.pop('_fresh')
        if '_id' in session:
            session.pop('_id')
        if 'chat_id' in session:
            session.pop('chat_id')

        cookie_name = current_app.config.get('REMEMBER_COOKIE_NAME', COOKIE_NAME)
        if cookie_name in request.cookies:
            session['_remember'] = 'clear'
            if '_remember_seconds' in session:
                session.pop('_remember_seconds')
        current_app.login_manager._update_request_context_with_user()
        return None

class User(db.Document, UserMixin):
    username = db.StringField(required=True, unique=True)
    email = db.EmailField(required=True, unique=True)
    password = db.StringField(required=True)

    # Returns unique string identifying our object
    def get_id(self):
        return self.username

class AIImage(db.Document):
    uuid = db.UUIDField(required=True)
    creator = db.ReferenceField(User, required=True)
    prompt = db.StringField(required=True)
    raw = db.ImageField(required=True)
    created = db.DateTimeField(required=True)

class AIChatContext(db.Document):
    uuid = db.UUIDField(required=True)
    creator = db.ReferenceField(User, required=True)
    context = db.StringField(required=True)
    created = db.DateTimeField(required=True)

class AIChatMessage(db.Document):
    context = db.ReferenceField(AIChatContext, required=True)
    content = db.StringField(required=True)
    role = db.StringField(required=True)
    created = db.DateTimeField(required=True)
