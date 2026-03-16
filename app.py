from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_cors import CORS
from config_banco import db, User, Post
from dotenv import load_dotenv
import os
import requests
from sqlalchemy import or_

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
ADMINS_AUTORIZADOS = [
    'lucasdanielrocha2009@gmail.com',
]

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

    # 2. Pega os dados básicos (username, avatar, bio)
    user_data = requests.get(
        'https://api.github.com/user',
        headers={'Authorization': f'token {access_token}'}
    ).json()

    # 3. Pega o e-mail real do endpoint privado
    emails_resp = requests.get(
        'https://api.github.com/user/emails',
        headers={'Authorization': f'token {access_token}'}
    ).json()
    github_email = next((e['email'] for e in emails_resp if e['primary']), None)

    github_username = user_data.get('login')
    github_avatar = user_data.get('avatar_url')
    github_bio = user_data.get('bio')

    # 4. Sincroniza com o banco de dados
    user = User.query.filter_by(username=github_username).first()

    if not user:
        user = User(
            username=github_username, 
            email=github_email,
            avatar_url=github_avatar,
            bio=github_bio
        )
        db.session.add(user)
    else:
        user.email = github_email
        user.avatar_url = github_avatar
        user.bio = github_bio
    
    db.session.commit()
    
    # Salva na sessão para as rotas e o menu
    session['user_id'] = user.id
    session['username'] = user.username
    session['access_token'] = access_token
    
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
    user_id = session.get('user_id')
    token = session.get('access_token') 
    
    if not user_id or not token:
        return redirect(url_for('login'))

    user = db.session.get(User, user_id)
    is_admin = (user.email in ADMINS_AUTORIZADOS)

    # Faz a chamada para a API do GitHub buscando os repositórios do dono da conta
    repos_resp = requests.get(
        'https://api.github.com/user/repos?type=owner&sort=updated',
        headers={'Authorization': f'token {token}'}
    ).json()

    return render_template('perfil.html', user=user, is_admin=is_admin, repos=repos_resp)

@app.route('/config')
def config_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Busca o usuário para preencher o formulário
    user = db.session.get(User, user_id)
    return render_template('config.html', user=user)

# =========================
#    PAINEL ADMIN
# =========================

@app.route('/admin')
def admin_panel():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user_admin = db.session.get(User, user_id)
    if not user_admin or user_admin.email not in ADMINS_AUTORIZADOS:
        return "<h1>Acesso Negado</h1>", 403

    # Captura parâmetros de busca e ordenação
    search_query = request.args.get('q', '')
    sort_option = request.args.get('sort', 'id_asc')

    # Lógica de Busca: ID, Nome ou Email
    query = User.query
    if search_query:
        # Tenta converter para int se for pesquisa por ID, senão pesquisa texto
        if search_query.isdigit():
            query = query.filter(or_(User.id == int(search_query), 
                                     User.username.contains(search_query), 
                                     User.email.contains(search_query)))
        else:
            query = query.filter(or_(User.username.contains(search_query), 
                                     User.email.contains(search_query)))

    # Lógica de Ordenação
    if sort_option == 'alpha_asc':
        query = query.order_by(User.username.asc())
    elif sort_option == 'alpha_desc':
        query = query.order_by(User.username.desc())
    elif sort_option == 'id_desc':
        query = query.order_by(User.id.desc())
    else: # id_asc (Padrão: ordem de adição/numérica)
        query = query.order_by(User.id.asc())

    todos_usuarios = query.all()
    todos_posts = Post.query.all()

    return render_template('painel-adm.html', 
                           usuarios=todos_usuarios, 
                           posts=todos_posts,
                           admin=user_admin,
                           search_query=search_query,
                           sort_option=sort_option)

# NOVA ROTA: Deletar Usuário
@app.route('/admin/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    user_id = session.get('user_id')
    user_admin = db.session.get(User, user_id)
    
    if not user_admin or user_admin.email not in ADMINS_AUTORIZADOS:
        return "Acesso negado", 403

    user_to_delete = db.session.get(User, id)
    if user_to_delete:
        # Note: Isso também deletará os posts do usuário devido ao backref/relacionamento
        db.session.delete(user_to_delete)
        db.session.commit()
    
    return redirect(url_for('admin_panel'))


@app.route('/update_bio', methods=['POST'])
def update_bio():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Pega o texto enviado pelo formulário
    nova_bio = request.form.get('bio')
    
    # Busca o usuário e atualiza
    user = db.session.get(User, user_id)
    if user:
        user.bio = nova_bio # Se vier vazio, o banco salva como string vazia ou nulo
        db.session.commit()
    
    return redirect(url_for('perfil'))


# fav icon pra parar de dar erro desnecessario
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    print("✅   SERVIDOR RODANDO NA PORTA 3000")
    print("⚠️    APERTE CTREL+C PARA PARAR O SERVIDOR")
    app.run(host='localhost', port=3000, debug=True)