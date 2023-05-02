from flask import (Flask, request, render_template, 
                   send_file, redirect, flash, url_for, session)
from flask_socketio import SocketIO, send
from PIL import Image
import io


app = Flask(__name__)
app.secret_key = 'SS'

@app.route('/')
def index():
    return render_template('file_test.html')


@app.route('/upload_files', methods=['POST'])
def upload_files():
    print(request.files)
    print(request.files.getlist('files'))
    return '0'


app.run(debug=True)