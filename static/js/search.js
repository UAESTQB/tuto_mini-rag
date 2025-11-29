// Gestion de la page de recherche/utilisation des documents

let isProcessing = false;
let conversationHistory = []; // Historique de la conversation

// Charger les stats de l'index au démarrage
async function loadIndexStats() {
    try {
        const response = await fetch('/api/index-stats');
        const data = await response.json();
        
        if (data.indexed) {
            document.getElementById('docCount').textContent = data.sources?.length || 0;
            document.getElementById('chunkCount').textContent = data.total_chunks || 0;
            document.getElementById('modelName').textContent = data.model || 'N/A';
        } else {
            showError('Aucun index disponible. Veuillez d\'abord indexer des documents.');
        }
    } catch (error) {
        console.error('Erreur lors du chargement des stats:', error);
        showError('Erreur lors du chargement des statistiques de l\'index');
    }
}

// Ajouter un message dans le chat
function addMessage(type, content, sources = null) {
    const messagesContainer = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const icons = {
        'user': '👤',
        'assistant': '🤖',
        'error': '❌',
        'system': 'ℹ️'
    };
    
    const iconDiv = document.createElement('div');
    iconDiv.className = 'message-icon';
    iconDiv.textContent = icons[type] || '💬';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Contenu principal
    const textP = document.createElement('p');
    textP.innerHTML = content.replace(/\n/g, '<br>');
    contentDiv.appendChild(textP);
    
    // Ajouter les sources si disponibles
    if (sources && sources.length > 0 && document.getElementById('showSources').checked) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources';
        
        const sourcesHeader = document.createElement('div');
        sourcesHeader.className = 'sources-header';
        sourcesHeader.textContent = `📚 Sources utilisées (${sources.length})`;
        sourcesDiv.appendChild(sourcesHeader);
        
        sources.forEach((source, index) => {
            const sourceItem = document.createElement('div');
            sourceItem.className = 'source-item';
            
            const sourceHeader = document.createElement('div');
            sourceHeader.className = 'source-header';
            
            const sourceName = document.createElement('span');
            sourceName.className = 'source-name';
            sourceName.textContent = `${index + 1}. ${source.source}`;
            
            const sourceScore = document.createElement('span');
            sourceScore.className = 'source-score';
            sourceScore.textContent = `Score: ${source.score.toFixed(2)}`;
            
            sourceHeader.appendChild(sourceName);
            sourceHeader.appendChild(sourceScore);
            
            const sourceText = document.createElement('div');
            sourceText.className = 'source-text';
            sourceText.textContent = source.text.substring(0, 200) + (source.text.length > 200 ? '...' : '');
            
            sourceItem.appendChild(sourceHeader);
            sourceItem.appendChild(sourceText);
            sourcesDiv.appendChild(sourceItem);
        });
        
        contentDiv.appendChild(sourcesDiv);
    }
    
    messageDiv.appendChild(iconDiv);
    messageDiv.appendChild(contentDiv);
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Afficher un indicateur de chargement
function showLoading() {
    const messagesContainer = document.getElementById('chatMessages');
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant-message';
    loadingDiv.id = 'loadingIndicator';
    
    const iconDiv = document.createElement('div');
    iconDiv.className = 'message-icon';
    iconDiv.textContent = '🤖';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-indicator';
    loadingIndicator.innerHTML = '<div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div>';
    
    contentDiv.appendChild(loadingIndicator);
    loadingDiv.appendChild(iconDiv);
    loadingDiv.appendChild(contentDiv);
    
    messagesContainer.appendChild(loadingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Supprimer l'indicateur de chargement
function hideLoading() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }
}

// Afficher une erreur
function showError(message) {
    addMessage('error', `<strong>Erreur :</strong> ${message}`);
}

// Envoyer une question
async function sendQuestion() {
    if (isProcessing) return;
    
    const questionInput = document.getElementById('questionInput');
    const question = questionInput.value.trim();
    
    if (!question) {
        showError('Veuillez entrer une question');
        return;
    }
    
    // Récupérer les paramètres
    const topK = parseInt(document.getElementById('topK').value);
    const temperature = parseFloat(document.getElementById('temperature').value);
    const maxTokens = parseInt(document.getElementById('maxTokens').value);
    
    // Afficher la question de l'utilisateur
    addMessage('user', question);
    
    // Ajouter à l'historique
    conversationHistory.push({
        role: 'user',
        content: question
    });
    
    questionInput.value = '';
    
    // Désactiver l'envoi pendant le traitement
    isProcessing = true;
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;
    
    // Afficher le chargement
    showLoading();
    
    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                conversation_history: conversationHistory,
                top_k: topK,
                temperature: temperature,
                max_tokens: maxTokens
            })
        });
        
        const data = await response.json();
        
        hideLoading();
        
        if (data.success) {
            addMessage('assistant', data.answer, data.sources);
            
            // Ajouter la réponse à l'historique
            conversationHistory.push({
                role: 'assistant',
                content: data.answer
            });
            
            // Mettre à jour le compteur d'historique
            updateHistoryCount();
        } else {
            showError(data.error || 'Erreur lors de la recherche');
        }
    } catch (error) {
        hideLoading();
        console.error('Erreur:', error);
        showError('Erreur de connexion au serveur');
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
        questionInput.focus();
    }
}

// Gestion du slider de température
document.getElementById('temperature').addEventListener('input', (e) => {
    document.getElementById('tempValue').textContent = e.target.value;
});

// Gestion du bouton d'envoi
document.getElementById('sendBtn').addEventListener('click', sendQuestion);

// Gestion de la touche Entrée (Ctrl+Enter pour envoyer)
document.getElementById('questionInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        e.preventDefault();
        sendQuestion();
    }
});

// Charger les stats au démarrage
loadIndexStats();

// Fonction pour mettre à jour le compteur d'historique
function updateHistoryCount() {
    const historyCount = document.getElementById('historyCount');
    if (historyCount) {
        historyCount.textContent = `Historique: ${conversationHistory.length} messages`;
    }
}

// Fonction pour effacer l'historique
function clearHistory() {
    conversationHistory = [];
    updateHistoryCount();
    
    // Effacer visuellement les messages (garder seulement le message de bienvenue)
    const messagesContainer = document.getElementById('chatMessages');
    const firstMessage = messagesContainer.querySelector('.system-message');
    messagesContainer.innerHTML = '';
    if (firstMessage) {
        messagesContainer.appendChild(firstMessage);
    }
    
    addMessage('system', '✨ Historique effacé. Vous pouvez démarrer une nouvelle conversation.');
}

// Gestion du bouton d'effacement
document.getElementById('clearHistoryBtn').addEventListener('click', clearHistory);
