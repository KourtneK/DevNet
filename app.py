from flask import Flask, render_template     #importa o flask
from flask_cors import CORS     #importa o flask cors
from config_banco import db, User, Post     # Importa o banco e os modelos
import os
from flask import send_from_directory
import requests
from flask import request, redirect, url_for, session

app = Flask(__name__)

# Habilita CORS para permitir requisições de diferentes origens
CORS(app)

# Configura o nome do arquivo do banco de dados exatamente como solicitado
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'devnet.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '35798081'

# Inicializa o banco de dados com as configurações do app
db.init_app(app)

# Cria o arquivo devnet.db e as tabelas automaticamente se não existirem
with app.app_context():
    db.create_all()

GITHUB_CLIENT_ID = "Ov23li2BzA0MMMH6jZZC"
GITHUB_CLIENT_SECRET = "f69d003b6cbc854c265dd6b57edce3915e6f47de"

@app.route('/login/github')
def login_github():
    # Impede que o usuário inicie o processo de OAuth se já estiver logado
    if 'user_id' in session:
        return redirect(url_for('feed'))
        
    github_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=user:email"
    return redirect(github_url)


# Rota github
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

    # 2. Pega os dados básicos do usuário (login/username)
    user_data = requests.get(
        'https://api.github.com/user',
        headers={'Authorization': f'token {access_token}'}
    ).json()
    github_username = user_data.get('login')

    # 3. BUSCA O E-MAIL REAL: Faz uma nova requisição para pegar todos os e-mails
    emails_resp = requests.get(
        'https://api.github.com/user/emails',
        headers={'Authorization': f'token {access_token}'}
    ).json()

    # Filtra para encontrar o e-mail marcado como 'primary'
    github_email = None
    for email_obj in emails_resp:
        if email_obj.get('primary'):
            github_email = email_obj.get('email')
            break

    # 4. Lógica de Banco de Dados
    user = User.query.filter_by(username=github_username).first()

    if not user:
        # Se o usuário não existir, cria com o e-mail real capturado
        user = User(username=github_username, email=github_email)
        db.session.add(user)
    else:
        # Se o usuário já existia (talvez com e-mail errado), atualiza para o real
        user.email = github_email
    
    db.session.commit()

    # 5. Salva o ID na sessão para acesso às rotas protegidas
    session['user_id'] = user.id
    
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
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('perfil.html')

@app.route('/config')
def config_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('config.html')

@app.route('/login')
def login():
    # Verifica se a chave do usuário está na sessão
    if 'user_id' in session:
        # Se já está logado, não precisa ver a tela de login novamente
        return redirect(url_for('feed')) 
        
    return render_template('login.html')

# ==================
#   ROTAS BACK-END
# ==================

@app.route('/admin') # Esta é a única rota que o Flask vai reconhecer
def admin_panel():   # Unificamos o nome da função
    # 1. Recupera o ID do usuário da sessão
    user_id = session.get('user_id')
    
    # 2. Segurança: Se não estiver logado, manda para o login
    if not user_id:
        return redirect(url_for('login'))

    # 3. Busca o usuário logado no banco de dados
    user_admin = User.query.get(user_id)
    
    # 4. Verifica se o e-mail é o autorizado
    if not user_admin or user_admin.email != 'lucasdanielrocha2009@gmail.com':
        return "<h1>Acesso Negado</h1><p>Você não tem permissão de administrador.</p>", 403

    # 5. Busca os dados reais do seu devnet.db para exibir no HTML
    todos_usuarios = User.query.all()
    todos_posts = Post.query.all()

    # 6. ESSENCIAL: Aponta para o arquivo e ENVIA os dados para ele
    return render_template('painel-adm.html', 
                           usuarios=todos_usuarios, 
                           posts=todos_posts,
                           admin=user_admin)

# rota logout
@app.route('/logout')
def logout():
    # Limpa todos os dados da sessão (remove o user_id)
    session.clear()
    # Redireciona de volta para a home
    return redirect(url_for('home'))


if __name__ == '__main__':
    print("\n✅  Servidor DevNet iniciado na porta 3000")
    print("⚠️   Aperte CTRL+C para encerrar o servidor\n")
    
    app.run(host='localhost', port=3000, debug=True)