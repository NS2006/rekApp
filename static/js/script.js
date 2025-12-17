document.addEventListener('DOMContentLoaded', function() {
    const videoFileInput = document.getElementById('videoFile');
    const fileNameDisplay = document.getElementById('fileName');
    const uploadForm = document.getElementById('uploadForm');
    const previewContainer = document.getElementById('previewContainer');
    const videoPreview = document.getElementById('videoPreview');
    const uploadArea = document.getElementById('uploadArea');
    const loading = document.getElementById('loading');
    
    // Handle file selection
    videoFileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            fileNameDisplay.textContent = file.name;
            
            // Show video preview
            const url = URL.createObjectURL(file);
            videoPreview.src = url;
            previewContainer.style.display = 'block';
            
            // Load the video for preview
            videoPreview.load();
        }
    });
    
    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const file = videoFileInput.files[0];
        if (!file) {
            alert('Please select a video file first.');
            return;
        }
        
        // Show loading state
        uploadArea.style.display = 'none';
        loading.style.display = 'flex';
        
        // Create FormData and send request
        const formData = new FormData();
        formData.append('video', file);
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = data.redirect;
            } else {
                alert(data.error || 'Upload failed. Please try again.');
                loading.style.display = 'none';
                uploadArea.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
            loading.style.display = 'none';
            uploadArea.style.display = 'block';
        });
    });
});