// Gestion de l'indexation

let indexationInProgress = false;

// Fonction pour supprimer l'index
async function deleteIndex() {
    if (!confirm('⚠️ Êtes-vous sûr de vouloir supprimer l\'index FAISS ?\n\nCette action est irréversible et vous devrez ré-indexer vos documents.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/delete-index', {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ ' + data.message);
            window.location.reload();
        } else {
            alert('❌ Erreur : ' + (data.error || 'Impossible de supprimer l\'index'));
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('❌ Erreur lors de la suppression de l\'index');
    }
}

function addLog(message, type = 'info') {
    const logContent = document.getElementById('logContent');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logContent.appendChild(entry);
    logContent.scrollTop = logContent.scrollHeight;
}

function updateStep(stepNumber, status) {
    const step = document.getElementById(`step${stepNumber}`);
    const statusEl = document.getElementById(`status${stepNumber}`);
    
    step.classList.remove('active', 'completed');
    
    if (status === 'active') {
        step.classList.add('active');
        statusEl.textContent = 'En cours...';
    } else if (status === 'completed') {
        step.classList.add('completed');
        statusEl.textContent = '✓ Terminé';
    } else if (status === 'error') {
        statusEl.textContent = '✗ Erreur';
        statusEl.style.color = '#dc3545';
    }
}

function updateProgress(percent) {
    const progressBarFill = document.getElementById('progressBarFill');
    const progressText = document.getElementById('progressText');
    
    progressBarFill.style.width = percent + '%';
    progressText.textContent = Math.round(percent) + '%';
}

async function startIndexation() {
    if (indexationInProgress) {
        alert('Une indexation est déjà en cours !');
        return;
    }
    
    // Récupérer la configuration
    const chunkSize = parseInt(document.getElementById('chunkSize').value);
    const chunkOverlap = parseInt(document.getElementById('chunkOverlap').value);
    const embeddingModel = document.getElementById('embeddingModel').value;
    
    // Masquer les résultats précédents
    document.getElementById('resultsSection').style.display = 'none';
    
    // Afficher la section de progression
    const progressSection = document.getElementById('progressSection');
    progressSection.style.display = 'block';
    
    // Réinitialiser les étapes
    for (let i = 1; i <= 4; i++) {
        const step = document.getElementById(`step${i}`);
        step.classList.remove('active', 'completed');
        document.getElementById(`status${i}`).textContent = 'En attente...';
        document.getElementById(`status${i}`).style.color = '';
    }
    
    document.getElementById('logContent').innerHTML = '';
    updateProgress(0);
    
    indexationInProgress = true;
    document.getElementById('indexButton').disabled = true;
    
    addLog('🚀 Démarrage de l\'indexation...', 'info');
    
    try {
        // Lancer l'indexation
        const response = await fetch('/api/index', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                chunk_size: chunkSize,
                chunk_overlap: chunkOverlap,
                embedding_model: embeddingModel
            })
        });
        
        if (!response.ok) {
            throw new Error('Erreur lors de l\'indexation');
        }
        
        const result = await response.json();
        
        if (result.success) {
            // Afficher les résultats
            showResults(result);
        } else {
            throw new Error(result.error || 'Erreur inconnue');
        }
        
    } catch (error) {
        addLog('❌ Erreur: ' + error.message, 'error');
        alert('Erreur lors de l\'indexation: ' + error.message);
    } finally {
        indexationInProgress = false;
        document.getElementById('indexButton').disabled = false;
    }
}

function showResults(result) {
    // Masquer la progression
    document.getElementById('progressSection').style.display = 'none';
    
    // Afficher les résultats
    const resultsSection = document.getElementById('resultsSection');
    const resultsGrid = document.getElementById('resultsGrid');
    
    resultsGrid.innerHTML = `
        <div class="result-card">
            <div class="result-label">Documents traités</div>
            <div class="result-value">${result.documents_processed}</div>
        </div>
        <div class="result-card">
            <div class="result-label">Total chunks</div>
            <div class="result-value">${result.total_chunks}</div>
        </div>
        <div class="result-card">
            <div class="result-label">Vecteurs indexés</div>
            <div class="result-value">${result.total_vectors}</div>
        </div>
        <div class="result-card">
            <div class="result-label">Temps écoulé</div>
            <div class="result-value">${result.elapsed_time}s</div>
        </div>
    `;
    
    resultsSection.style.display = 'block';
    
    // Mettre à jour le statut de la page
    document.getElementById('indexStatus').innerHTML = '<span class="status-badge success">✓ Oui</span>';
    
    // Rafraîchir les statistiques
    updateIndexStats();
}

async function updateIndexStats() {
    try {
        const response = await fetch('/api/index-stats');
        const stats = await response.json();
        
        if (stats.indexed) {
            document.getElementById('indexStatus').innerHTML = '<span class="status-badge success">✓ Oui</span>';
            
            // Ajouter les stats si disponibles
            const statusBox = document.getElementById('statusBox');
            
            // Retirer les anciennes stats
            const oldStats = statusBox.querySelectorAll('.dynamic-stat');
            oldStats.forEach(el => el.remove());
            
            // Ajouter les nouvelles
            if (stats.total_chunks) {
                const chunkStat = document.createElement('div');
                chunkStat.className = 'status-item dynamic-stat';
                chunkStat.innerHTML = `
                    <span class="status-label">Total chunks indexés:</span>
                    <span class="status-value">${stats.total_chunks}</span>
                `;
                statusBox.appendChild(chunkStat);
            }
            
            if (stats.model) {
                const modelStat = document.createElement('div');
                modelStat.className = 'status-item dynamic-stat';
                modelStat.innerHTML = `
                    <span class="status-label">Modèle utilisé:</span>
                    <span class="status-value" style="font-size: 1rem;">${stats.model}</span>
                `;
                statusBox.appendChild(modelStat);
            }
        }
    } catch (error) {
        console.error('Erreur lors de la récupération des stats:', error);
    }
}

// Charger les stats au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    updateIndexStats();
});
