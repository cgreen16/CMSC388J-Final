import base64
from dotenv import load_dotenv
import io
import openai
import os
import uuid

load_dotenv()

openai.api_key = os.environ.get('OPENAI_API_KEY')

class ChatSession:
    def __init__(self, control):
        assert isinstance(control, str)
        self.uuid = uuid.uuid4()
        self.context = control
        self._state = [
            {'role': 'system', 'content': f"{control}. You are an assistant."}
        ]

    def get_chat_completion(self, content):
        assert isinstance(content, str)
        self._state.append({'role': 'user', 'content': content})
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=self._state, temperature=0.5)
        result = completion['choices'][0]['message']['content']
        self._state.append({'role': 'assistant', 'content': result})
        return result

    @classmethod
    def from_models(cls, context, messages):
        c = cls(context.context)
        c._state += [{'role': message.role, 'content': message.content} for message in messages]
        return c

def generate_image(prompt):
    generation_response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1024x1024",
        response_format="b64_json",
    )

    raw_b64 = generation_response['data'][0]['b64_json']
    raw_image = base64.b64decode(raw_b64)
    return io.BytesIO(raw_image)
