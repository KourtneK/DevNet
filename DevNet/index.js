const express = require('express');
const path = require('path');
const morgan = require('morgan');
const session = require('express-session');// Para gerenciar o login
const passport = require('passport'); // Para a autenticação
const GitHubStrategy = require('passport-github2').Strategy; // Estratégia do GitHub

const app = express();
const port = 3000;

// --- MEMÓRIA TEMPORÁRIA PARA OS POSTS REAIS ---
let postsGlobais = [
    { usuario: "Sistema", avatar: "https://github.com/github.png", conteudo: "Bem-vindo à DevNet! Logue com seu GitHub para postar.", data: "11/03/2026" }
];

// --- CONFIGURAÇÕES DO SERVIOR (LOCAL) ---
app.use(morgan('dev'));
app.set('view engine', 'ejs');   // Define o motor de visualização para ejs
app.set('views', path.join(__dirname, 'views'));    // Garante que o Express ache a pasta views
app.use(express.static(path.join(__dirname, 'public')));    // Middleware para arquivos estáticos (CSS, Imagens)
app.use(express.urlencoded({ extended: true }));    // Middleware para ler dados de formulários (Necessário para posts reais futuramente)

// --- CONFIGURAÇÃO DE AUTENTICAÇÃO (SESSÃO E PASSPORT) ---
app.use(session({
    secret: 'devnet-ifro-secret-key',   // Chave de segurança para a sessão
    resave: false,
    saveUninitialized: false
}));

app.use(passport.initialize());
app.use(passport.session());

// Configurando a estratégia com as suas chaves fornecidas
passport.use(new GitHubStrategy({
    clientID: 'Ov23lix91K8ckamWpusN',   // id cliente
    clientSecret: 'e2e72d01f27e626158d2d82d536b1b4dcba5a68f',   // id secreto cliente
    callbackURL: "http://localhost:3000/auth/github/callback"
  },
  function(accessToken, refreshToken, profile, done) {
    return done(null, profile);
  }
));

passport.serializeUser((user, done) => done(null, user));
passport.deserializeUser((obj, done) => done(null, obj));

// --- ROTAS DE LOGIN ---
app.get('/auth/github', passport.authenticate('github', { scope: [ 'user:email' ] }));

app.get('/auth/github/callback', 
  passport.authenticate('github', { failureRedirect: '/' }),
  (req, res) => res.redirect('/feed')
);

app.get('/logout', (req, res) => {
  req.logout(() => res.redirect('/'));
});

// --- ROTAS DA DEVNET ---

app.get('/', (req, res) => {
    res.render('index', { paginaAtual: 'home', user: req.user });   // Rota Home
});

app.get('/feed', (req, res) => {
    res.render('feed', { paginaAtual: 'feed', user: req.user, posts: postsGlobais });   // Rota Feed agora envia os posts e os dados do usuário logado 
});

app.get('/perfil', (req, res) => {
    res.render('perfil', { paginaAtual: 'perfil', user: req.user });    // Rota Perfil
});

app.get('/config', (req, res) => {
    res.render('config', { paginaAtual: 'config', user: req.user });    // Rota Configurações
});

// --- ROTA PARA RECEBER POSTAGENS REAIS ---
app.post('/postar', (req, res) => {
    if (!req.isAuthenticated()) return res.redirect('/auth/github'); // Só posta se estiver logado

    const novoPost = {
        usuario: req.user.username,     // Puxa o nome de usuário real do GitHub
        avatar: req.user._json.avatar_url,    // Puxa a foto do GitHub
        conteudo: req.body.conteudo,    // Puxa o que foi escrito no textarea
        data: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
    };

    postsGlobais.unshift(novoPost);     // Adiciona no início da lista
    res.redirect('/feed');      // Volta para o feed
});

// --- INICIA O SERVIDOR ---
app.listen(port, () => {
    console.log(`🚀 DevNet rodando em http://localhost:${port}`);
    console.log('Pressione CTREL+C para parar o servidor'); //
});