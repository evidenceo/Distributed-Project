document.addEventListener('DOMContentLoaded', function() {
    var setupForm = document.getElementById('setupForm');

    setupForm.addEventListener('submit', function(event) {
        event.preventDefault();

        // Gather data from the form
        var lastPeriodDate = document.getElementById('lastPeriodDate').value;
        var averagePeriodLength = document.getElementById('averagePeriodLength').value;
        var averageCycleLength = document.getElementById('averageCycleLength').value;

        // Construct an object to send in the request
        var setupData = {
            lastPeriodDate: lastPeriodDate,
            averagePeriodLength: averagePeriodLength,
            averageCycleLength: averageCycleLength
        };

        // Send data to your backend
        fetch('/setup', {  // Replace '/setup' with your backend route for handling setup data
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(setupData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                window.location.href = '/main'; // Redirect to the main page after successful setup
            } else {
                alert('Setup failed: ' + data.message); // Show error message
            }
        })
        .catch(error => {
            console.error('Error during setup:', error);
            alert('Error during setup. Please try again.');
        });
    });
});
