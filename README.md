# 🔥 SIGEM - Sistema de Gestão de Missões

** Um projeto amador em desenvolvimento para o Corpo de Bombeiros Militar do Estado de Goiás - 1º Ten Heitor Braga de Paula**

Sistema para gerenciamento de missões, designações e avaliação de carga de trabalho dos oficiais.

🌐 **Produção**: https://sigem.onrender.com

---

## 📋 Índice

- [Funcionalidades](#-funcionalidades)
- [Requisitos](#-requisitos)
- [Instalação Local](#-instalação-local)
- [Deploy em Produção](#-deploy-em-produção)
- [Páginas do Sistema](#-páginas-do-sistema)
- [Perfis de Acesso](#-perfis-de-acesso)
- [Estrutura do Banco](#️-estrutura-do-banco)
- [Tecnologias](#-tecnologias)

---

## ✨ Funcionalidades

### 📊 Dashboard (Visão Geral)
- KPIs em tempo real: oficiais ativos, missões ativas, taxa de ocupação, carga média
- Gráficos interativos com Chart.js
- Evolução mensal de missões (12 meses)
- Distribuição por tipo, posto e quadro
- Monitoramento de oficiais sob maior demanda (com indicadores de status)
- Sistema de alertas automáticos (crítico, alto, médio)
- Tooltips explicativos em cada gráfico/card
- Filtros por OBM para comandantes

### 👥 Gestão de Oficiais
- Cadastro completo com foto
- Filtros por posto, quadro, OBM e status
- Importação em massa via Excel
- Exportação para Excel e PDF
- Visualização de carga de trabalho individual

### 📁 Gestão de Missões
- Tipos: Operacional, Administrativa, Ensino, Correicional, Comissão, Ação Social
- Status: Planejada, Em Andamento, Concluída, Cancelada
- Organograma visual dos designados
- Controle de período e documentação (SEI)

### 🔗 Gestão de Designações
- Vinculação oficial ↔ missão
- Funções: Comandante, Subcomandante, Coordenador, Presidente, Encarregado, Membro
- Complexidade: Baixa (peso 1), Média (peso 2), Alta (peso 3)
- Cálculo automático de carga ponderada

### 📝 Sistema de Solicitações
- **Solicitação de Missão**: oficial solicita criação de nova missão
  - Campos: nome, tipo, status, local, período, nº SEI
- **Solicitação de Designação**: oficial solicita inclusão em missão existente
  - Campos: missão (lista), função, nº SEI/BG
  - Complexidade definida pela BM/3 na aprovação
- Fluxo de aprovação pelo Admin/BM/3
- Edição de solicitações antes da aprovação
- Campo de observações para justificativas
- Criação automática de missão/designação na aprovação
- Histórico de solicitações ("Minhas Solicitações")

### 🏢 Gestão de Unidades (OBMs)
- Estrutura hierárquica (CBMGO > CRBMs > BBMs > Cias)
- Importação em massa via Excel
- Níveis: Geral, CRBM, BBM, Companhia

### 👤 Gestão de Usuários
- Autenticação por CPF
- Vinculação automática com oficial
- Reset de senha pelo admin
- Múltiplos perfis de acesso

### 📥 Importação/Exportação
- Importação de oficiais, missões, designações e unidades via Excel
- Planilha modelo disponível para download
- Exportação para Excel com formatação profissional
- Exportação para PDF

---

## 📋 Requisitos

### Desenvolvimento Local
- Python 3.10+
- PostgreSQL 14+ (ou SQLite para testes)
- pip (gerenciador de pacotes Python)

### Produção (Render + Neon)
- Conta no [Render](https://render.com)
- Banco PostgreSQL no [Neon](https://neon.tech)

---

## 🚀 Instalação Local

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/sigem.git
cd sigem
```

### 2. Crie e ative o ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz:

```env
DEBUG=True
SECRET_KEY=sua-chave-secreta-aqui
DATABASE_URL=postgres://usuario:senha@localhost:5432/sigem
```

### 5. Execute as migrações

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crie o usuário administrador

```bash
python manage.py criar_admin
```
- CPF padrão: `00000000000`
- Senha padrão: `123456`

### 7. Inicie o servidor

```bash
python manage.py runserver
```

Acesse: **http://127.0.0.1:8000**

---

## ☁️ Deploy em Produção

### Render + Neon

1. **Banco de Dados (Neon)**
   - Crie um projeto no [Neon](https://neon.tech)
   - Copie a connection string

2. **Aplicação (Render)**
   - Crie um Web Service no [Render](https://render.com)
   - Conecte ao repositório GitHub
   - Configure as variáveis de ambiente:
     ```
     DATABASE_URL=sua-connection-string-neon
     SECRET_KEY=sua-chave-secreta
     DEBUG=False
     PYTHON_VERSION=3.11.0
     ```
   - Build Command: `./build.sh`
   - Start Command: `gunicorn core.wsgi:application`

3. **O `build.sh` executa automaticamente:**
   - Instalação de dependências
   - Coleta de arquivos estáticos
   - Criação de migrações
   - Aplicação de migrações
   - Criação do usuário admin

---

## 📱 Páginas do Sistema

| URL | Página | Acesso |
|-----|--------|--------|
| `/` | Login | Público |
| `/dashboard/` | Visão Geral | Admin, Comando-Geral, Comandante |
| `/comparar/` | Comparar Oficiais | Admin, Comando-Geral, Comandante, BM/3 |
| `/missoes/` | Dashboard de Missões | Admin, Comando-Geral, Comandante, BM/3, Corregedor |
| `/painel/` | Meu Painel | Oficial |
| `/oficial/` | Consultar Oficial | Admin, Comando-Geral, Comandante |
| `/oficial/<id>/` | Detalhe do Oficial | Admin, Comando-Geral, Comandante |
| `/minhas-solicitacoes/` | Histórico de Solicitações | Oficial |
| `/admin-painel/` | Painel Administrativo | Admin, BM/3, Corregedor |
| `/admin/` | Django Admin | Superusuário |

---

## 👥 Perfis de Acesso

| Perfil | Descrição | Permissões |
|--------|-----------|------------|
| **admin** | Administrador do sistema | Acesso total |
| **comando_geral** | Comando Geral do CBMGO | Dashboard, consultas, relatórios |
| **comandante** | Comandante de OBM | Dashboard filtrado por OBM, consultas |
| **bm3** | Seção BM/3 | Gestão de missões, designações, solicitações |
| **corregedor** | Corregedoria | Visualização de missões e designações |
| **oficial** | Oficial BM | Meu Painel, solicitações |

### Matriz de Permissões

| Funcionalidade | Admin | Cmd Geral | Comandante | BM/3 | Corregedor | Oficial |
|----------------|:-----:|:---------:|:----------:|:----:|:----------:|:-------:|
| Dashboard | ✅ | ✅ | ✅* | ❌ | ❌ | ❌ |
| Comparar Oficiais | ✅ | ✅ | ✅* | ✅ | ❌ | ❌ |
| Missões | ✅ | ✅ | ✅* | ✅ | ✅ | ❌ |
| Consultar Oficial | ✅ | ✅ | ✅* | ❌ | ❌ | ❌ |
| Meu Painel | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| CRUD Oficiais | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| CRUD Missões | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| CRUD Designações | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| CRUD Unidades | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| CRUD Usuários | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Avaliar Solicitações | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Fazer Solicitações | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

*\* Filtrado pela OBM do comandante*

---

## 🗄️ Estrutura do Banco

### Tabelas Principais

| Tabela | Descrição |
|--------|-----------|
| **Oficial** | Dados dos oficiais (nome, posto, quadro, OBM, CPF, RG, foto) |
| **Missao** | Missões/operações (tipo, status, local, período, documento) |
| **Designacao** | Vínculo oficial ↔ missão (função, complexidade, status) |
| **Unidade** | OBMs e estrutura hierárquica |
| **Usuario** | Autenticação (CPF, perfil, vínculo com oficial) |
| **SolicitacaoMissao** | Solicitações de criação de missão |
| **SolicitacaoDesignacao** | Solicitações de inclusão em missão |

### Diagrama Simplificado

```
Oficial ──────┬────── Designacao ────── Missao
              │
              ├────── Usuario
              │
              ├────── SolicitacaoMissao
              │
              └────── SolicitacaoDesignacao ────── Missao
```

---

## 📊 Métricas e Cálculos

### Carga Ponderada
```
Carga = (Qtd Baixa × 1) + (Qtd Média × 2) + (Qtd Alta × 3)
```

### Status de Carga (Monitoramento)
| Carga | Status | Indicador |
|-------|--------|-----------|
| > 20 | Crítico | 🔴 |
| 15-20 | Alto | 🟠 |
| 10-14 | Moderado | 🟡 |
| < 10 | Normal | 🟢 |

### Taxa de Ocupação
```
Taxa = (Oficiais com missão ÷ Total de oficiais) × 100
Meta ideal: 70% a 85%
```

### Índice de Alta Complexidade
```
Índice = (Designações alta ÷ Total designações) × 100
Meta: manter abaixo de 25%
```

---

## 🔧 Comandos Úteis

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Rodar servidor local
python manage.py runserver

# Criar migrações
python manage.py makemigrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Criar admin padrão (CPF: 00000000000, Senha: 123456)
python manage.py criar_admin

# Coletar arquivos estáticos
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
│   ├── views.py            # Lógica das páginas (~2900 linhas)
│   ├── urls.py             # Rotas do app
│   ├── admin.py            # Config do Django Admin
│   ├── decorators.py       # Decoradores de permissão
│   └── management/
│       └── commands/
│           └── criar_admin.py
├── templates/
│   ├── base.html           # Template base com menu
│   ├── auth/
│   │   └── login.html
│   ├── pages/
│   │   ├── dashboard.html
│   │   ├── admin_painel.html
│   │   ├── painel_oficial.html
│   │   ├── minhas_solicitacoes.html
│   │   ├── consultar_oficial.html
│   │   ├── comparar_oficiais.html
│   │   └── missoes.html
│   └── htmx/               # Componentes HTMX
│       ├── oficiais_tabela.html
│       ├── missoes_tabela.html
│       ├── designacoes_tabela.html
│       ├── solicitacoes_lista.html
│       ├── solicitacao_missao_form.html
│       ├── solicitacao_designacao_form.html
│       └── ...
├── static/
│   ├── css/
│   │   └── sigem.css
│   └── img/
│       ├── brasao_cbmgo.png
│       └── default_avatar.png
├── media/
│   └── fotos_oficiais/
├── .env
├── .gitignore
├── build.sh
├── requirements.txt
├── manage.py
└── README.md
```

---

## 🎨 Tecnologias

| Categoria | Tecnologia |
|-----------|------------|
| **Backend** | Django 5.x |
| **Banco de Dados** | PostgreSQL (Neon) |
| **Frontend** | HTML5 + HTMX |
| **Estilização** | CSS customizado |
| **Gráficos** | Chart.js |
| **Ícones** | Lucide Icons |
| **Fontes** | Inter + Oswald (Google Fonts) |
| **Hospedagem** | Render |
| **Planilhas** | openpyxl |
| **PDF** | ReportLab |

---

## 📝 Changelog

### v12 (Janeiro/2026)
- Sistema de solicitações refatorado (missão + designação separados)
- Botão de edição de solicitações antes da aprovação
- Feedback imediato em ações HTMX (sem reload)
- Correção do menu para perfil Oficial (/painel vs /oficial)
- Campo de observações para justificativas
- Criação automática de missão/designação na aprovação

### v11
- Novo modelo SolicitacaoMissao
- Página "Minhas Solicitações"
- Dois formulários no Meu Painel (missão e designação)
- Complexidade definida pela BM/3 na aprovação

### v10
- Tooltips de informação em todos os gráficos do dashboard
- Refatoração do ranking de oficiais (monitoramento de carga)
- Indicadores de status por cores (crítico, alto, moderado, normal)
- Correção do campo atualizado_em em SolicitacaoDesignacao

### v9
- Correção do filtro OBM (duplicação de resultados)
- Correção do filtro por posto (TC - Tenente-Coronel)

### v8
- Dashboard para comandantes (filtrado por OBM)
- Controle de acesso hierárquico
- Escopo de dados por unidade

---

## 🔐 Segurança

- Autenticação por CPF + senha
- Senhas criptografadas (PBKDF2)
- Proteção CSRF em formulários
- Controle de acesso por decoradores
- Sessões seguras

---

## 📞 Suporte

Desenvolvido para o **CBMGO** - Corpo de Bombeiros Militar do Estado de Goiás.

**"Vidas Alheias e Riquezas Salvar"** 🔥
