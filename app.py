from flask import Flask, render_template     #importa o flask
from flask_cors import CORS     #importa o flask cors
from config_banco import db, User, Post     # Importa o banco e os modelos

app = Flask(__name__)

# Habilita CORS para permitir requisições de diferentes origens
CORS(app)

# Configura o nome do arquivo do banco de dados exatamente como solicitado
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///devnet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '35798081'

# Inicializa o banco de dados com as configurações do app
db.init_app(app)

# Cria o arquivo devnet.db e as tabelas automaticamente se não existirem
with app.app_context():
    db.create_all()

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