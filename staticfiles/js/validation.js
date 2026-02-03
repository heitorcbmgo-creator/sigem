/**
 * Validation Panel JavaScript
 * Gerenciamento de seleção em lote e modais para o painel de validação
 */

// Gerenciamento de seleção em lote
let selectedIds = new Set();

/**
 * Alterna a seleção de uma linha específica
 */
function toggleRowSelection(checkbox, id) {
    if (checkbox.checked) {
        selectedIds.add(id);
        checkbox.closest('tr').classList.add('selected');
    } else {
        selectedIds.delete(id);
        checkbox.closest('tr').classList.remove('selected');
    }
    updateBatchUI();
}

/**
 * Alterna seleção de todas as linhas visíveis
 */
function toggleSelectAll(checkbox) {
    const checkboxes = document.querySelectorAll('.row-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = checkbox.checked;
        const id = parseInt(cb.value);
        if (checkbox.checked) {
            selectedIds.add(id);
            cb.closest('tr').classList.add('selected');
        } else {
            selectedIds.delete(id);
            cb.closest('tr').classList.remove('selected');
        }
    });
    updateBatchUI();
}

/**
 * Seleciona todas as linhas visíveis
 */
function selectAll() {
    const checkboxes = document.querySelectorAll('.row-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = true;
        const id = parseInt(cb.value);
        selectedIds.add(id);
        cb.closest('tr').classList.add('selected');
    });
    document.getElementById('select-all').checked = true;
    updateBatchUI();
}

/**
 * Desmarca todas as seleções
 */
function deselectAll() {
    selectedIds.clear();
    const checkboxes = document.querySelectorAll('.row-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = false;
        cb.closest('tr').classList.remove('selected');
    });
    document.getElementById('select-all').checked = false;
    updateBatchUI();
}

/**
 * Atualiza a UI da barra de ações em lote
 */
function updateBatchUI() {
    const count = selectedIds.size;
    const batchBar = document.getElementById('batch-actions');
    const countSpan = document.getElementById('selected-count');

    if (countSpan) {
        countSpan.textContent = count;
    }

    if (batchBar) {
        batchBar.style.display = count > 0 ? 'flex' : 'none';
    }
}

// ========================================
// Modal Management
// ========================================

/**
 * Abre modal com conteúdo específico
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        lucide.createIcons();
    }
}

/**
 * Fecha um modal específico
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Fecha todos os modais
 */
function closeAllModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
}

/**
 * Abre modal de quick approve
 */
function openQuickApproveModal(id) {
    const modal = document.getElementById('modal-quick-approve');
    const body = document.getElementById('modal-quick-approve-body');

    // Criar formulário de quick approve
    body.innerHTML = `
        <form id="form-quick-approve" hx-post="/htmx/solicitacao/${id}/quick-approve/"
              hx-target="#quick-approve-feedback">
            <div class="form-group">
                <label class="form-label">Complexidade *</label>
                <div class="radio-group">
                    <label class="radio-label">
                        <input type="radio" name="complexidade" value="BAIXA"> Baixa
                    </label>
                    <label class="radio-label">
                        <input type="radio" name="complexidade" value="MEDIA" checked> Média
                    </label>
                    <label class="radio-label">
                        <input type="radio" name="complexidade" value="ALTA"> Alta
                    </label>
                </div>
            </div>

            <div id="quick-approve-feedback"></div>

            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" onclick="closeModal('modal-quick-approve')">Cancelar</button>
                <button type="submit" class="btn btn-success">
                    <i data-lucide="check-circle"></i> Aprovar
                </button>
            </div>
        </form>
    `;

    htmx.process(body);
    lucide.createIcons();
    modal.style.display = 'flex';
}

/**
 * Abre modal de detalhes completo
 */
function openDetailModal(id) {
    const modal = document.getElementById('modal-detalhes');
    const body = document.getElementById('modal-detalhes-body');

    // Carregar conteúdo via HTMX
    fetch(`/htmx/solicitacao/${id}/detalhes/`)
        .then(response => response.text())
        .then(html => {
            body.innerHTML = html;
            htmx.process(body);
            lucide.createIcons();
            modal.style.display = 'flex';
        })
        .catch(error => {
            console.error('Erro ao carregar detalhes:', error);
            body.innerHTML = `
                <div class="alert alert-danger">
                    <i data-lucide="alert-circle"></i>
                    Erro ao carregar detalhes da solicitação.
                </div>
            `;
            lucide.createIcons();
        });
}

// ========================================
// Batch Operations
// ========================================

/**
 * Abre modal de aprovação em lote
 */
function openBatchApproveModal() {
    if (selectedIds.size === 0) {
        alert('Selecione ao menos uma solicitação.');
        return;
    }

    const modal = document.getElementById('modal-batch-approve');
    document.getElementById('batch-approve-count').textContent = selectedIds.size;
    modal.style.display = 'flex';
    lucide.createIcons();
}

/**
 * Submete aprovação em lote
 */
function submitBatchApprove() {
    const form = document.getElementById('form-batch-approve');
    const complexidade = form.querySelector('input[name="complexidade"]:checked')?.value;
    const observacao = form.querySelector('textarea[name="observacao"]').value;

    if (!complexidade) {
        alert('Selecione a complexidade.');
        return;
    }

    const formData = new FormData();
    selectedIds.forEach(id => formData.append('ids[]', id));
    formData.append('complexidade', complexidade);
    formData.append('observacao', observacao);

    // Obter CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (csrfToken) {
        formData.append('csrfmiddlewaretoken', csrfToken);
    }

    fetch('/htmx/solicitacao/batch-approve/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken || ''
        }
    })
    .then(response => response.text())
    .then(html => {
        // Mostrar resultado
        const modalBody = document.querySelector('#modal-batch-approve .modal-body');
        modalBody.innerHTML = html + modalBody.innerHTML;

        // Limpar seleções
        selectedIds.clear();
        deselectAll();

        // Fechar modal e atualizar lista
        setTimeout(() => {
            closeModal('modal-batch-approve');
            htmx.trigger('#validation-content', 'refresh');
            location.reload(); // Recarregar para atualizar contadores
        }, 2000);

        lucide.createIcons();
    })
    .catch(error => {
        console.error('Erro ao aprovar em lote:', error);
        alert('Erro ao processar aprovação em lote.');
    });
}

/**
 * Abre modal de recusa em lote
 */
function openBatchRejectModal() {
    if (selectedIds.size === 0) {
        alert('Selecione ao menos uma solicitação.');
        return;
    }

    const modal = document.getElementById('modal-batch-reject');
    document.getElementById('batch-reject-count').textContent = selectedIds.size;
    modal.style.display = 'flex';
    lucide.createIcons();
}

/**
 * Submete recusa em lote
 */
function submitBatchReject() {
    const form = document.getElementById('form-batch-reject');
    const observacao = form.querySelector('textarea[name="observacao"]').value.trim();

    if (!observacao) {
        alert('A justificativa é obrigatória para recusa em lote.');
        return;
    }

    const formData = new FormData();
    selectedIds.forEach(id => formData.append('ids[]', id));
    formData.append('observacao', observacao);

    // Obter CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (csrfToken) {
        formData.append('csrfmiddlewaretoken', csrfToken);
    }

    fetch('/htmx/solicitacao/batch-reject/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken || ''
        }
    })
    .then(response => response.text())
    .then(html => {
        // Mostrar resultado
        const modalBody = document.querySelector('#modal-batch-reject .modal-body');
        modalBody.innerHTML = html + modalBody.innerHTML;

        // Limpar seleções
        selectedIds.clear();
        deselectAll();

        // Fechar modal e atualizar lista
        setTimeout(() => {
            closeModal('modal-batch-reject');
            htmx.trigger('#validation-content', 'refresh');
            location.reload(); // Recarregar para atualizar contadores
        }, 2000);

        lucide.createIcons();
    })
    .catch(error => {
        console.error('Erro ao recusar em lote:', error);
        alert('Erro ao processar recusa em lote.');
    });
}

// ========================================
// Event Listeners
// ========================================

// Fechar modais ao clicar fora
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
});

// Prevenir fechar modal ao clicar no conteúdo
document.querySelectorAll('.modal-content').forEach(content => {
    content.addEventListener('click', function(event) {
        event.stopPropagation();
    });
});

// Atualizar ícones após HTMX swap
document.body.addEventListener('htmx:afterSwap', function(event) {
    lucide.createIcons();

    // Se atualizou o conteúdo de validação, limpar seleções
    if (event.detail.target.id === 'validation-content') {
        selectedIds.clear();
        updateBatchUI();
    }
});

// Atualizar ícones após quick approve
document.body.addEventListener('htmx:afterSwap', function(event) {
    if (event.detail.target.id === 'quick-approve-feedback') {
        lucide.createIcons();
        // Fechar modal e atualizar lista após sucesso
        setTimeout(() => {
            closeModal('modal-quick-approve');
            htmx.trigger('#validation-content', 'refresh');
            location.reload();
        }, 1500);
    }
});

// Inicializar no carregamento da página
document.addEventListener('DOMContentLoaded', function() {
    lucide.createIcons();
    updateBatchUI();
});