from app import app
from config_banco import db, User, Post

def popular_banco():
    with app.app_context():
        # Lista de usuários de teste para validar a ordenação e busca
        usuarios_teste = [
            User(username="Alice_Dev", email="alice@exemplo.com", bio="C++ enthusiast 💻"),
            User(username="Zeno_Coder", email="zeno@ifro.edu.br", bio="Filosofia e Código"),
            User(username="Bruno_JS", email="bruno@js.com", bio="Vanilla JS only!"),
            User(username="Carla_Eng", email="carla@eng.com", bio="Hardware & Software"),
            User(username="Dev_IFRO", email="estudante@ifro.edu.br", bio="Rondônia Tech")
        ]
        
        try:
            for u in usuarios_teste:
                # Verifica se o usuário já existe para não dar erro de Unique
                if not User.query.filter_by(username=u.username).first():
                    db.session.add(u)
            
            db.session.commit()
            print("✅ 5 usuários de teste adicionados com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao popular banco: {e}")

if __name__ == "__main__":
    popular_banco()