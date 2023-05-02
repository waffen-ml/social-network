from flask import (Flask, request, render_template, 
                   send_file, redirect, flash, url_for, session)
from flask_socketio import SocketIO, send
import os
from universal import *
from my_forms import *
from chat import *
import io
import json


app = Flask(__name__)
app.secret_key = 'SS'
socketio = SocketIO(app, cors_allowed_origins="*")
root = 'http://127.0.0.1:5000/'
DATA_TYPES = ['image', 'video', 'audio']


def classify_data(data):
    d = {dt: [] for dt in DATA_TYPES}
    for obj in data:
        a, b = obj.split('/')
        if a not in d:
            continue
        d[a].append(b)
    return d


class User:
    def __init__(self, user_name, account_name, email, password):
        self.user_name = user_name
        self.account_name = account_name
        self.email = email
        self.password = password

    def set_idx(self, idx):
        self.idx = idx

    def html(self):
        return html('<a class="profile" href="#">',
            '<img src="" class="profile-icon">',
            f'<span class="profile-name">{self.user_name}</span></a>')


class Content:
    def __init__(self, text='', additionals=[]):
        self.text = text
        classified = classify_data(additionals)
        self.image = classified['image']
        self.video = classified['video']
        self.audio = classified['audio']

    def html(self):
        content = f'<div class="content"><p class="text-data">{self.text}</p>'
        ni = len(self.image)
        nv = len(self.video)

        if ni + nv > 1:
            d, r = divmod(ni + nv, 3)
            s = (d - (r == 1)) * 3
            content += '<div class="visual-grid">'
            for i, visual in enumerate(self.image + self.video):
                is_video = i >= ni
                cls_appendix = ' video' if is_video else ''
                cls_appendix += ' small' if i < s else ''
                data_link = ('video' if is_video else 'image') + '/' + visual
                script = f"javascript: showContent('{data_link}')"
                src = 'get_content/' + data_link
                content += f'<a class="tile{cls_appendix}" href="{script}">'
                if is_video:
                    content += f'<video><source src="{src}"></video>'
                else:
                    content += f'<img src="{src}">'
                content += '</a>'
            content += '</div>'
        elif ni == 1:
            content += html('<img class="semi-visual" ', 
                f'src="/get_content/image/{self.image[0]}">')
        elif nv == 1:
            content += html('<video class="semi-visual" controls>',
                f'<source src="/get_content/video/{self.video[0]}"></video>')

        if len(self.audio) > 0:
            content += '<div class="audio-block">'
            for a_idx in self.audio:
                content += html('<audio controls>',
                    f'<source src="/get_content/audio/{a_idx}"',
                    'type="audio/mp3"></audio>')
            content += '</div>'

        return content + '</div>'


class Post:
    def __init__(self, content, sender):
        self.content = content
        self.sender = sender
        self.upload_date = get_today()

    def html(self):
        profile_header = self.sender.html()
        content_html = self.content.html()
        return html(
            '<div class="post block">',
            profile_header, content_html,
            '<div class="bottom">',
            '<div class="actions">',
            '<input type="button" value="👍" class="button">',
            '<input type="button" value="👎" class="button">',
            '<input type="button" value="💬" class="button">',
            f'</div><span class="date">{self.upload_date}</span></div></div>'
        )


class FileSystem:
    def __init__(self, root):
        required_paths = [root] + [root + '/' + ct 
                           for ct in DATA_TYPES]
        for req_path in required_paths:
            if not os.path.exists(req_path):
                os.mkdir(req_path)

        self.root = root
        self.index_table = {dt: MovingIndex()
            for dt in DATA_TYPES}

    def append(self, file):
        a, b = file.mimetype.split('/')
        if a not in DATA_TYPES:
            return None
        idx = self.index_table[a].next()
        link = f'{a}/{idx}.{b}'
        file.save(f'{self.root}/{link}')
        return link

    def extend(self, files):
        return [self.append(file) for file in files]

    def get_path(self, link):
        return os.path.join(self.root, *link.split('/'))


class UserSystem:
    def __init__(self):
        self.users = IndexedArray()

    def does_account_exist(self, name):
        return self.get_account_by_name(name) is not None
    
    def get_account_by_name(self, name):
        for user in self.users.values():
            if user.account_name == name:
                return user
        return None
    
    def add_user(self, user):
        idx = self.users.add(user)
        user.set_idx(idx)
        return idx

    def get_user(self, idx):
        return self.users.get(idx)


def is_account_name_valid(name):
    return True


def register_handler(data):
    if data['password'] != data['password-rep']:
        return False, 'Пароли не совпадают'
    if not is_account_name_valid(data['account_name']):
        return False, 'Некорректное имя аккаунта'
    if user_system.does_account_exist(data['account_name']):
        return False, 'Это имя аккаунта уже занято'

    session['idx'] = user_system.add_user(User(
        data['user_name'], data['account_name'],
        data['email'], data['password']
    ))

    return True, 'index'


def login_handler(data):
    user = user_system.get_account_by_name(
        data['account_name'])
    if user is None:
        return False, 'Аккаунта с таким именем не найдено'
    if user.password != data['password']:
        return False, 'Неверный пароль'
    session['idx'] = user.idx
    return True, 'index'


user_system = UserSystem()


def get_logined():
    if 'idx' not in session:
        return None
    idx = session['idx']
    return user_system.get_user(idx)


def is_logined():
    return get_logined() is not None


def get_files(name='files'):
    files = request.files.getlist(name)
    return files if files[0] else []


fs = FileSystem('storage')
posts_storage = IndexedArray()

forms = IndexedArray()
forms.add(Form('Регистрация', register_handler, [
        Inputfield('user_name', 'Ваше имя'),
        Inputfield('account_name', 'Имя аккаунта'),
        Inputfield('email', 'Электронная почта', email=True),
        Inputfield('password', 'Пароль', password=True),
        Inputfield('password-rep', 'Повторите пароль', password=True)
    ], exit_cond=is_logined))
forms.add(Form('Вход', login_handler, [
        Inputfield('account_name', 'Имя аккаунта'),
        Inputfield('password', 'Пароль', password=True),
    ]))

main_chat = Chat()



def render(temp_name, css=[], **kwargs):
    nav = [
        ('Создать пост', 'create_post'),
        ('Новости', 'posts'),
        ('Мессенджер', 'chat'),
        ('Выход', 'log_off')
    ] if is_logined() else [
        ('Вход', 'form/1'),
        ('Регистрация', 'form/0')
    ]
    css = ['style.css', 'popup.css'] + css
    return render_template(temp_name, nav=nav, css=css, **kwargs)


@app.route('/')
def index():
    if is_logined():
        return redirect('/posts')
    return redirect('/form/1')


@app.route('/create_post', methods=['POST', 'GET'])
def create_post():
    if request.method == 'POST':
        text = request.form['text']
        files = get_files('addit')
        addit_idx = fs.extend(files)
        post = Post(
            Content(text, addit_idx),
            get_logined())
        posts_storage.add(post)
    if not is_logined():
        return redirect('/')
    return render('create_post.html')


@app.route('/posts')
def posts():
    return render('posts.html', posts=posts_storage.values())


@app.route('/get_content/<type>/<idx>', methods=['GET'])
def get_content(type, idx):
    path = fs.get_path(f'{type}/{idx}')
    ext = idx[idx.rindex('.') + 1:]
    return send_file(path, mimetype=f'{type}/{ext}')


@app.route('/form/<int:idx>', methods=['GET', 'POST'])
def form(idx):
    target = forms[idx]
    if request.method == 'POST':
        success, text = target(request.form)
        if success: return redirect(url_for(text))
        target = target.fill(request.form)
        flash(text)
    if target.exit_cond():
        return redirect('/')
    return render('form.html', form=target, idx=idx)


@app.route('/log_off')
def log_off():
    del session['idx']
    return redirect('/')


@app.route('/chat')
def chat():
    if not is_logined():
        return redirect('/')
    chat_html = main_chat.html(10)
    return render('chat.html', 
                  css=['chat.css'],
                  chat_html=chat_html,
                  my_idx=get_logined().idx)


@app.route('/upload_files', methods=['POST'])
def upload_files():
    files = get_files('files')
    return json.dumps(fs.extend(files))


@socketio.on('message')
def message(msg):
    text = msg['text']
    addit_idx = msg['attached_files']
    msg = Message(Content(text, addit_idx), get_logined())
    n = main_chat.add_message(msg)
    html = main_chat.html(n)
    send(html, broadcast=True)


socketio.run(app, debug=True)
#app.run(debug=True)

