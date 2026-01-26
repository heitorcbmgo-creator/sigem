"""
============================================================
📋 SIGEM - Modelos do Banco de Dados
Sistema de Gestão de Missões - CBMGO
============================================================
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


# ============================================================
# 👤 GERENCIADOR DE USUÁRIO CUSTOMIZADO
# ============================================================
class UsuarioManager(BaseUserManager):
    """Gerenciador customizado para o modelo Usuario."""
    
    def create_user(self, cpf, password=None, **extra_fields):
        """Cria e salva um usuário comum."""
        if not cpf:
            raise ValueError('O CPF é obrigatório')
        
        user = self.model(cpf=cpf, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, cpf, password=None, **extra_fields):
        """Cria e salva um superusuário."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        
        return self.create_user(cpf, password, **extra_fields)


# ============================================================
# 🎖️ MODELO: OFICIAL
# ============================================================
class Oficial(models.Model):
    """Representa um oficial do Corpo de Bombeiros."""
    
    POSTO_CHOICES = [
        ('Cel', 'Coronel'),
        ('TC', 'Tenente-Coronel'),
        ('Maj', 'Major'),
        ('Cap', 'Capitão'),
        ('1º Ten', 'Primeiro-Tenente'),
        ('2º Ten', 'Segundo-Tenente'),
        ('Asp', 'Aspirante'),
    ]
    
    QUADRO_CHOICES = [
        ('QOC', 'QOC'),
        ('QOA/Adm', 'QOA/Adm'),
        ('QOA/Mús', 'QOA/Mús'),
        ('QOM/Médico', 'QOM/Médico'),
        ('QOM/Dentista', 'QOM/Dentista'),
    ]
    
    cpf = models.CharField('CPF', max_length=11, unique=True)
    rg = models.CharField('RG Militar', max_length=20, unique=True)
    nome = models.CharField('Nome Completo', max_length=150)
    nome_guerra = models.CharField('Nome de Guerra', max_length=50, blank=True)
    posto = models.CharField('Posto', max_length=20, choices=POSTO_CHOICES)
    quadro = models.CharField('Quadro', max_length=20, choices=QUADRO_CHOICES)
    obm = models.CharField('OBM de Lotação', max_length=100, blank=True)
    funcao = models.CharField('Função', max_length=100, blank=True)
    email = models.EmailField('E-mail', blank=True)
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    foto = models.ImageField('Foto', upload_to='fotos_oficiais/', blank=True, null=True)
    ativo = models.BooleanField('Ativo', default=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Oficial'
        verbose_name_plural = 'Oficiais'
        ordering = ['posto', 'nome']
    
    def __str__(self):
        return f"{self.posto} {self.nome_guerra or self.nome}"
    
    @property
    def foto_url(self):
        """Retorna a URL da foto ou uma imagem padrão."""
        if self.foto:
            return self.foto.url
        return '/static/img/default_avatar.png'
    
    @property
    def total_missoes_ativas(self):
        """Retorna o total de missões ativas do oficial."""
        return self.designacoes.filter(missao__status='EM_ANDAMENTO').count()
    
    @property
    def total_baixa(self):
        """Total de designações de complexidade BAIXA em missões EM_ANDAMENTO."""
        return self.designacoes.filter(
            missao__status='EM_ANDAMENTO',
            complexidade='BAIXA'
        ).count()
    
    @property
    def total_media(self):
        """Total de designações de complexidade MÉDIA em missões EM_ANDAMENTO."""
        return self.designacoes.filter(
            missao__status='EM_ANDAMENTO',
            complexidade='MEDIA'
        ).count()
    
    @property
    def total_alta(self):
        """Total de designações de complexidade ALTA em missões EM_ANDAMENTO."""
        return self.designacoes.filter(
            missao__status='EM_ANDAMENTO',
            complexidade='ALTA'
        ).count()
    
    @property
    def carga_total(self):
        """Carga ponderada: Baixa=1, Média=2, Alta=3."""
        return self.total_baixa + (self.total_media * 2) + (self.total_alta * 3)
    
    def get_ultimas_missoes(self, limit=5):
        """Retorna as últimas missões do oficial."""
        return self.designacoes.select_related('missao').filter(
            missao__status='EM_ANDAMENTO'
        ).order_by('-criado_em')[:limit]


# ============================================================
# 🗂️ MODELO: MISSÃO
# ============================================================
class Missao(models.Model):
    """Representa uma missão/operação."""
    
    TIPO_CHOICES = [
        ('OPERACIONAL', 'Operacional'),
        ('ADMINISTRATIVA', 'Administrativa'),
        ('ENSINO', 'Ensino'),
        ('CORREICIONAL', 'Correicional'),
        ('COMISSAO', 'Comissão'),
        ('ACAO_SOCIAL', 'Ação Social'),
    ]
    
    STATUS_CHOICES = [
        ('PLANEJADA', 'Planejada'),
        ('EM_ANDAMENTO', 'Em andamento'),
        ('CONCLUIDA', 'Concluída'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    nome = models.CharField('Nome da Missão', max_length=200)
    descricao = models.TextField('Descrição', blank=True)
    local = models.CharField('Local', max_length=200, blank=True)
    data_inicio = models.DateField('Data de Início', null=True, blank=True)
    data_fim = models.DateField('Data de Término', null=True, blank=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PLANEJADA')
    documento_referencia = models.CharField('Documento de Referência (SEI/BG)', max_length=100, blank=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Missão'
        verbose_name_plural = 'Missões'
        ordering = ['-data_inicio', 'nome']
    
    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"
    
    @property
    def total_designados(self):
        """Retorna o total de oficiais designados."""
        return self.designacoes.count()
    
    @property
    def esta_ativa(self):
        """Verifica se a missão está em andamento."""
        return self.status == 'EM_ANDAMENTO'


# ============================================================
# 🤝 MODELO: DESIGNAÇÃO
# ============================================================
class Designacao(models.Model):
    """Representa a designação de um oficial para uma missão."""
    
    FUNCAO_CHOICES = [
        ('COMANDANTE', 'Comandante'),
        ('SUBCOMANDANTE', 'Subcomandante'),
        ('COORDENADOR', 'Coordenador'),
        ('PRESIDENTE', 'Presidente'),
        ('MEMBRO', 'Membro'),
        ('AUXILIAR', 'Auxiliar'),
        ('INSTRUTOR', 'Instrutor'),
        ('ENCARREGADO', 'Encarregado'),
        ('RELATOR', 'Relator'),
        ('ESCRIVAO', 'Escrivão'),
    ]
    
    COMPLEXIDADE_CHOICES = [
        ('BAIXA', 'Baixa'),
        ('MEDIA', 'Média'),
        ('ALTA', 'Alta'),
    ]
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente de Aprovação'),
        ('APROVADA', 'Aprovada'),
        ('RECUSADA', 'Recusada'),
    ]
    
    missao = models.ForeignKey(
        Missao, 
        on_delete=models.CASCADE, 
        related_name='designacoes',
        verbose_name='Missão'
    )
    oficial = models.ForeignKey(
        Oficial, 
        on_delete=models.CASCADE, 
        related_name='designacoes',
        verbose_name='Oficial'
    )
    funcao_na_missao = models.CharField(
        'Função na Missão', 
        max_length=20, 
        choices=FUNCAO_CHOICES,
        default='MEMBRO'
    )
    complexidade = models.CharField(
        'Complexidade', 
        max_length=10, 
        choices=COMPLEXIDADE_CHOICES,
        default='MEDIA'
    )
    observacoes = models.TextField('Observações', blank=True)
    status = models.CharField(
        'Status da Designação',
        max_length=20,
        choices=STATUS_CHOICES,
        default='APROVADA'
    )
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Designação'
        verbose_name_plural = 'Designações'
        ordering = ['-criado_em']
        unique_together = ['missao', 'oficial']  # Um oficial só pode ter uma designação por missão
    
    def __str__(self):
        return f"{self.oficial} → {self.missao.nome} ({self.get_funcao_na_missao_display()})"
    
    @property
    def is_chefia(self):
        """Verifica se é uma função de chefia/comando."""
        return self.funcao_na_missao in ['COMANDANTE', 'SUBCOMANDANTE', 'COORDENADOR', 'PRESIDENTE', 'ENCARREGADO']


# ============================================================
# 🏢 MODELO: UNIDADE
# ============================================================
class Unidade(models.Model):
    """Representa uma unidade/OBM."""
    
    TIPO_CHOICES = [
        ('COMANDO_GERAL', 'Comando Geral'),
        ('DIRETORIA', 'Diretoria'),
        ('BBM', 'Batalhão BM'),
        ('CIBM', 'Companhia Independente BM'),
        ('CBM', 'Companhia BM'),
        ('SECAO', 'Seção'),
    ]
    
    nome = models.CharField('Nome', max_length=150)
    sigla = models.CharField('Sigla', max_length=20, blank=True)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    comando_superior = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinadas',
        verbose_name='Comando Superior'
    )
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Unidade'
        verbose_name_plural = 'Unidades'
        ordering = ['nome']
    
    def __str__(self):
        return self.sigla or self.nome


# ============================================================
# 👤 MODELO: USUÁRIO CUSTOMIZADO
# ============================================================
class Usuario(AbstractBaseUser, PermissionsMixin):
    """Usuário customizado que usa CPF como login."""
    
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('corregedor', 'Corregedor'),
        ('bm3', 'BM/3'),
        ('comando_geral', 'Comando-Geral'),
        ('comandante', 'Comandante'),
        ('oficial', 'Oficial'),
    ]
    
    cpf = models.CharField('CPF', max_length=11, unique=True)
    role = models.CharField('Perfil', max_length=20, choices=ROLE_CHOICES, default='oficial')
    oficial = models.OneToOneField(
        Oficial,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuario',
        verbose_name='Oficial Vinculado'
    )
    is_active = models.BooleanField('Ativo', default=True)
    is_staff = models.BooleanField('Acesso ao Admin', default=False)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    ultimo_acesso = models.DateTimeField('Último Acesso', null=True, blank=True)
    
    objects = UsuarioManager()
    
    USERNAME_FIELD = 'cpf'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
    
    def __str__(self):
        if self.oficial:
            return f"{self.oficial.posto} {self.oficial.nome_guerra or self.oficial.nome}"
        return self.cpf
    
    # ============================================================
    # 🔐 PROPRIEDADES DE PERMISSÃO
    # ============================================================
    
    @property
    def is_admin(self):
        """Administrador - acesso total"""
        return self.role == 'admin'
    
    @property
    def is_corregedor(self):
        """Corregedor - acesso a Missões e Designações"""
        return self.role == 'corregedor'
    
    @property
    def is_bm3(self):
        """BM/3 - acesso a Missões, Designações e Solicitações"""
        return self.role == 'bm3'
    
    @property
    def is_comando_geral(self):
        """Comando-Geral - visualização ampla, sem admin"""
        return self.role == 'comando_geral'
    
    @property
    def is_comandante(self):
        """Comandante - acesso restrito à sua OBM"""
        return self.role == 'comandante'
    
    @property
    def is_oficial(self):
        """Oficial comum"""
        return self.role == 'oficial'
    
    # ============================================================
    # 🔑 PERMISSÕES DE ACESSO ÀS PÁGINAS
    # ============================================================
    
    @property
    def pode_ver_dashboard(self):
        """Quem pode ver a página Visão Geral"""
        return self.role in ['admin', 'comando_geral', 'comandante']
    
    @property
    def pode_ver_comparar(self):
        """Quem pode ver a página Comparar Oficiais"""
        return self.role in ['admin', 'corregedor', 'bm3', 'comando_geral', 'comandante']
    
    @property
    def pode_ver_missoes(self):
        """Quem pode ver a página Missões"""
        return True  # Todos podem ver
    
    @property
    def pode_ver_painel(self):
        """Quem pode ver o Meu Painel"""
        return True  # Todos podem ver
    
    @property
    def pode_ver_admin(self):
        """Quem pode ver a página de Administração"""
        return self.role in ['admin', 'corregedor', 'bm3']
    
    # ============================================================
    # 🔑 PERMISSÕES DE AÇÕES NA ADMINISTRAÇÃO
    # ============================================================
    
    @property
    def pode_gerenciar_oficiais(self):
        """Quem pode CRUD de oficiais"""
        return self.role == 'admin'
    
    @property
    def pode_gerenciar_missoes(self):
        """Quem pode CRUD de missões"""
        return self.role in ['admin', 'corregedor', 'bm3']
    
    @property
    def pode_gerenciar_designacoes(self):
        """Quem pode CRUD de designações"""
        return self.role in ['admin', 'corregedor', 'bm3']
    
    @property
    def pode_gerenciar_unidades(self):
        """Quem pode CRUD de unidades"""
        return self.role == 'admin'
    
    @property
    def pode_gerenciar_usuarios(self):
        """Quem pode CRUD de usuários"""
        return self.role == 'admin'
    
    @property
    def pode_gerenciar_solicitacoes(self):
        """Quem pode avaliar solicitações"""
        return self.role in ['admin', 'bm3']
    
    # ============================================================
    # 🏢 MÉTODOS PARA COMANDANTE (OBM)
    # ============================================================
    
    def get_obm_subordinadas(self):
        """Retorna lista de OBMs subordinadas ao comandante."""
        if not self.oficial:
            return []
        
        obm_usuario = self.oficial.obm
        if not obm_usuario:
            return []
        
        # Buscar a unidade do comandante
        try:
            unidade_comandante = Unidade.objects.get(
                models.Q(nome__icontains=obm_usuario) | models.Q(sigla__icontains=obm_usuario)
            )
        except Unidade.DoesNotExist:
            return [obm_usuario]
        except Unidade.MultipleObjectsReturned:
            unidade_comandante = Unidade.objects.filter(
                models.Q(nome__icontains=obm_usuario) | models.Q(sigla__icontains=obm_usuario)
            ).first()
        
        # Buscar subordinadas recursivamente
        obms = [obm_usuario]
        obms.extend(self._get_subordinadas_recursivo(unidade_comandante))
        
        return list(set(obms))
    
    def _get_subordinadas_recursivo(self, unidade):
        """Busca recursiva de unidades subordinadas."""
        subordinadas = []
        for sub in unidade.subordinadas.all():
            # Prioriza sigla, se não tiver usa o nome
            if sub.sigla:
                subordinadas.append(sub.sigla)
            elif sub.nome:
                subordinadas.append(sub.nome)
            subordinadas.extend(self._get_subordinadas_recursivo(sub))
        return subordinadas
    
    def pode_ver_oficial(self, oficial):
        """Verifica se o usuário pode ver determinado oficial."""
        # Admin, Corregedor, BM/3 e Comando-Geral veem todos
        if self.role in ['admin', 'corregedor', 'bm3', 'comando_geral']:
            return True
        
        # Comandante vê apenas sua OBM e subordinadas
        if self.role == 'comandante':
            obms_permitidas = self.get_obm_subordinadas()
            return any(obm in (oficial.obm or '') for obm in obms_permitidas)
        
        # Oficial comum vê apenas a si mesmo
        if self.role == 'oficial':
            return self.oficial and self.oficial.id == oficial.id
        
        return False
    
    @property
    def foto_url(self):
        """Retorna a URL da foto do oficial vinculado."""
        if self.oficial and self.oficial.foto:
            return self.oficial.foto.url
        return '/static/img/default_avatar.png'


# ============================================================
# 📝 MODELO: SOLICITAÇÃO DE DESIGNAÇÃO
# ============================================================
class SolicitacaoDesignacao(models.Model):
    """Solicitação de inclusão de designação feita pelo oficial."""
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADA', 'Aprovada'),
        ('RECUSADA', 'Recusada'),
    ]
    
    solicitante = models.ForeignKey(
        Oficial,
        on_delete=models.CASCADE,
        related_name='solicitacoes',
        verbose_name='Solicitante'
    )
    nome_missao = models.CharField('Nome da Missão', max_length=200)
    funcao_na_missao = models.CharField('Função na Missão', max_length=100)
    complexidade = models.CharField('Complexidade', max_length=20)
    documento_referencia = models.CharField('Nº SEI / BG', max_length=100, blank=True)
    justificativa = models.TextField('Justificativa', blank=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    avaliado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitacoes_avaliadas',
        verbose_name='Avaliado por'
    )
    data_avaliacao = models.DateTimeField('Data da Avaliação', null=True, blank=True)
    observacao_avaliador = models.TextField('Observação do Avaliador', blank=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Solicitação de Designação'
        verbose_name_plural = 'Solicitações de Designação'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"{self.solicitante} - {self.nome_missao} ({self.get_status_display()})"
