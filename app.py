from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_cors import CORS
from config_banco import db, User, Post
from dotenv import load_dotenv
import os
import requests

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)

# Habilita CORS
CORS(app)

# Configurações do Banco de Dados e Segurança
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'devnet.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")

# Inicializa o banco de dados
db.init_app(app)

# Cria as tabelas se não existirem
with app.app_context():
    db.create_all()

# Configurações do GitHub OAuth
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

# =========================
#    SISTEMA DE LOGIN
# =========================

@app.route('/login')
def login():
    # Se já está logado, não precisa ver a tela de login
    if 'user_id' in session:
        return redirect(url_for('feed')) 
    return render_template('login.html')

@app.route('/login/github')
def login_github():
    # Impede login duplicado
    if 'user_id' in session:
        return redirect(url_for('feed'))
        
    # Solicita o escopo 'user:email' para garantir que pegamos o e-mail real
    github_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=user:email"
    return redirect(github_url)

@app.route('/login/github/callback')
def github_callback():
    code = request.args.get('code')
    
    # 1. Troca o código pelo Access Token
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

    # 2. Pega os dados básicos do usuário (login)
    user_data = requests.get(
        'https://api.github.com/user',
        headers={'Authorization': f'token {access_token}'}
    ).json()
    github_username = user_data.get('login')

    # 3. Busca o E-MAIL REAL (Endpoint de e-mails privados)
    emails_resp = requests.get(
        'https://api.github.com/user/emails',
        headers={'Authorization': f'token {access_token}'}
    ).json()

    # Filtra para encontrar o e-mail primário
    github_email = None
    for email_obj in emails_resp:
        if email_obj.get('primary'):
            github_email = email_obj.get('email')
            break

    # 4. Lógica de Persistência no devnet.db
    user = User.query.filter_by(username=github_username).first()

    if not user:
        # Se o usuário não existir, cria com o e-mail real
        user = User(username=github_username, email=github_email)
        db.session.add(user)
    else:
        # Se já existia, garante que o e-mail esteja atualizado para o real
        user.email = github_email
    
    db.session.commit()

    # 5. Define a sessão
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
#    PAINEL ADMINISTRATIVO
# =========================

@app.route('/admin')
def admin_panel():
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(url_for('login'))

    # Busca o usuário usando a sessão atual (SQLAlchemy 2.0 style)
    user_admin = db.session.get(User, user_id)
    
    # Validação do e-mail do Diretor
    if not user_admin or user_admin.email != 'lucasdanielrocha2009@gmail.com':
        return "<h1>Acesso Negado</h1><p>Você não tem permissão de administrador.</p>", 403

    # Dados para exibição no painel
    todos_usuarios = User.query.all()
    todos_posts = Post.query.all()

    return render_template('painel-adm.html', 
                           usuarios=todos_usuarios, 
                           posts=todos_posts,
                           admin=user_admin)

# =========================
#    ARQUIVOS ESTÁTICOS
# =========================

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    print("\n✅  Servidor DevNet iniciado na porta 3000")
    print("⚠️   Aperte CTRL+C para encerrar o servidor\n")
    
    app.run(host='localhost', port=3000, debug=True)