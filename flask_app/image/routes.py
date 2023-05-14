import base64
import datetime
import openai
import uuid

from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from mongoengine.queryset.visitor import Q

from ..forms import ImageCreateForm
from ..models import AIImage, load_user
from ..util import queries_mongodb
from ..client.openai_api import generate_image

from .. import max_images_per_day


image_blueprint = Blueprint('image', __name__)

@image_blueprint.route('/image', defaults={'username': None}, methods=['GET'])
@image_blueprint.route('/image/<username>', methods=['GET'])
@queries_mongodb
def image(username):
    if username:
        user = load_user(username)
        if not user:
            return render_template('404.html', message=f"User '{username}' does not exist."), 404
        images = AIImage.objects(creator=user).order_by('-created')
    else:
        images = AIImage.objects().order_by('-created')[:10]
    return render_template('image.html', username=username, images=[(x.creator.username, x.prompt, base64.b64encode(x.raw.read()).decode(), x.created, x.uuid) for x in images])

@image_blueprint.route('/image_create', methods=['GET', 'POST'])
@login_required
@queries_mongodb
def image_create():
    d = datetime.datetime.now() - datetime.timedelta(days=1)
    # https://docs.mongoengine.org/guide/querying.html
    images_within_1_day = AIImage.objects(Q(creator=current_user._get_current_object()) & Q(created__gte=d))

    next_use = None
    if (len(images_within_1_day) >= max_images_per_day):
        next_use = min(images_within_1_day, key=lambda x: x.created).created + datetime.timedelta(days=1)

    form = ImageCreateForm()
    if form.validate_on_submit() and not next_use:
        try:
            image = generate_image(form.prompt.data)
            ai_image = AIImage(
                uuid = uuid.uuid4(),
                creator = current_user._get_current_object(),
                prompt = form.prompt.data,
                raw = image,
                created = datetime.datetime.now()
            )
            ai_image.save()

            return redirect(url_for('image.image_display', id=ai_image.uuid))
        except openai.OpenAIError:
            flash('Oh no! Failed to query the OpenAI API. Please try again later.')
    
    return render_template('image_create.html', uses=max_images_per_day - len(images_within_1_day), next_use=next_use, form=form)

@image_blueprint.route('/image_display/<id>', methods=['GET'])
@queries_mongodb
def image_display(id):

    try:
        input_uuid = uuid.UUID(id)
    except ValueError:
        return render_template('404.html', message='Bad UUID'), 404

    image = AIImage.objects(uuid=input_uuid).first()
    if not image:
        return render_template('404.html', message='Image does not exist'), 404

    return render_template('image_display.html', image=(image.creator.username, image.prompt, base64.b64encode(image.raw.read()).decode(), image.created), back='')

