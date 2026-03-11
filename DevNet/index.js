const express = require('express');
const path = require('path');
const morgan = require('morgan');
const app = express();
const port = 3000;

// Configurações do Servidor
app.use(morgan('dev'));
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views')); // Garante que o Express ache a pasta views

// Middleware para arquivos estáticos (CSS, Imagens)
app.use(express.static(path.join(__dirname, 'public')));

// Middleware para ler dados de formulários (Necessário para posts reais futuramente)
app.use(express.urlencoded({ extended: true }));

// --- ROTAS DA DEVNET ---

// Rota Home
app.get('/', (req, res) => {
    res.render('index', { paginaAtual: 'home' });
});

// Rota Feed
app.get('/feed', (req, res) => {
    res.render('feed', { paginaAtual: 'feed' });
});

// Rota Perfil
app.get('/perfil', (req, res) => {
    res.render('perfil', { paginaAtual: 'perfil' });
});

// Rota Configurações
app.get('/config', (req, res) => {
    res.render('config', { paginaAtual: 'config' });
});

// Inicia o servidor
app.listen(port, () => {
    console.log(`🚀 DevNet rodando em http://localhost:${port}`);
    console.log('Pressione CTRL+C para parar o servidor');
});