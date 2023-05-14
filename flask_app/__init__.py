# 3rd-party packages
from flask import Flask, render_template
from flask_mongoengine import MongoEngine
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_talisman import Talisman

def page_not_found(e):
    return render_template('404.html', title='Page Not Found'), 404

db = MongoEngine()
login_manager = LoginManager()
bcrypt = Bcrypt()

max_images_per_day = 3
max_text_per_day = 50

from .main.routes import main
from .user.routes import user
from .image.routes import image_blueprint
from .chat.routes import chat_blueprint

def create_app(test_config=None):
    app = Flask(__name__)

    Talisman(app, content_security_policy={
        'default-src': '\'self\'',
        'script-src': ['\'self\'', 'code.jquery.com', 'stackpath.bootstrapcdn.com'],
        'style-src': ['\'self\'', 'stackpath.bootstrapcdn.com'],
        'img-src': ['\'self\'', 'data:'],
    }, content_security_policy_nonce_in=['script-src'])

    app.config.from_pyfile('config.py', silent=False)
    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    app.register_blueprint(main)
    app.register_blueprint(user)
    app.register_blueprint(image_blueprint)
    app.register_blueprint(chat_blueprint)
    app.register_error_handler(404, page_not_found)
    
    login_manager.login_view = 'user.login'
    
    return app
