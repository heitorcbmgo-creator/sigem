# 🔥 SIGEM - Sistema de Gestão de Missões

** Um projeto amador em desenvolvimento para o Corpo de Bombeiros Militar do Estado de Goiás - 1º Ten Heitor Braga de Paula**

Sistema para gerenciamento de missões, designações e avaliação de carga de trabalho dos oficiais.

---

## 📋 Requisitos

- Python 3.10+
- PostgreSQL 14+
- WSL/Ubuntu (recomendado para Windows)

---

## 🚀 Instalação

### 1. Clone ou copie o projeto para sua máquina

```bash
cd ~
# Se já tiver a pasta sigem, entre nela
cd sigem
```

### 2. Crie e ative o ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install django psycopg2-binary pillow django-htmx python-decouple openpyxl
```

### 4. Configure o banco de dados

Certifique-se de que o PostgreSQL está rodando:
```bash
sudo service postgresql start
```

O banco `sigem` já deve existir (criado na etapa anterior).

### 5. Execute as migrações

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crie um superusuário

```bash
python manage.py createsuperuser
```
- CPF: digite um CPF (apenas números, ex: 12345678900)
- Senha: escolha uma senha

### 7. Inicie o servidor

```bash
python manage.py runserver
```

Acesse: **http://127.0.0.1:8000**

---

## 📱 Páginas do Sistema

| URL | Página | Descrição |
|-----|--------|-----------|
| `/` | Login | Autenticação por CPF |
| `/dashboard/` | Visão Geral | Dashboard com métricas |
| `/comparar/` | Comparar Oficiais | Comparação de carga de trabalho |
| `/missoes/` | Missões | Dashboard de missões + organograma |
| `/painel/` | Painel do Oficial | Área pessoal do oficial |
| `/admin-painel/` | Administração | CRUD completo (apenas gestores) |
| `/admin/` | Django Admin | Admin nativo do Django |

---

## 👥 Perfis de Acesso

| Perfil | Permissões |
|--------|------------|
| **admin** | Acesso total ao sistema |
| **gestor** | CRUD de oficiais, missões, designações |
| **comandante** | Visualização e relatórios da unidade |
| **oficial** | Apenas visualização do próprio painel |

---

## 🗄️ Estrutura do Banco

### Tabelas Principais

- **Oficial**: Dados dos oficiais (nome, posto, quadro, OBM, etc.)
- **Missao**: Missões/operações (tipo, status, local, período)
- **Designacao**: Vínculo oficial ↔ missão (função, complexidade)
- **Unidade**: OBMs e estrutura hierárquica
- **Usuario**: Autenticação (login por CPF)
- **SolicitacaoDesignacao**: Pedidos de inclusão feitos pelos oficiais

---

## 🔧 Comandos Úteis

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Rodar servidor
python manage.py runserver

# Criar migrações após alterar models
python manage.py makemigrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos (para produção)
python manage.py collectstatic

# Shell do Django
python manage.py shell
```

---

## 📁 Estrutura de Pastas

```
sigem/
├── core/                   # Configurações do Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── missoes/                # App principal
│   ├── models.py           # Modelos do banco
│   ├── views.py            # Lógica das páginas
│   ├── urls.py             # Rotas
│   └── admin.py            # Config do Django Admin
├── templates/              # Templates HTML
│   ├── base.html           # Template base
│   ├── auth/               # Login
│   ├── pages/              # Páginas principais
│   └── htmx/               # Componentes HTMX
├── static/                 # CSS, JS, Imagens
│   ├── css/
│   └── img/
├── media/                  # Uploads (fotos)
├── .env                    # Variáveis de ambiente
├── manage.py
└── README.md
```

---

## 🎨 Tecnologias

- **Backend**: Django 5.x
- **Frontend**: HTML + HTMX + CSS customizado
- **Banco**: PostgreSQL
- **Ícones**: Lucide Icons
- **Fontes**: Inter + Oswald (Google Fonts)

---

## 📞 Suporte

Desenvolvido para o **CBMGO** - Corpo de Bombeiros Militar do Estado de Goiás.

**"Vidas Alheias e Riquezas Salvar"** 🔥
