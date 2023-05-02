from flask import Flask, request, send_file, render_template, session, flash, url_for, redirect
import os

content_types = ['image', 'video', 'audio']
root = 'storage'

required_paths = [root] + [root + '/' + ct 
                           for ct in content_types]

for req_path in required_paths:
    if not os.path.exists(req_path):
        os.mkdir(req_path)


app = Flask(__name__)
app.secret_key = 'SS'

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_content/<type>/<idx>', methods=['GET'])
def get_content(type, idx):
    url = os.path.join(root, type, idx)
    ext = idx[idx.rindex('.') + 1:]
    return send_file(url, mimetype=f'{type}/{ext}')

app.run(debug=True)
