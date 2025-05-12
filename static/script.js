document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    const loadingMessage = document.getElementById('loadingMessage'); // Updated ID
    const uploadProgressBarContainer = document.getElementById('uploadProgressBarContainer');
    const uploadProgressBar = document.getElementById('uploadProgressBar');

    function initEventListeners() {
        fileInput.addEventListener('change', handleFileSelect);
        dropZone.addEventListener('dragover', handleDragOver);
        dropZone.addEventListener('dragleave', handleDragLeave);
        dropZone.addEventListener('drop', handleDrop);
    }

    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) processFile(file);
    }

    function handleDragOver(e) {
        e.preventDefault();
        dropZone.style.borderColor = '#76c7c0'; // New color: Teal
        dropZone.style.backgroundColor = 'rgba(118, 199, 192, 0.1)'; // Lighter Teal
    }

    function handleDragLeave(e) {
        e.preventDefault();
        resetDropZoneStyles();
    }

    function handleDrop(e) {
        e.preventDefault();
        resetDropZoneStyles();
        const file = e.dataTransfer.files[0];
        if (file) processFile(file);
    }

    function resetDropZoneStyles() {
        dropZone.style.borderColor = '#d1d8e0'; // New color: Light Grey
        dropZone.style.backgroundColor = 'transparent';
    }

    function processFile(file) {
        const fileExt = file.name.split('.').pop().toLowerCase();
        if (!['cob', 'txt'].includes(fileExt)) {
            alert('Only .cob and .txt files are allowed');
            return;
        }

        fileInfo.textContent = `Selected file: ${file.name}`;
        loadingMessage.style.display = 'block'; // Show processing message
        uploadProgressBarContainer.style.display = 'block';
        uploadProgressBar.style.width = '0%';

        const formData = new FormData();
        formData.append('file', file);

        // Simulate progress for upload - replace with actual XHR progress if available
        let progress = 0;
        const interval = setInterval(() => {
            progress += 10;
            uploadProgressBar.style.width = progress + '%';
            if (progress >= 100) {
                clearInterval(interval);
            }
        }, 100); // Adjust timing as needed

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            clearInterval(interval); // Clear interval on response
            uploadProgressBar.style.width = '100%'; // Ensure it's full on completion
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            if (data.conversion_id) {
                // Redirect to results page
                window.location.href = `/results/${data.conversion_id}`;
            } else {
                throw new Error('Conversion ID not received.');
            }
        })
        .catch(error => {
            clearInterval(interval);
            console.error('Error:', error);
            alert(`Processing failed: ${error.message}`);
            loadingMessage.style.display = 'none';
            uploadProgressBarContainer.style.display = 'none';
            uploadProgressBar.style.width = '0%';
        });
    }

    initEventListeners();
});