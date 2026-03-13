from flask import Flask, render_template     #importa o flask
from flask_cors import CORS     #importa o flask cors
from config_banco import db, User, Post     # Importa o banco e os modelos
import os
from flask import send_from_directory
import requests
from flask import request, redirect, url_for, session
from dotenv import load_dotenv

app = Flask(__name__)

# Habilita CORS para permitir requisições de diferentes origens
CORS(app)

# Configura o nome do arquivo do banco de dados exatamente como solicitado
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'devnet.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")

# Inicializa o banco de dados com as configurações do app
db.init_app(app)

# Cria o arquivo devnet.db e as tabelas automaticamente se não existirem
with app.app_context():
    db.create_all()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

@app.route('/login/github')
def login_github():
    # 1. Redireciona para o GitHub pedindo autorização
    github_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=user"
    return redirect(github_url)

@app.route('/login/github/callback')
def github_callback():
    # 2. GitHub volta com um código na URL
    code = request.args.get('code')
    
    # 3. Troca o código pelo Access Token
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

    # 4. Usa o token para pegar os dados do usuário
    user_data = requests.get(
        'https://api.github.com/user',
        headers={'Authorization': f'token {access_token}'}
    ).json()

    # Aqui você já tem o username e email do GitHub!
    print(f"Usuário logado: {user_data.get('login')}")
    
    # Próximo passo: salvar no seu devnet.db (SQLAlchemy)
    return redirect(url_for('feed'))

# Rota favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# =========================
# ROTAS DO FRONTEND
# =========================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/feed')
def feed():
    return render_template('feed.html')

@app.route('/perfil')
def perfil():
    return render_template('perfil.html')

@app.route('/config')
def config_page():
    return render_template('config.html')

@app.route('/login')
def login():
    return render_template('login.html')

if __name__ == '__main__':
    print("\n✅  Servidor DevNet iniciado na porta 3000")
    print("⚠️   Aperte CTRL+C para encerrar o servidor\n")
    
    app.run(host='localhost', port=3000, debug=True)