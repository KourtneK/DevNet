from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_cors import CORS
from config_banco import db, User, Post
from dotenv import load_dotenv
import os
import requests

# 1. Carrega as variáveis do .env antes de tudo
load_dotenv()

app = Flask(__name__)
CORS(app)

# 2. Configurações do Banco e Segurança
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'devnet.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")

db.init_app(app)

with app.app_context():
    db.create_all()

# 3. Configurações OAuth
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

# =========================
#    ROTAS DE AUTENTICAÇÃO
# =========================

@app.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('feed')) 
    return render_template('login.html')

@app.route('/login/github')
def login_github():
    if 'user_id' in session:
        return redirect(url_for('feed'))
    github_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=user:email"
    return redirect(github_url)

@app.route('/login/github/callback')
def github_callback():
    code = request.args.get('code')
    
    token_resp = requests.post(
        'https://github.com/login/oauth/access_token',
        data={
            'client_id': GITHUB_CLIENT_ID,
            'client_secret': GITHUB_CLIENT_SECRET,
            'code': code
        },
        headers={'Accept': 'application/json'}
    ).json()
    
    access_token = token_resp.get('access_token')

    user_data = requests.get(
        'https://api.github.com/user',
        headers={'Authorization': f'token {access_token}'}
    ).json()
    github_username = user_data.get('login')

    emails_resp = requests.get(
        'https://api.github.com/user/emails',
        headers={'Authorization': f'token {access_token}'}
    ).json()

    github_email = next((e['email'] for e in emails_resp if e['primary']), None)

    user = User.query.filter_by(username=github_username).first()

    if not user:
        user = User(username=github_username, email=github_email)
        db.session.add(user)
    else:
        user.email = github_email
    
    db.session.commit()
    session['user_id'] = user.id
    session['username'] = user.username
    
    return redirect(url_for('feed'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# =========================
#    PÁGINAS DO FRONTEND
# =========================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/feed')
def feed():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('feed.html')

@app.route('/perfil')
def perfil():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('perfil.html')

@app.route('/config')
def config_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('config.html')

# =========================
#    PAINEL ADMIN
# =========================

@app.route('/admin')
def admin_panel():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user_admin = db.session.get(User, user_id)
    
    #
    if not user_admin or user_admin.email != 'lucasdanielrocha2009@gmail.com':
        return "<h1>Acesso Negado</h1>", 403

    todos_usuarios = User.query.all()
    todos_posts = Post.query.all()

    return render_template('painel-adm.html', 
                           usuarios=todos_usuarios, 
                           posts=todos_posts,
                           admin=user_admin)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(host='localhost', port=3000, debug=True)