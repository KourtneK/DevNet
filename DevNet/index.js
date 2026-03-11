const express = require('express');     // importa o express
const path = require('path');   //importa o path para mexer com caminhos de arquivos
const morgan = require('morgan');
const app = express();  // inicializa o express
const port = 3000 //em qual porta o servidor ira rodar

app.use(morgan('dev'));     //depuração

app.use(express.static(path.join(__dirname, 'public')));    //configura o express para servir arquivos estaticos da pasta public

//inicia o servidor
app.listen(port, () => {
    console.log(`Servidor rodando em http://localhost:${port}`);
    console.log('Use CTREL+C para parar o servidor');
});