from flask import Blueprint, render_template

from .. import max_images_per_day, max_text_per_day


main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def index():
    return render_template('index.html', images=max_images_per_day, chats=max_text_per_day)
