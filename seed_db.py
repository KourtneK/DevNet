import random
from app import app
from config_banco import db, User, Post

def popular_banco_em_massa(quantidade=99):
    with app.app_context():
        nomes = ["Lucas", "Marcos", "Julia", "Pedro", "Ana", "Dev", "Coder", "Syntax", "Null", "Root"]
        sufixos = ["_Rondonia", "_IFRO", "_Soberano", "_Vanilla", "_Hero", "01", "07", "XP", "Dev"]
        bios = [
            "Estudante de Engenharia no IFRO", 
            "Apaixonado por C++ e Hardware", 
            "Vanilla JS é vida!", 
            "Spiders and Insects enthusiast 🕷️",
            "Construindo meu próprio motor de jogo",
            "Soberania digital acima de tudo"
        ]

        print(f"🚀 Iniciando geração de {quantidade} usuários...")
        
        try:
            for i in range(quantidade):
                # Gera dados aleatórios para testar a ordenação alfabética
                username = f"{random.choice(nomes)}{random.choice(sufixos)}_{i}"
                email = f"user_{i}@devnet.edu.br"
                bio = random.choice(bios)
                # Adiciona o campo avatar_url para evitar o erro 500 que vimos
                avatar = f"https://api.dicebear.com/7.x/identicon/svg?seed={username}"
                
                # Verifica duplicatas antes de inserir
                if not User.query.filter_by(username=username).first():
                    novo_u = User(
                        username=username, 
                        email=email, 
                        bio=bio, 
                        avatar_url=avatar,
                        is_banned=random.choice([False, False, False, True]) # 25% de chance de teste de banido
                    )
                    db.session.add(novo_u)
            
            db.session.commit()
            print(f"✅ Banco de dados populado com {quantidade} usuários de teste!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro crítico no seed: {e}")

if __name__ == "__main__":
    popular_banco_em_massa(99)