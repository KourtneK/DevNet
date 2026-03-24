from flask import Blueprint, request, session, redirect, url_for, render_template
import requests
import os
from config_banco import db, User, Post, Interaction, Comment, CommentInteraction, Notification

social_bp = Blueprint('social', __name__)

# --- PERFIL E CONFIGURAÇÕES ---

@social_bp.route('/perfil')
def perfil():
    user_id = session.get('user_id')
    token = session.get('access_token')
    if not user_id or not token:
        return redirect(url_for('login'))

    user = db.session.get(User, user_id)
    
    # Importa a lista de admins do app principal
    from app import ADMINS_AUTORIZADOS
    is_admin = (user.email in ADMINS_AUTORIZADOS)

    # Busca repositórios para exibir no perfil
    repos_resp = requests.get(
        'https://api.github.com/user/repos?type=owner&sort=updated',
        headers={'Authorization': f'token {token}'}
    ).json()

    return render_template('perfil.html', user=user, is_admin=is_admin, repos=repos_resp)

@social_bp.route('/update_bio', methods=['POST'])
def update_bio():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    user = db.session.get(User, user_id)
    if user:
        user.bio = request.form.get('bio')
        db.session.commit()
    return redirect(url_for('social.perfil'))

# --- INTERAÇÕES EM POSTS (LIKE/DISLIKE) ---

@social_bp.route('/interagir/<string:tipo>/<int:post_id>', methods=['POST'])
def interagir(tipo, post_id):
    user_id = session.get('user_id')
    if not user_id:
        return {"erro": "Não autorizado"}, 401

    post = db.session.get(Post, post_id)
    if not post:
        return {"erro": "Post não encontrado"}, 404

    existente = Interaction.query.filter_by(user_id=user_id, post_id=post_id).first()

    if existente:
        if existente.type == tipo:
            db.session.delete(existente)
        else:
            existente.type = tipo
    else:
        nova = Interaction(user_id=user_id, post_id=post_id, type=tipo)
        db.session.add(nova)
        
        # Notifica o autor do post (exceto se for o próprio autor)
        from app import criar_notificacao
        criar_notificacao(post.user_id, user_id, post_id, tipo)

    db.session.commit()
    
    # Atualiza contadores
    post.likes = Interaction.query.filter_by(post_id=post_id, type='like').count()
    post.dislikes = Interaction.query.filter_by(post_id=post_id, type='dislike').count()
    db.session.commit()

    return {"likes": post.likes, "dislikes": post.dislikes}

# --- COMENTÁRIOS E RESPOSTAS ---

@social_bp.route('/comentar/<int:post_id>', methods=['POST'])
def comentar(post_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    conteudo = request.form.get('comment_text')
    codigo = request.form.get('comment_code')
    parent_id = request.form.get('parent_id') # Para o sistema de threads
    
    if conteudo:
        novo = Comment(
            content=conteudo, 
            code_content=codigo, 
            user_id=user_id, 
            post_id=post_id,
            parent_id=parent_id
        )
        db.session.add(novo)
        db.session.commit()
        
        # Notifica o dono do post
        from app import criar_notificacao
        post = db.session.get(Post, post_id)
        criar_notificacao(post.user_id, user_id, post_id, 'comment')
        
    return redirect(url_for('ver_post', post_id=post_id))

@social_bp.route('/interagir_comentario/<string:tipo>/<int:comment_id>', methods=['POST'])
def interagir_comentario(tipo, comment_id):
    user_id = session.get('user_id')
    if not user_id:
        return {"erro": "Não autorizado"}, 401
    
    comentario = db.session.get(Comment, comment_id)
    if not comentario:
        return {"erro": "Comentário não encontrado"}, 404
        
    existente = CommentInteraction.query.filter_by(user_id=user_id, comment_id=comment_id).first()
    
    if existente:
        if existente.type == tipo:
            db.session.delete(existente)
        else:
            existente.type = tipo
    else:
        nova = CommentInteraction(user_id=user_id, comment_id=comment_id, type=tipo)
        db.session.add(nova)
        
    db.session.commit()
    
    # Recalcula likes/dislikes do comentário
    comentario.likes = CommentInteraction.query.filter_by(comment_id=comment_id, type='like').count()
    comentario.dislikes = CommentInteraction.query.filter_by(comment_id=comment_id, type='dislike').count()
    db.session.commit()
    
    return {"likes": comentario.likes, "dislikes": comentario.dislikes}

# --- SISTEMA DE NOTIFICAÇÕES (APIs) ---

@social_bp.route('/api/notifications')
def get_notifications():
    user_id = session.get('user_id')
    if not user_id:
        return {"erro": "Não autorizado"}, 401
        
    notifs = Notification.query.filter_by(recipient_id=user_id)\
                               .order_by(Notification.date_created.desc())\
                               .limit(10).all()
    output = []
    for n in notifs:
        output.append({
            "id": n.id,
            "sender": n.sender.username,
            "type": n.type,
            "post_id": n.post_id,
            "is_read": n.is_read
        })
    return {"notifications": output}

@social_bp.route('/api/notifications/read', methods=['POST'])
def mark_read():
    user_id = session.get('user_id')
    if not user_id:
        return {"erro": "Não autorizado"}, 401
    
    Notification.query.filter_by(recipient_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return {"status": "ok"}

@social_bp.route('/api/notifications/clear', methods=['POST'])
def clear_notifications():
    user_id = session.get('user_id')
    if not user_id:
        return {"erro": "Não autorizado"}, 401
    
    Notification.query.filter_by(recipient_id=user_id).delete()
    db.session.commit()
    return {"status": "limpo"}