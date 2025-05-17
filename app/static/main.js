document.getElementById('generateBtn').addEventListener('click', function() {
    const formData = new FormData();
    formData.append('dummy', 'value'); // You can remove or adjust this based on your actual backend needs

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
        // ✅ Update the presentation count without refreshing the page
        document.getElementById('presentationsRemaining').textContent = data.presentations_remaining;
        alert(data.message);
    })
    .catch(error => {
        if (error.error === 'limit_reached') {
            alert(error.message);
            // Optionally redirect to pricing page
            window.location.href = '/pricing';
        } else {
            alert("An unexpected error occurred. Please try again.");
            console.error(error);
        }
    });
});

// Test comment
