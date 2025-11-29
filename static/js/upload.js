// Gestion de l'upload de fichiers avec drag & drop et barre de progression

const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressPercent = document.getElementById('progressPercent');
const progressFileName = document.getElementById('progressFileName');
const progressStatus = document.getElementById('progressStatus');
const documentsList = document.getElementById('documentsList');
const fileCount = document.getElementById('fileCount');
const nextStepButton = document.getElementById('nextStepButton');
const nextStepMessage = document.getElementById('nextStepMessage');

// Drag & Drop
uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    handleFiles(files);
});

// Click pour sélectionner
uploadZone.addEventListener('click', (e) => {
    // Ne déclencher que si on clique sur la zone, pas sur le bouton
    if (e.target.tagName !== 'LABEL' && !e.target.closest('label')) {
        fileInput.click();
    }
});

fileInput.addEventListener('change', (e) => {
    const files = e.target.files;
    handleFiles(files);
    // Réinitialiser l'input pour permettre de sélectionner le même fichier
    e.target.value = '';
});

// Gestion des fichiers
let hasError = false;

function handleFiles(files) {
    if (files.length === 0) return;
    
    hasError = false;
    // Upload séquentiel des fichiers
    uploadFilesSequentially(Array.from(files), 0);
}

function uploadFilesSequentially(files, index) {
    if (index >= files.length) {
        // Tous les fichiers sont uploadés
        // Ne cacher que si pas d'erreur
        if (!hasError) {
            setTimeout(() => {
                progressContainer.style.display = 'none';
                refreshFileList();
            }, 2500);
        } else {
            // Juste rafraîchir la liste mais garder le message d'erreur
            refreshFileList();
        }
        return;
    }
    
    const file = files[index];
    uploadFile(file, () => {
        // Passer au fichier suivant après un court délai
        setTimeout(() => {
            uploadFilesSequentially(files, index + 1);
        }, 2000);
    });
}

function uploadFile(file, callback) {
    // Vérifier si le fichier existe déjà
    const existingFiles = Array.from(documentsList.querySelectorAll('.document-name')).map(el => el.textContent);
    if (existingFiles.includes(file.name)) {
        showError(`Le fichier "${file.name}" existe déjà`);
        callback();
        return;
    }
    
    // Vérifier la taille
    const maxSize = 256 * 1024 * 1024; // 256 MB
    if (file.size > maxSize) {
        showError(`Le fichier ${file.name} est trop volumineux (max 256 MB)`);
        callback();
        return;
    }
    
    // Vérifier l'extension
    const allowedExtensions = ['pdf', 'txt', 'doc', 'docx', 'md'];
    const extension = file.name.split('.').pop().toLowerCase();
    if (!allowedExtensions.includes(extension)) {
        showError(`Type de fichier non autorisé : ${file.name}`);
        callback();
        return;
    }
    
    // Afficher la barre de progression
    progressContainer.style.display = 'block';
    progressFileName.textContent = file.name;
    progressPercent.textContent = '0%';
    progressFill.style.width = '0%';
    progressStatus.textContent = 'Upload en cours...';
    progressStatus.className = 'progress-status';
    
    // Créer FormData
    const formData = new FormData();
    formData.append('file', file);
    
    // Upload avec XMLHttpRequest pour suivre la progression
    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            progressFill.style.width = percentComplete + '%';
            progressPercent.textContent = percentComplete + '%';
        }
    });
    
    xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            progressFill.style.width = '100%';
            progressFill.style.background = 'repeating-linear-gradient(45deg, #28a745, #28a745 10px, #34d058 10px, #34d058 20px)';
            progressPercent.textContent = '100%';
            progressStatus.textContent = '✓ Upload réussi !';
            progressStatus.className = 'progress-status success';
            
            // Ajouter le fichier à la liste
            addFileToList(response);
            
            callback();
        } else {
            const error = JSON.parse(xhr.responseText);
            showError(error.error || 'Erreur lors de l\'upload');
            callback();
        }
    });
    
    xhr.addEventListener('error', () => {
        showError('Erreur réseau lors de l\'upload');
        callback();
    });
    
    xhr.open('POST', '/api/upload');
    xhr.send(formData);
}

function showError(message) {
    hasError = true;
    progressContainer.style.display = 'block';
    progressFill.style.width = '100%';
    progressFill.style.background = 'repeating-linear-gradient(45deg, #dc3545, #dc3545 10px, #e04b59 10px, #e04b59 20px)';
    progressPercent.textContent = 'Erreur';
    progressStatus.textContent = '✗ ' + message;
    progressStatus.className = 'progress-status error';
    
    // Ne pas cacher automatiquement - l'utilisateur peut voir l'erreur
    // Le prochain upload ou refresh cachera le message
}

function addFileToList(fileInfo) {
    // Supprimer l'état vide si présent
    const emptyState = document.getElementById('emptyState');
    if (emptyState) {
        emptyState.remove();
    }
    
    // Créer la carte du document
    const card = document.createElement('div');
    card.className = 'document-card';
    card.setAttribute('data-filename', fileInfo.filename);
    
    // Déterminer l'icône selon l'extension
    let icon = '📄';
    if (fileInfo.filename.endsWith('.pdf')) icon = '📕';
    else if (fileInfo.filename.endsWith('.txt')) icon = '📝';
    else if (fileInfo.filename.endsWith('.md')) icon = '📗';
    else if (fileInfo.filename.endsWith('.doc') || fileInfo.filename.endsWith('.docx')) icon = '📘';
    
    const sizeKB = (fileInfo.size / 1024).toFixed(2);
    
    card.innerHTML = `
        <div class="document-icon">${icon}</div>
        <div class="document-info">
            <div class="document-name">${fileInfo.filename}</div>
            <div class="document-meta">
                <span class="document-size">${sizeKB} KB</span>
                <span class="document-date">${fileInfo.date}</span>
            </div>
        </div>
        <button class="delete-button" onclick="deleteFile('${fileInfo.filename}')">
            🗑️
        </button>
    `;
    
    // Ajouter au début de la liste
    documentsList.insertBefore(card, documentsList.firstChild);
    
    // Mettre à jour le compteur
    updateFileCount();
}

function deleteFile(filename) {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer "${filename}" ?`)) {
        return;
    }
    
    fetch(`/api/delete/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Supprimer la carte du DOM
            const card = document.querySelector(`[data-filename="${filename}"]`);
            if (card) {
                card.style.animation = 'fadeOut 0.3s ease';
                setTimeout(() => {
                    card.remove();
                    updateFileCount();
                    
                    // Afficher l'état vide si plus de fichiers
                    if (documentsList.children.length === 0) {
                        showEmptyState();
                    }
                }, 300);
            }
        } else {
            alert('Erreur lors de la suppression : ' + data.error);
        }
    })
    .catch(error => {
        alert('Erreur réseau lors de la suppression');
        console.error(error);
    });
}

function refreshFileList() {
    fetch('/api/files')
        .then(response => response.json())
        .then(data => {
            documentsList.innerHTML = '';
            
            if (data.files.length === 0) {
                showEmptyState();
            } else {
                data.files.forEach(fileInfo => {
                    // Créer la carte sans l'ajouter (pour éviter la duplication)
                    const card = document.createElement('div');
                    card.className = 'document-card';
                    card.setAttribute('data-filename', fileInfo.name);
                    
                    let icon = '📄';
                    if (fileInfo.name.endsWith('.pdf')) icon = '📕';
                    else if (fileInfo.name.endsWith('.txt')) icon = '📝';
                    else if (fileInfo.name.endsWith('.md')) icon = '📗';
                    else if (fileInfo.name.endsWith('.doc') || fileInfo.name.endsWith('.docx')) icon = '📘';
                    
                    const sizeKB = (fileInfo.size / 1024).toFixed(2);
                    
                    card.innerHTML = `
                        <div class="document-icon">${icon}</div>
                        <div class="document-info">
                            <div class="document-name">${fileInfo.name}</div>
                            <div class="document-meta">
                                <span class="document-size">${sizeKB} KB</span>
                                <span class="document-date">${fileInfo.date}</span>
                            </div>
                        </div>
                        <button class="delete-button" onclick="deleteFile('${fileInfo.name}')">
                            🗑️
                        </button>
                    `;
                    
                    documentsList.appendChild(card);
                });
            }
            
            updateFileCount();
        })
        .catch(error => {
            console.error('Erreur lors du rafraîchissement:', error);
        });
}

function showEmptyState() {
    documentsList.innerHTML = `
        <div class="empty-state" id="emptyState">
            <div class="empty-icon">📭</div>
            <p>Aucun document uploadé pour le moment</p>
            <p class="empty-hint">Commencez par ajouter des documents ci-dessus</p>
        </div>
    `;
}

function updateFileCount() {
    const cards = documentsList.querySelectorAll('.document-card');
    const count = cards.length;
    
    fileCount.textContent = count;
    
    // Activer/désactiver les boutons
    const deleteAllButton = document.getElementById('deleteAllButton');
    if (count > 0) {
        nextStepButton.disabled = false;
        nextStepMessage.textContent = `Vous avez ${count} document(s). Passez à l'indexation !`;
        if (deleteAllButton) deleteAllButton.disabled = false;
    } else {
        nextStepButton.disabled = true;
        nextStepMessage.textContent = 'Uploadez au moins un document pour continuer.';
        if (deleteAllButton) deleteAllButton.disabled = true;
    }
}

function deleteAllFiles() {
    const count = documentsList.querySelectorAll('.document-card').length;
    
    if (count === 0) return;
    
    if (!confirm(`Êtes-vous sûr de vouloir supprimer tous les ${count} document(s) ?`)) {
        return;
    }
    
    fetch('/api/delete-all', {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Supprimer toutes les cartes
            documentsList.innerHTML = '';
            showEmptyState();
            updateFileCount();
            alert(`${data.count} fichier(s) supprimé(s) avec succès`);
        } else {
            alert('Erreur lors de la suppression : ' + data.error);
        }
    })
    .catch(error => {
        alert('Erreur réseau lors de la suppression');
        console.error(error);
    });
}

// Animation de disparition
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(-20px);
        }
    }
`;
document.head.appendChild(style);
