# Stock & Roll

## Identificação
- Nome da aplicação: Stock & Roll
- Disciplina: Técnicas Avançadas de Programação Web
- Aluno: Luan de Oliveira Teixeira
- Descrição resumida: Sistema de gerenciamento de estoque para controlar produtos, categorias, fornecedores e movimentações de entrada e saída.

## Sobre o projeto
O problema que o Stock & Roll resolve é a dificuldade de pequenos negócios e escritórios em manter o cadastro de produtos e acompanhar com precisão as quantidades disponíveis e suas alterações.

O objetivo do sistema é centralizar o catálogo de produtos, categorias e fornecedores, oferecer um painel com visão geral do estoque e permitir o registro e acompanhamento das entradas e saídas de mercadorias.

Principais funcionalidades:
- Cadastro de produtos, categorias e fornecedores
- Visualização do estoque atual
- Registro de movimentações de entrada e saída, que atualizam automaticamente o saldo dos produtos
- Dashboard com indicadores de produtos ativos, categorias, estoque baixo e valor estimado do estoque
- CRUD completo para produtos e categorias
- Administração via Django Admin

## Tecnologias utilizadas
- Python
- Django
- SQLite
- HTML
- CSS

## Regras de negócio implementadas
1. Não é permitido registrar uma saída de estoque maior que a quantidade disponível em estoque.
2. O preço do produto deve ser maior que zero e a quantidade em estoque não pode ser negativa.
3. Produtos inativos não podem receber movimentações de estoque.
4. Movimentações registradas são tratadas como histórico: não podem ser editadas nem excluídas.
5. O saldo de produtos existentes é alterado por movimentações, não pela edição direta do produto.
6. No dashboard, os indicadores operacionais consideram apenas produtos ativos; o valor estimado do estoque inclui também os saldos de produtos inativos.

## Modelagem
O sistema possui quatro modelos relacionados: Categoria, Fornecedor, Produto e MovimentacaoEstoque. Produtos se relacionam com categorias e fornecedores, e as movimentações ficam vinculadas aos produtos. A aplicação Web oferece CRUD para produtos e categorias.

## Como executar
1. Crie um ambiente virtual e instale as dependências:
   ```bash
   python -m venv .venv
   ```
   No Linux, ative o ambiente virtual com:
   ```bash
   source .venv/bin/activate
   ```
   No Windows, use o comando correspondente ao terminal:
   ```powershell
   # PowerShell
   .venv\Scripts\Activate.ps1
   ```
   ```bat
   :: Prompt de Comando (cmd)
   .venv\Scripts\activate.bat
   ```
   Depois, instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Aplique as migrações:
   ```bash
   python manage.py migrate
   ```
3. Para acessar o Django Admin, crie uma conta de administrador:
   ```bash
   python manage.py createsuperuser
   ```
   Informe o nome de usuário e a senha quando solicitado. Essa conta é criada
   no banco local; cada pessoa define suas próprias credenciais. Não é necessário
   configurar `DJANGO_SECRET_KEY` para essa etapa.
4. Inicie o servidor:
   ```bash
   python manage.py runserver
   ```
5. Acesse:
   - http://127.0.0.1:8000/
   - http://127.0.0.1:8000/admin/

## Observações
- O projeto usa SQLite por padrão.
- A chave padrão do Django é apenas para desenvolvimento local; defina `DJANGO_SECRET_KEY` no ambiente para usar outra chave.
- O Django Admin foi configurado para permitir cadastro e filtro de categorias, produtos e movimentações.
