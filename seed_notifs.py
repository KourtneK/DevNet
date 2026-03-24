from app import app
from config_banco import db, Notification, User, Post

def semear_notificacoes():
    with app.app_context():
        # 1. Busca o seu usuário (ajuste o username para o seu do GitHub)
        meu_usuario = User.query.filter_by(username='KourtneK').first()
        
        if not meu_usuario:
            print("❌ Erro: Usuário 'KourtneK' não encontrado no banco.")
            return

        # 2. Busca um post qualquer para vincular à notificação
        post_exemplo = Post.query.first()
        post_id = post_exemplo.id if post_exemplo else None

        print(f"🚀 Semeando notificações para: {meu_usuario.username} (ID: {meu_usuario.id})")

        # 3. Cria notificações de teste
        notifs = [
            Notification(recipient_id=meu_usuario.id, sender_id=meu_usuario.id, type='comment', post_id=post_id),
            Notification(recipient_id=meu_usuario.id, sender_id=meu_usuario.id, type='like', post_id=post_id),
            Notification(recipient_id=meu_usuario.id, sender_id=meu_usuario.id, type='mention', post_id=post_id)
        ]

        # 4. Limpa notificações antigas para não poluir (opcional)
        Notification.query.filter_by(recipient_id=meu_usuario.id).delete()
        
        # 5. Salva no devnet.db
        db.session.add_all(notifs)
        db.session.commit()
        
        print(f"✅ Sucesso! 3 notificações fakes criadas para o post {post_id}.")

if __name__ == "__main__":
    semear_notificacoes()