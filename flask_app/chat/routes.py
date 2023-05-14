import base64
import datetime
import openai
import uuid

from flask import Blueprint, render_template, flash, redirect, url_for, session
from flask_login import login_required, current_user
from mongoengine.queryset.visitor import Q

from ..forms import InitiateChatForm, SendChatForm
from ..models import AIChatContext, AIChatMessage, load_user
from ..util import queries_mongodb
from ..client.openai_api import ChatSession

from .. import max_text_per_day

chat_blueprint = Blueprint('chat', __name__)

@chat_blueprint.route('/chat', defaults={'username': None}, methods=['GET'])
@chat_blueprint.route('/chat/<username>', methods=['GET'])
@queries_mongodb
def chat(username):
    if username:
        user = load_user(username)
        if not user:
            return render_template('404.html', message=f"User '{username}' does not exist."), 404
        chat_contexts = AIChatContext.objects(creator=user).order_by('-created')
        chats = ((context, AIChatMessage.objects(context=context).order_by('+created')) for context in chat_contexts)
    else:
        chat_contexts = AIChatContext.objects().order_by('-created')[:10]
        chats = ((context, AIChatMessage.objects(context=context).order_by('+created')) for context in chat_contexts)
    return render_template('chat.html', username=username, chats=chats if chat_contexts else [])

@chat_blueprint.route('/end_chat', methods=['GET'])
@login_required
def end_chat():
    session.pop('chat_id', None)
    return redirect(url_for('chat.chat_create'))

@chat_blueprint.route('/resume_chat/<id>', methods=['GET'])
@login_required
@queries_mongodb
def resume_chat(id):
    session['chat_id'] = uuid.UUID(id)
    return redirect(url_for('chat.chat_create'))

@chat_blueprint.route('/chat_create', methods=['GET', 'POST'])
@login_required
@queries_mongodb
def chat_create():
    current_context_id = session.get('chat_id', None)
    d = datetime.datetime.now() - datetime.timedelta(days=1)
    # https://docs.mongoengine.org/guide/querying.html

    user_contexts = AIChatContext.objects(creator=current_user._get_current_object())
    chats_within_one_day = sum(([x for x in AIChatMessage.objects(Q(context=context) & Q(created__gte=d) & Q(role='user'))] for context in user_contexts), [])

    next_use = None
    if (len(chats_within_one_day) >= max_text_per_day):
        next_use = min(chats_within_one_day, key=lambda x: x.created).created + datetime.timedelta(days=1)

    # This doubles as validation since we save the id as a cookie, clients can theoretically change it
    current_context = next((x for x in user_contexts if x.uuid == current_context_id), None) if current_context_id else None
    current_messages = [x for x in AIChatMessage.objects(context=current_context).order_by('+created')] if current_context else []

    init_form = InitiateChatForm()
    chat_form = SendChatForm()

    if init_form.validate_on_submit() and not current_context and not next_use:
        context = AIChatContext(
            uuid = uuid.uuid4(),
            creator = current_user._get_current_object(),
            context = init_form.prompt.data,
            created = datetime.datetime.now()
        )
        context.save()
        session['chat_id'] = context.uuid
        current_context = context
    elif chat_form.validate_on_submit() and current_context and not next_use:
        chat_session = ChatSession.from_models(current_context, current_messages)
        message = chat_form.message.data
        outgoing_message = AIChatMessage(
            context = current_context,
            role = 'user',
            content = message,
            created = datetime.datetime.now()
        )
        outgoing_message.save()
        
        try:
            result = chat_session.get_chat_completion(message)
            incoming_message = AIChatMessage(
                context = current_context,
                role = 'assistant',
                content = result,
                created = datetime.datetime.now()
            )
            incoming_message.save()
            current_messages.append(outgoing_message)
            current_messages.append(incoming_message)
        except openai.OpenAIError:
            flash('Oh no! Failed to query the OpenAI API. Please try again later.')

    return render_template('chat_create.html', init_form=init_form, chat_form=chat_form, uses=max_text_per_day - len(chats_within_one_day), next_use=next_use, current_context=current_context, current_messages=current_messages)
