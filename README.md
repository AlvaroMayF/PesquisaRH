Sistema de Pesquisa de Clima Organizacional - Rede Hospitalar Samar
Este repositório contém o código-fonte da aplicação web desenvolvida para automatizar a coleta, o processamento e a análise da Pesquisa de Clima Organizacional da Rede Hospitalar Samar.

Status do Projeto: Versão 1.0 - Em Produção

📜 Sobre o Projeto
O Sistema de Pesquisa de Clima Organizacional é uma ferramenta estratégica que visa substituir processos manuais, garantir o total anonimato dos colaboradores e fornecer à gestão dados estruturados e visuais para apoiar a tomada de decisões.

Confira a documentação interativa completa: Clique aqui para ver a apresentação do sistema
(Nota: Substitua os placeholders acima após hospedar a apresentação HTML com o GitHub Pages)

✨ Funcionalidades Principais (v1.0)
O sistema é dividido em dois fluxos principais:

👤 Fluxo do Colaborador
Autenticação Segura: Login via CPF e Data de Nascimento.

Validação de Acesso: Permite o acesso apenas para colaboradores cadastrados que ainda não responderam.

Formulário Dinâmico: As perguntas são carregadas diretamente do banco de dados.

Garantia de Anonimato: As respostas são salvas sem qualquer vínculo com a identidade do colaborador.

ադ Fluxo do Administrador
Dashboard Analítico: Painel com a taxa de adesão em tempo real e resultados agregados.

Visualização de Dados: Gráficos interativos (pizza, barras) para análise quantitativa.

Análise Qualitativa: Listagem anônima das respostas de texto aberto.

Gerenciamento de Colaboradores (CRUD): Interface completa para adicionar, editar e desativar participantes.

🚀 Tecnologias Utilizadas
Backend: Python 3 com Flask

Frontend: HTML5, CSS3 (com Tailwind CSS), JavaScript

Banco de Dados: MySQL

Ambiente Virtual: venv

Dependências: (Listadas em requirements.txt)

⚙️ Como Rodar o Projeto Localmente
Siga os passos abaixo para configurar e executar o projeto em sua máquina.

Pré-requisitos
Python 3.x instalado

Git instalado

Um servidor de banco de dados MySQL rodando

1. Clonar o Repositório
git clone https://github.com/[SEU-USUARIO-GITHUB]/[NOME-DO-REPOSITORIO].git
cd [NOME-DO-REPOSITORIO]

2. Configurar o Ambiente Virtual
É uma boa prática usar um ambiente virtual para isolar as dependências do projeto.

# Criar o ambiente virtual
python -m venv venv

# Ativar o ambiente virtual
# No Windows:
venv\Scripts\activate
# No macOS/Linux:
source venv/bin/activate

3. Instalar as Dependências
Com o ambiente virtual ativado, instale todas as bibliotecas necessárias.

pip install -r requirements.txt

(Nota: Certifique-se de que você tem um arquivo requirements.txt com todas as dependências, como Flask, mysql-connector-python, etc.)

4. Configurar o Banco de Dados
Crie um banco de dados no seu servidor MySQL (ex: pesquisa_rh).

Importe a estrutura das tabelas (você pode usar um script SQL de dump do seu banco de desenvolvimento).

Configure as variáveis de ambiente. Crie um arquivo .env na raiz do projeto com as suas credenciais:

DB_HOST=localhost
DB_USER=seu_usuario_mysql
DB_PASSWORD=sua_senha_mysql
DB_NAME=pesquisa_rh

5. Executar a Aplicação
Execute o comando abaixo para iniciar o servidor de desenvolvimento do Flask.

flask run

A aplicação estará disponível em http://127.0.0.1:5000 (ou o endereço que aparecer no seu terminal).

🤝 Contribuições
Este projeto está atualmente em desenvolvimento ativo. Para contribuir, por favor, crie uma nova branch, faça suas alterações e abra um Pull Request para revisão.

📄 Licença
Este projeto é de propriedade da Rede Hospitalar Samar. Todos os direitos reservados.