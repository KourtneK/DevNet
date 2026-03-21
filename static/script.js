/**
 * DevNet - script.js (Central Engine)
 * Organizado por funções para controle total do sistema Vanilla.
 */

// --- FUNÇÕES DO FEED (POSTAGEM UNIVERSAL) ---

function avisarDesenvolvimento(recurso) {
    alert(`O sistema de ${recurso} está em desenvolvimento!`);
}

/* - Lógica de Visualização Simultânea */
function mostrarPreview(input, tipo) {
    const area = document.getElementById('preview-area');
    const img = document.getElementById('img-preview');
    const vid = document.getElementById('vid-preview');
    const text = document.getElementById('file-name-preview');

    if (input.files && input.files[0]) {
        area.style.display = 'block'; // Ativa o container principal
        const reader = new FileReader();

        if (tipo === 'image') {
            reader.onload = e => { 
                img.src = e.target.result; 
                img.style.display = 'block'; // Mostra sem ocultar os outros
            };
            reader.readAsDataURL(input.files[0]);
        } else if (tipo === 'video') {
            const url = URL.createObjectURL(input.files[0]);
            vid.src = url; 
            vid.style.display = 'block'; // Coexiste com a imagem e anexo
        } else {
            // Suporta qualquer extensão técnica (.ejs, .pdf, etc.)
            text.innerHTML = "📎 Arquivo: <strong>" + input.files[0].name + "</strong>";
            text.style.display = 'block'; 
        }
    }
}

// --- FUNÇÕES DO PERFIL (FILTRO DE REPOS) ---

function filtrarRepositorios() {
    const searchInput = document.getElementById('repo-search');
    const repoCards = document.querySelectorAll('.repo-card');

    if (!searchInput) return; // Só executa se o campo existir na página

    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();

        repoCards.forEach(card => {
            const repoName = card.querySelector('.repo-name').innerText.toLowerCase();
            const repoDesc = card.querySelector('.repo-desc').innerText.toLowerCase();

            if (repoName.includes(term) || repoDesc.includes(term)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    });
}

// --- INICIALIZAÇÃO AUTOMÁTICA ---

document.addEventListener('DOMContentLoaded', () => {
    // Dispara funções que precisam de listeners automáticos
    filtrarRepositorios();
    
    console.log("DevNet Engine: Sistema carregado e funções prontas. 🚀");
});

// Interagir com posts
async function interagirPost(postId, tipo) {
    try {
        const response = await fetch(`/interagir/${tipo}/${postId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok) {
            const data = await response.json();
            
            // Busca os spans específicos pelo ID único do post
            const likeSpan = document.getElementById(`likes-count-${postId}`);
            const dislikeSpan = document.getElementById(`dislikes-count-${postId}`);
            
            if (likeSpan) likeSpan.innerText = data.likes;
            if (dislikeSpan) dislikeSpan.innerText = data.dislikes;
            
            console.log(`DevNet Engine: ${tipo} registrado no post ${postId}`);
        } else {
            console.error("Erro na interação:", response.statusText);
        }
    } catch (error) {
        console.error("Erro de conexão com o motor:", error);
    }
}

// Compartilhamento
function copiarLink(postId) {
    // Constrói a URL usando o domínio atual + a rota de visualização
    const url = window.location.origin + '/ver_post/' + postId;

    navigator.clipboard.writeText(url).then(() => {
        // Feedback visual de UI/UX: Troca o texto do botão temporariamente
        const btn = document.getElementById(`btn-share-${postId}`);
        if (btn) {
            const originalHTML = btn.innerHTML;
            btn.innerHTML = "✅ Link Copiado!";
            btn.style.color = "var(--accent-green)";

            // Retorna ao estado original após 2 segundos
            setTimeout(() => {
                btn.innerHTML = originalHTML;
                btn.style.color = "";
            }, 2000);
        }
    }).catch(err => {
        console.error("Erro ao copiar o link:", err);
    });
}

function toggleComentario() {
    const area = document.getElementById('area-comentario');
    const campo = document.getElementById('campo-texto-comentario');
    
    // Vanilla puro: Se estiver escondido, mostra. Se estiver visível, esconde.
    if (area.style.display === 'none' || area.style.display === '') {
        area.style.display = 'block';
        campo.focus(); // Coloca o cursor no texto automaticamente
    } else {
        area.style.display = 'none';
    }
}

// Escutador de carregamento: Verifica se o usuário "quis" comentar vindo do feed
document.addEventListener('DOMContentLoaded', () => {
    // Se a URL terminar em #comentar, abre o formulário direto
    if (window.location.hash === '#comentar') {
        toggleComentario();
    }
    
    // Mantém suas outras inicializações
    filtrarRepositorios();
});