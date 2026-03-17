/**
 * DevNet - script.js (Central Engine)
 * Organizado por funções para controle total do sistema Vanilla.
 */

// --- FUNÇÕES DO FEED (POSTAGEM UNIVERSAL) ---

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