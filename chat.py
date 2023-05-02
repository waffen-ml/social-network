import datetime
from universal import *


class Message:
    def __init__(self, content, sender):
        self.time = get_now()
        self.content = content
        self.sender = sender

    def html(self):
        sender_idx = self.sender.idx
        return html(f'<div class="message block" from="{sender_idx}">',
            f'<div class="head"><a href="#" class="sender">{self.sender.user_name}</a>',
            f'<span class="special">({self.time})</span></div>',
            self.content.html(), '</div>')


class SystemMessage:
    def __init__(self, text):
        self.text = text

    def html(self):
        return f'<span class="system-message special">{self.text}</span>'


class Chat:
    def __init__(self):
        self.messages = []

    def add_message(self, msg):
        self.messages.append(msg)
        return 1

    def html(self, n=-1):
        n = n if n >= 0 else len(self.messages)
        return html(*[  
            msg.html() for msg in self.messages[-n:]
        ])