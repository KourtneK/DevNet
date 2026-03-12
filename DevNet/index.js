const express = require('express');
const path = require('path');
const morgan = require('morgan');
const session = require('express-session'); // Para gerenciar o login
const passport = require('passport'); // Para a autenticação
const GitHubStrategy = require('passport-github2').Strategy; // Estratégia do GitHub

const app = express();
const port = 3000;

// --- MEMÓRIA TEMPORÁRIA PARA OS POSTS REAIS ---
let postsGlobais = [
    { 
        id: "1741720000000",
        usuario: "Sistema", 
        avatar: "https://github.com/github.png", 
        tipo: "texto",
        conteudo: "Bem-vindo à DevNet! Logue com seu GitHub para postar códigos, imagens e vídeos.", 
        linkMidia: "",
        data: "11/03/2026" 
    }
];

// --- CONFIGURAÇÕES DO SERVIOR (LOCAL) ---
app.use(morgan('dev'));
app.set('view engine', 'ejs');  // Define o motor de visualização para ejs
app.set('views', path.join(__dirname, 'views')); // Garante que o Express ache a pasta views
app.use(express.static(path.join(__dirname, 'public')));    // Middleware para arquivos estáticos (CSS, Imagens)
app.use(express.urlencoded({ extended: true }));    // Middleware para ler dados de formulários (Necessário para posts reais futuramente)

// --- CONFIGURAÇÃO DE AUTENTICAÇÃO (SESSÃO E PASSPORT) ---
app.use(session({
    secret: 'devnet-ifro-secret-key', // Chave de segurança para a sessão
    resave: false,
    saveUninitialized: false
}));

app.use(passport.initialize());
app.use(passport.session());

passport.use(new GitHubStrategy({
    clientID: 'Ov23lix91K8ckamWpusN', // id cliente
    clientSecret: 'e2e72d01f27e626158d2d82d536b1b4dcba5a68f', // id secreto cliente
    callbackURL: "http://localhost:3000/auth/github/callback"
  },
  function(accessToken, refreshToken, profile, done) {
    return done(null, profile);
  }
));

passport.serializeUser((user, done) => done(null, user));
passport.deserializeUser((obj, done) => done(null, obj));

// --- MIDDLEWARE DE USUÁRIO (EVITA O ERRO REFERENCEERROR) ---
app.use((req, res, next) => {
    res.locals.user = req.user || null;
    next();
});

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
    res.render('index', { paginaAtual: 'home' });   // User agora é automático!
});

app.get('/feed', (req, res) => {
    res.render('feed', { paginaAtual: 'feed', posts: postsGlobais });    // Posts ainda precisam ser passados
});

app.get('/perfil', (req, res) => {
    res.render('perfil', { paginaAtual: 'perfil' });    // Rota Perfil
});

app.get('/config', (req, res) => {
    res.render('config', { paginaAtual: 'config' });    // Rota Configurações
});

// --- ROTA PARA RECEBER POSTAGENS REAIS ---
app.post('/postar', (req, res) => {
    if (!req.isAuthenticated()) return res.redirect('/auth/github'); 

    const { conteudo, tipo, linkMidia } = req.body; // Pega os novos campos

    const novoPost = {
        id: Date.now().toString(), // Cria um ID único baseado no tempo
        usuario: req.user.username, 
        avatar: req.user._json.avatar_url,
        tipo: tipo || 'texto', // texto, codigo, imagem, video, repo
        conteudo: conteudo,
        linkMidia: linkMidia || '',
        data: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
    };

    postsGlobais.unshift(novoPost); 
    res.redirect('/feed');
});

// --- ROTA PARA DELETAR POSTS ---
app.post('/deletar/:id', (req, res) => {
    if (!req.isAuthenticated()) return res.redirect('/auth/github');

    const idPost = req.params.id;
    // Encontra o post e verifica se o usuário é o dono
    const post = postsGlobais.find(p => p.id === idPost);

    if (post && post.usuario === req.user.username) {
        postsGlobais = postsGlobais.filter(p => p.id !== idPost); // Remove o post da lista
    }

    res.redirect('/feed');
});

// --- INICIA O SERVIDOR ---
app.listen(port, () => {
    console.log(`🚀 DevNet rodando em http://localhost:${port}`);
    console.log('Pressione CTREL+C para parar o servidor'); 
});