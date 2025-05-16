document.getElementById('generateBtn').addEventListener('click', function() {
    const formData = new FormData();
    formData.append('dummy', 'value'); // Example data, adjust if necessary

    fetch('/generate_presentation', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(error => { throw error });
        }
        return response.json();
    })
    .then(data => {
        // Update the count dynamically
        document.getElementById('presentationsRemaining').textContent = data.presentations_remaining;
        alert(data.message);
    })
    .catch(error => {
        if (error.error === 'limit_reached') {
            alert(error.message);
            window.location.href = '/pricing';
        } else {
            alert("An unexpected error occurred. Please try again.");
        }
    });
});
