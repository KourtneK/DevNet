from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_cors import CORS
from config_banco import db, User, Post, Interaction, Comment, CommentInteraction, Notification
from dotenv import load_dotenv
import os
import requests
from sqlalchemy import or_
import mimetypes
from werkzeug.utils import secure_filename
from datetime import *
import re
from markupsafe import Markup
from social import social_bp

# =========================================================
# 1. CONFIGURAÇÕES INICIAIS E AMBIENTE
# =========================================================

# Carrega as variáveis sensíveis (Client ID, Secret, Flask Key) do ficheiro .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuração do caminho absoluto para o banco de dados SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'devnet.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=3650)

# Inicialização do Banco de Dados
db.init_app(app)
app.register_blueprint(social_bp)

with app.app_context():
    db.create_all() # Garante que as tabelas User e Post sejam criadas

# Configuração de Uploads e Prevenção de Erros de Diretório
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# CRITICAL: Cria a pasta se ela não existir para evitar FileNotFoundError
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) 

# Configurações OAuth do GitHub e Whitelist de Admins
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
ADMINS_AUTORIZADOS = [
    'lucasdanielrocha2009@gmail.com',
]

# =========================================================
# 2. SISTEMA DE AUTENTICAÇÃO (GITHUB OAUTH)
# =========================================================

@app.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('feed')) 
    return render_template('login.html')

@app.route('/login/github')
def login_github():
    if 'user_id' in session:
        return redirect(url_for('feed'))
    # Redireciona para o GitHub solicitando acesso ao e-mail
    github_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=user:email"
    return redirect(github_url)

@app.route('/login/github/callback')
def github_callback():
    code = request.args.get('code')
    
    # 1. Troca o código temporário pelo Access Token
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

    # 2. Recupera dados do perfil (Username, Avatar, Bio)
    user_data = requests.get(
        'https://api.github.com/user',
        headers={'Authorization': f'token {access_token}'}
    ).json()

    # 3. Recupera o e-mail primário verificado
    emails_resp = requests.get(
        'https://api.github.com/user/emails',
        headers={'Authorization': f'token {access_token}'}
    ).json()
    github_email = next((e['email'] for e in emails_resp if e['primary']), None)

    github_username = user_data.get('login')
    github_avatar = user_data.get('avatar_url')
    github_bio = user_data.get('bio')

    # 4. Sincronização com o Banco de Dados
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
        if not user.bio:
            user.bio = github_bio

    db.session.commit()
    
    # 5. PERSISTÊNCIA ATIVADA
    # Isso impede o logout automático ao reiniciar o servidor
    session.permanent = True 
    session['user_id'] = user.id
    session['username'] = user.username
    session['access_token'] = access_token
    
    return redirect(url_for('feed'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# =========================================================
# 3. MOTOR SOCIAL (FEED E POSTAGEM UNIVERSAL)
# =========================================================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/feed')
def feed():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Busca posts ordenados do mais recente para o mais antigo
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    # Envia a lista para o Jinja2 (Resolve o erro UndefinedError)
    return render_template('feed.html', posts=posts)

@app.route('/postar', methods=['POST'])
def criar_post():
    user_id = session.get('user_id')
    if not user_id: return redirect(url_for('login'))

    texto = request.form.get('content')
    codigo = request.form.get('code_content')
    
    # Instancia o post único que receberá todos os dados de uma vez
    novo_post = Post(content=texto, code_content=codigo, user_id=user_id)

    # Motor de Upload Universal: Aceita qualquer extensão existente
    for key in ['image', 'video', 'attachment']:
        file = request.files.get(key)
        if file and file.filename != '':
            ext = os.path.splitext(file.filename)[1].lower()
            
            if ext: # Validação agnóstica de extensão [.pdf, .ejs, .dguiourawjdnfjqwn, etc]
                filename = secure_filename(f"{user_id}_{datetime.now().timestamp()}{ext}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                
                if key == 'image': novo_post.image_path = filename
                elif key == 'video': novo_post.video_path = filename
                else: 
                    novo_post.file_path = filename
                    novo_post.file_extension = ext

    db.session.add(novo_post)
    db.session.commit()
    return redirect(url_for('feed'))

@app.route('/post')
def post_view():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('post.html')

# deletar post
@app.route('/deletar_post/<int:post_id>', methods=['POST'])
def deletar_post(post_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    post = db.session.get(Post, post_id)

    if post and post.user_id == user_id:
        # Lista os possíveis caminhos de arquivos atrelados ao post
        arquivos_para_deletar = [post.image_path, post.video_path, post.file_path]
        
        for nome_arquivo in arquivos_para_deletar:
            if nome_arquivo:
                caminho_completo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
                if os.path.exists(caminho_completo):
                    os.remove(caminho_completo) # Deleta o arquivo do disco
        
        #deleta do banco de dados
        db.session.delete(post)
        db.session.commit()
    
    return redirect(url_for('feed'))

@app.route('/ver_post/<int:post_id>')
def ver_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Busca o post específico no banco usando o ID da URL
    post = db.session.get(Post, post_id)
    
    if not post:
        return "Post não encontrado", 404
        
    # Carrega o molde exclusivo para um único post
    return render_template('post_detalhe.html', post=post)

# =========================================================
# 4. PERFIL E CONFIGURAÇÕES
# =========================================================

@app.route('/config')
def config_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    user = db.session.get(User, user_id)
    return render_template('config.html', user=user)

# =========================================================
# 5. PAINEL ADMINISTRATIVO (CENTRAL DE COMANDO)
# =========================================================

@app.route('/admin')
def admin_panel():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user_admin = db.session.get(User, user_id)
    # A TRANCA: Só entra se estiver logado e na lista autorizada
    if not user_admin or user_admin.email not in ADMINS_AUTORIZADOS:
        return "<h1>Acesso Negado</h1>", 403

    # Captura parâmetros do Motor de Busca e Ordenação
    search_query = request.args.get('q', '')
    sort_option = request.args.get('sort', 'id_asc')

    query = User.query
    if search_query:
        # Busca Híbrida Inteligente: Identifica IDs numéricos ou texto
        if search_query.isdigit():
            query = query.filter(or_(User.id == int(search_query), 
                                     User.username.contains(search_query), 
                                     User.email.contains(search_query)))
        else:
            query = query.filter(or_(User.username.contains(search_query), 
                                     User.email.contains(search_query)))

    # Motor de Ordenação de Dados
    if sort_option == 'alpha_asc':
        query = query.order_by(User.username.asc())
    elif sort_option == 'alpha_desc':
        query = query.order_by(User.username.desc())
    elif sort_option == 'id_desc':
        query = query.order_by(User.id.desc())
    else: 
        query = query.order_by(User.id.asc())

    todos_usuarios = query.all()
    todos_posts = Post.query.all()

    return render_template('painel-adm.html', 
                           usuarios=todos_usuarios, 
                           posts=todos_posts,
                           admin=user_admin,
                           search_query=search_query,
                           sort_option=sort_option)

@app.route('/admin/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    user_id = session.get('user_id')
    user_admin = db.session.get(User, user_id)
    
    if not user_admin or user_admin.email not in ADMINS_AUTORIZADOS:
        return "Acesso negado", 403

    user_to_delete = db.session.get(User, id)
    if user_to_delete:
        # A remoção limpa posts automaticamente via relacionamento backref
        db.session.delete(user_to_delete)
        db.session.commit()
    
    return redirect(url_for('admin_panel'))

def criar_notificacao(destinatario_id, remetente_id, post_id, tipo):
    if destinatario_id == remetente_id:
        return
    nova_notif = Notification(
        recipient_id=destinatario_id,
        sender_id=remetente_id,
        post_id=post_id,
        type=tipo
    )
    db.session.add(nova_notif)
    db.session.commit()

# =========================================================
# 6. UTILITÁRIOS E INICIALIZAÇÃO
# =========================================================

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.template_filter('mentions')
def highlight_mentions(text):
    mention_pattern = r'@(\w+)'
    replacement = r'<span style="color: var(--accent-perfil); font-weight: bold;">\1</span>'
    processed_text = re.sub(mention_pattern, replacement, text)
    return Markup(processed_text)

@app.context_processor
def inject_notifications():
    if 'user_id' in session:
        count = Notification.query.filter_by(
            recipient_id=session['user_id'], 
            is_read=False
        ).count()
        return dict(notif_count=count)
    return dict(notif_count=0)

if __name__ == '__main__':
    print("✅   SERVIDOR DE-NET RODANDO NA PORTA 3000")
    print("⚠️    APERTE CTREL+C PARA PARAR O MOTOR")
    app.run(host='localhost', port=3000, debug=True)