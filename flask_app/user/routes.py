import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from flask_login import current_user, login_user, login_required, logout_user
from mongoengine.queryset.visitor import Q

from .. import bcrypt
from ..forms import LoginForm, RegistrationForm, UpdateUsernameForm
from ..models import User, AIImage, AIChatContext, AIChatMessage
from ..util import queries_mongodb, redirect_dest

from .. import max_images_per_day, max_text_per_day


user = Blueprint('user', __name__)

@user.route("/register", methods=['GET', 'POST'])
@queries_mongodb
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user.account'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data, email=form.email.data, password=hashed)
        user.save()

        flash('Registration complete! Please log in.')
        return redirect(url_for('user.login'))
    
    return render_template('register.html', title="Register", form=form)


@user.route('/login', methods=['GET', 'POST'])
@queries_mongodb
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user.account'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(username=form.username.data).first()

        if user is not None and bcrypt.check_password_hash(
            user.password, form.password.data
        ):
            login_user(user)
            return redirect_dest(fallback=url_for('user.account'))
        else:
            flash('Login failed. Check your username and/or password.')
            return redirect(url_for('user.login'))

    return render_template('login.html', title='Login', form=form)


@user.route('/account', methods=['GET', 'POST'])
@login_required
@queries_mongodb
def account():
    d = datetime.datetime.now() - datetime.timedelta(days=1)
    # https://docs.mongoengine.org/guide/querying.html
    images_within_1_day = AIImage.objects(Q(creator=current_user._get_current_object()) & Q(created__gte=d))
    user_contexts = AIChatContext.objects(creator=current_user._get_current_object())
    chats_within_one_day = sum(([x for x in AIChatMessage.objects(Q(context=context) & Q(created__gte=d) & Q(role='user'))] for context in user_contexts), [])
    
    next_image_use = None
    if (len(images_within_1_day) >= max_images_per_day):
        next_image_use = min(images_within_1_day, key=lambda x: x.created).created + datetime.timedelta(days=1)

    next_chat_use = None
    if (len(chats_within_one_day) >= max_text_per_day):
        next_chat_use = min(chats_within_one_day, key=lambda x: x.created).created + datetime.timedelta(days=1)

    form = UpdateUsernameForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.save()
        flash('Please log in again with your new username.')
        return redirect(url_for('user.login'))

    return render_template('account.html', form=form, image_uses=max_images_per_day - len(images_within_1_day), chat_uses=max_text_per_day - len(chats_within_one_day) ,next_image_use=next_image_use, next_chat_use=next_chat_use)


@user.route('/user/<username>', methods=['GET'])
@queries_mongodb
def user_page(username):
    user = User.objects(username=username)
    if not user:
        return render_template('404.html', message=f"user '{username}' does not exist.")
    return render_template('user.html', username=username)


@user.route("/logout")
@login_required
def logout():
    session.pop('chat_id', None)
    logout_user()
    return redirect(url_for('main.index'))
