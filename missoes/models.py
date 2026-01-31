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

    # Campos para integração com SICAD
    foto_sicad_id = models.CharField('ID da Foto no SICAD', max_length=100, blank=True)
    foto_sicad_hash = models.CharField('Hash da Foto no SICAD', max_length=64, blank=True)
    foto_origem = models.CharField(
        'Origem da Foto',
        max_length=10,
        choices=[('LOCAL', 'Local'), ('SICAD', 'SICAD')],
        default='LOCAL',
        blank=True
    )

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
        """Retorna a URL da foto priorizando SICAD."""
        # Prioriza foto do SICAD se disponível
        if self.foto_origem == 'SICAD' and self.foto_sicad_id and self.foto_sicad_hash:
            from django.conf import settings
            sicad_url = getattr(settings, 'SICAD_FILESYSTEM_URL', '')
            if sicad_url:
                return f"{sicad_url}/{self.foto_sicad_id}/{self.foto_sicad_hash}"

        # Fallback para foto local
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
        from django.db.models import F
        return self.designacoes.filter(
            missao__status='EM_ANDAMENTO'
        ).annotate(
            soma=F('funcao__tde') + F('funcao__nqt') + F('funcao__grs') + F('funcao__dec')
        ).filter(soma__gte=4, soma__lte=6).count()

    @property
    def total_media(self):
        """Total de designações de complexidade MÉDIA em missões EM_ANDAMENTO."""
        from django.db.models import F
        return self.designacoes.filter(
            missao__status='EM_ANDAMENTO'
        ).annotate(
            soma=F('funcao__tde') + F('funcao__nqt') + F('funcao__grs') + F('funcao__dec')
        ).filter(soma__gte=7, soma__lte=9).count()

    @property
    def total_alta(self):
        """Total de designações de complexidade ALTA em missões EM_ANDAMENTO."""
        from django.db.models import F
        return self.designacoes.filter(
            missao__status='EM_ANDAMENTO'
        ).annotate(
            soma=F('funcao__tde') + F('funcao__nqt') + F('funcao__grs') + F('funcao__dec')
        ).filter(soma__gte=10, soma__lte=12).count()
    
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
    ano = models.IntegerField('Ano', null=True, blank=True, default=2026)
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
        return self.nome_completo

    @property
    def nome_completo(self):
        """Retorna o nome completo da missão com o ano (se houver)."""
        if self.ano:
            return f"{self.nome} {self.ano}"
        return self.nome

    @property
    def total_designados(self):
        """Retorna o total de oficiais designados."""
        return self.designacoes.count()

    @property
    def esta_ativa(self):
        """Verifica se a missão está em andamento."""
        return self.status == 'EM_ANDAMENTO'


# ============================================================
# 🎯 MODELO: FUNÇÃO
# ============================================================
class Funcao(models.Model):
    """Representa uma função dentro de uma missão com sua complexidade calculada."""

    NIVEL_TDE_NQT_GRS_CHOICES = [
        (1, 'Baixo'),
        (2, 'Médio'),
        (3, 'Alto'),
    ]

    NIVEL_DEC_CHOICES = [
        (1, 'Pequeno'),
        (2, 'Médio'),
        (3, 'Grande'),
    ]

    COMPLEXIDADE_CHOICES = [
        ('BAIXA', 'Baixa'),
        ('MEDIA', 'Média'),
        ('ALTA', 'Alta'),
    ]

    missao = models.ForeignKey(
        'Missao',
        on_delete=models.CASCADE,
        related_name='funcoes',
        verbose_name='Missão'
    )
    funcao = models.CharField('Função', max_length=100)
    tde = models.IntegerField(
        'TDE (Tempo de Dedicação Exigido)',
        choices=NIVEL_TDE_NQT_GRS_CHOICES,
        default=2
    )
    nqt = models.IntegerField(
        'NQT (Nível de Qualificação Técnica Exigido)',
        choices=NIVEL_TDE_NQT_GRS_CHOICES,
        default=2
    )
    grs = models.IntegerField(
        'GRS (Grau de Responsabilidade Suportado)',
        choices=NIVEL_TDE_NQT_GRS_CHOICES,
        default=2
    )
    dec = models.IntegerField(
        'DEC (Dimensão do Efetivo Comandado)',
        choices=NIVEL_DEC_CHOICES,
        default=2
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Função'
        verbose_name_plural = 'Funções'
        ordering = ['missao__nome', 'funcao']
        unique_together = ['missao', 'funcao']

    def __str__(self):
        return f"{self.funcao} - {self.missao.nome_completo}"

    @property
    def soma_criterios(self):
        """Retorna a soma dos critérios TDE + NQT + GRS + DEC."""
        return self.tde + self.nqt + self.grs + self.dec

    @property
    def complexidade(self):
        """Calcula a complexidade com base na soma dos critérios.

        Baixa: soma 4-6
        Média: soma 7-9
        Alta: soma 10-12
        """
        soma = self.soma_criterios
        if 4 <= soma <= 6:
            return 'BAIXA'
        elif 7 <= soma <= 9:
            return 'MEDIA'
        else:  # 10-12
            return 'ALTA'

    def get_complexidade_display(self):
        """Retorna o display da complexidade."""
        complexidade_map = {
            'BAIXA': 'Baixa',
            'MEDIA': 'Média',
            'ALTA': 'Alta',
        }
        return complexidade_map.get(self.complexidade, '')


# ============================================================
# 🤝 MODELO: DESIGNAÇÃO
# ============================================================
class Designacao(models.Model):
    """Representa a designação de um oficial para uma missão em uma função específica."""

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
    funcao = models.ForeignKey(
        'Funcao',
        on_delete=models.PROTECT,  # Não permite deletar função se houver designações
        related_name='designacoes',
        verbose_name='Função'
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
        unique_together = ['missao', 'oficial', 'funcao']  # Um oficial não pode ter a mesma função duas vezes na mesma missão

    def __str__(self):
        return f"{self.oficial} → {self.missao.nome_completo} ({self.funcao.funcao})"

    @property
    def complexidade(self):
        """Retorna a complexidade da função."""
        return self.funcao.complexidade

    def get_complexidade_display(self):
        """Retorna o display da complexidade."""
        return self.funcao.get_complexidade_display()


# ============================================================
# 🏢 MODELO: UNIDADE
# ============================================================
class Unidade(models.Model):
    """Representa uma unidade/OBM."""
    
    TIPO_CHOICES = [
        ('COMANDO_GERAL', 'Comando-Geral'),
        ('ORGAO_DIRECAO', 'Órgão de Direção'),
        ('ORGAO_APOIO', 'Órgão de Apoio'),
        ('ORGAO_EXEC', 'Órgão de Execução'),
        ('SECAO_EMG', 'Seção do EMG'),
        ('BBM', 'Batalhão BM'),
        ('CIBM', 'Cia Independente BM'),
        ('PBM', 'Pelotão BM'),
        ('DBM', 'Destacamento BM'),
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
        # Todos exceto Oficial comum
        return self.role in ['admin', 'comando_geral', 'comandante', 'bm3', 'corregedor']
    
    @property
    def pode_ver_comparar(self):
        """Quem pode ver a página Comparar Oficiais"""
        return self.role in ['admin', 'comando_geral', 'comandante', 'bm3', 'corregedor']
    
    @property
    def pode_ver_missoes(self):
        """Quem pode ver a página Missões"""
        return True  # Todos podem ver
    
    @property
    def pode_ver_consultar_oficial(self):
        """Quem pode consultar outros oficiais"""
        return self.role in ['admin', 'comando_geral', 'comandante', 'bm3', 'corregedor']
    
    @property
    def pode_ver_painel(self):
        """Quem pode ver o Meu Painel (precisa ter oficial vinculado)"""
        return self.oficial is not None
    
    @property
    def pode_ver_admin(self):
        """Quem pode ver a página de Administração"""
        return self.role in ['admin', 'comando_geral', 'corregedor', 'bm3']
    
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
        return self.role in ['admin', 'comando_geral', 'corregedor', 'bm3']
    
    @property
    def pode_gerenciar_designacoes(self):
        """Quem pode CRUD de designações"""
        return self.role in ['admin', 'comando_geral', 'corregedor', 'bm3']
    
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
# 📝 MODELO: SOLICITAÇÃO UNIFICADA
# ============================================================
class Solicitacao(models.Model):
    """
    Solicitação unificada para inclusão de missão e/ou designação.
    
    Tipos:
    - NOVA_MISSAO: Cria uma nova missão E uma designação para o solicitante
    - DESIGNACAO: Cria apenas uma designação em missão já existente
    """
    
    TIPO_SOLICITACAO_CHOICES = [
        ('NOVA_MISSAO', 'Nova Missão + Designação'),
        ('DESIGNACAO', 'Designação em Missão Existente'),
    ]
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADA', 'Aprovada'),
        ('RECUSADA', 'Recusada'),
    ]
    
    LOCAL_CHOICES = [
        ('INTERNACIONAL', 'Internacional'),
        ('NACIONAL', 'Nacional'),
        ('ESTADUAL', 'Estadual'),
        ('CAPITAL', 'Capital'),
        ('1_CRBM', '1º CRBM'),
        ('2_CRBM', '2º CRBM'),
        ('3_CRBM', '3º CRBM'),
        ('4_CRBM', '4º CRBM'),
        ('5_CRBM', '5º CRBM'),
        ('6_CRBM', '6º CRBM'),
        ('7_CRBM', '7º CRBM'),
        ('8_CRBM', '8º CRBM'),
        ('9_CRBM', '9º CRBM'),
    ]
    
    # === Identificação ===
    tipo_solicitacao = models.CharField(
        'Tipo de Solicitação',
        max_length=20,
        choices=TIPO_SOLICITACAO_CHOICES
    )
    solicitante = models.ForeignKey(
        Oficial,
        on_delete=models.CASCADE,
        related_name='solicitacoes',
        verbose_name='Solicitante'
    )
    
    # === Campos de MISSÃO (preenchidos se tipo='NOVA_MISSAO') ===
    nome_missao = models.CharField('Nome da Missão', max_length=200, blank=True)
    ano_missao = models.IntegerField('Ano da Missão', null=True, blank=True, default=2026)
    tipo_missao = models.CharField(
        'Tipo da Missão',
        max_length=20,
        choices=Missao.TIPO_CHOICES,
        blank=True
    )
    status_missao = models.CharField(
        'Status da Missão',
        max_length=20,
        choices=Missao.STATUS_CHOICES,
        default='EM_ANDAMENTO',
        blank=True
    )
    local_missao = models.CharField(
        'Local da Missão',
        max_length=20,
        choices=LOCAL_CHOICES,
        blank=True
    )
    data_inicio = models.DateField('Data de Início', null=True, blank=True)
    data_fim = models.DateField('Data de Término', null=True, blank=True)
    documento_sei_missao = models.CharField('Nº SEI da Missão', max_length=100, blank=True)
    
    # === Campos de FUNÇÃO (para NOVA_MISSAO) ===
    nome_funcao = models.CharField('Nome da Função', max_length=100, blank=True)
    tde = models.IntegerField(
        'TDE',
        null=True,
        blank=True,
        help_text='Preenchido pelo avaliador na aprovação'
    )
    nqt = models.IntegerField(
        'NQT',
        null=True,
        blank=True,
        help_text='Preenchido pelo avaliador na aprovação'
    )
    grs = models.IntegerField(
        'GRS',
        null=True,
        blank=True,
        help_text='Preenchido pelo avaliador na aprovação'
    )
    dec = models.IntegerField(
        'DEC',
        null=True,
        blank=True,
        help_text='Preenchido pelo avaliador na aprovação'
    )

    # === Campos de DESIGNAÇÃO (sempre preenchidos) ===
    missao_existente = models.ForeignKey(
        Missao,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='solicitacoes_designacao',
        verbose_name='Missão Existente',
        help_text='Preenchido apenas se tipo=DESIGNACAO'
    )
    funcao_existente = models.ForeignKey(
        'Funcao',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='solicitacoes_designacao',
        verbose_name='Função Existente',
        help_text='Preenchido apenas se tipo=DESIGNACAO'
    )
    documento_sei_designacao = models.CharField('Nº SEI/BG da Designação', max_length=100)
    
    # === Controle da Solicitação ===
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDENTE'
    )
    avaliado_por = models.ForeignKey(
        'Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitacoes_avaliadas',
        verbose_name='Avaliado por'
    )
    data_avaliacao = models.DateTimeField('Data da Avaliação', null=True, blank=True)
    observacao_avaliador = models.TextField('Observação do Avaliador', blank=True)
    
    # === Resultados (preenchidos na aprovação) ===
    missao_criada = models.ForeignKey(
        Missao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitacao_origem_missao',
        verbose_name='Missão Criada',
        help_text='Preenchido automaticamente na aprovação se tipo=NOVA_MISSAO'
    )
    funcao_criada = models.ForeignKey(
        'Funcao',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitacao_origem_funcao',
        verbose_name='Função Criada',
        help_text='Preenchido automaticamente na aprovação se tipo=NOVA_MISSAO'
    )
    designacao_criada = models.ForeignKey(
        Designacao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitacao_origem',
        verbose_name='Designação Criada',
        help_text='Preenchido automaticamente na aprovação'
    )
    
    # === Timestamps ===
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Solicitação'
        verbose_name_plural = 'Solicitações'
        ordering = ['-criado_em']
    
    def __str__(self):
        if self.tipo_solicitacao == 'NOVA_MISSAO':
            return f"{self.solicitante} - Nova: {self.nome_missao} ({self.get_status_display()})"
        else:
            missao_nome = self.missao_existente.nome if self.missao_existente else '?'
            return f"{self.solicitante} - Designação em: {missao_nome} ({self.get_status_display()})"
    
    @property
    def is_nova_missao(self):
        """Verifica se é solicitação de nova missão."""
        return self.tipo_solicitacao == 'NOVA_MISSAO'
    
    @property
    def is_designacao(self):
        """Verifica se é solicitação de designação em missão existente."""
        return self.tipo_solicitacao == 'DESIGNACAO'
    
    @property
    def missao_referencia(self):
        """Retorna a missão de referência (criada ou existente)."""
        if self.tipo_solicitacao == 'NOVA_MISSAO':
            return self.missao_criada
        return self.missao_existente
    
    def aprovar(self, avaliador, observacao=''):
        """
        Aprova a solicitação e cria os registros necessários.

        Se NOVA_MISSAO: Cria Missão + Função + Designação
        Se DESIGNACAO: Cria apenas Designação (função já existe)

        Para NOVA_MISSAO, os campos tde, nqt, grs, dec devem já estar preenchidos na solicitação.
        """
        from django.utils import timezone

        self.avaliado_por = avaliador
        self.data_avaliacao = timezone.now()
        self.observacao_avaliador = observacao
        self.status = 'APROVADA'

        if self.tipo_solicitacao == 'NOVA_MISSAO':
            # Validar critérios
            if self.tde is None or self.nqt is None or self.grs is None or self.dec is None:
                raise ValueError('TDE, NQT, GRS e DEC devem ser informados.')

            # 1. Criar Missão
            missao = Missao.objects.create(
                nome=self.nome_missao,
                ano=self.ano_missao,
                tipo=self.tipo_missao,
                status=self.status_missao,
                local=self.local_missao,
                data_inicio=self.data_inicio,
                data_fim=self.data_fim,
                documento_referencia=self.documento_sei_missao,
            )
            self.missao_criada = missao

            # 2. Criar Função
            funcao = Funcao.objects.create(
                missao=missao,
                funcao=self.nome_funcao,
                tde=self.tde,
                nqt=self.nqt,
                grs=self.grs,
                dec=self.dec
            )
            self.funcao_criada = funcao

            # 3. Criar Designação
            designacao = Designacao.objects.create(
                oficial=self.solicitante,
                missao=missao,
                funcao=funcao,
                observacoes=f'Criado via solicitação. SEI: {self.documento_sei_designacao}',
            )
            self.designacao_criada = designacao

        else:  # DESIGNACAO
            if not self.funcao_existente:
                raise ValueError('Função deve ser selecionada.')

            designacao = Designacao.objects.create(
                oficial=self.solicitante,
                missao=self.missao_existente,
                funcao=self.funcao_existente,
                observacoes=f'Criado via solicitação. SEI: {self.documento_sei_designacao}',
            )
            self.designacao_criada = designacao

        self.save()
        return True

    
    def recusar(self, avaliador, observacao=''):
        """Recusa a solicitação."""
        from django.utils import timezone
        
        self.avaliado_por = avaliador
        self.data_avaliacao = timezone.now()
        self.observacao_avaliador = observacao
        self.status = 'RECUSADA'
        self.save()
        return True
