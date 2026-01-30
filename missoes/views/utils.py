"""
============================================================
SIGEM - View Utilities
============================================================
Shared utility functions for views.
Extracted common patterns for pagination, ordering, and filtering.
"""

from django.core.paginator import Paginator
from django.db.models import Q


def apply_pagination(queryset, request, per_page=25):
    """
    Applies pagination to a queryset.
    Returns (page_obj, query_string) tuple.

    Common pattern used in:
    - htmx_oficiais_lista
    - htmx_missoes_tabela
    - htmx_designacoes_lista
    - htmx_unidades_lista
    - htmx_usuarios_lista

    Args:
        queryset: Django QuerySet to paginate
        request: HTTP request object
        per_page: Items per page (default 25)

    Returns:
        tuple: (page_obj, query_string) where query_string preserves filters
    """
    por_pagina = int(request.GET.get('por_pagina', per_page))
    pagina = request.GET.get('pagina', 1)

    paginator = Paginator(queryset, por_pagina)
    page_obj = paginator.get_page(pagina)

    # Build query string for pagination links (preserve existing filters)
    query_params = request.GET.copy()
    if 'pagina' in query_params:
        del query_params['pagina']
    query_string = query_params.urlencode()

    return page_obj, query_string


def apply_ordering(queryset, request, default_order='-criado_em'):
    """
    Applies ordering based on request parameters.

    Common pattern used across all lista functions.

    Args:
        queryset: Django QuerySet to order
        request: HTTP request object
        default_order: Default ordering field (default '-criado_em')

    Returns:
        QuerySet: Ordered queryset
    """
    ordenar = request.GET.get('ordenar', default_order)
    direcao = request.GET.get('direcao', 'desc')

    # Apply direction prefix
    if direcao == 'desc' and not ordenar.startswith('-'):
        ordenar = f'-{ordenar}'
    elif direcao == 'asc' and ordenar.startswith('-'):
        ordenar = ordenar[1:]

    return queryset.order_by(ordenar)


def build_search_filter(search_term, *fields):
    """
    Builds a Q object for searching across multiple fields.

    Example:
        q_filter = build_search_filter(busca, 'nome__icontains', 'cpf__icontains')
        oficiais = Oficial.objects.filter(q_filter)

    Args:
        search_term: String to search for
        *fields: Field lookups to search in (e.g., 'nome__icontains')

    Returns:
        Q: Django Q object for filtering
    """
    if not search_term:
        return Q()

    q_filter = Q()
    for field in fields:
        q_filter |= Q(**{field: search_term})

    return q_filter