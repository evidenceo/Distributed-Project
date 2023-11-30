// login.html
document.addEventListener('DOMContentLoaded', function() {
    var loginForm = document.getElementById('loginForm');

    loginForm.addEventListener('submit', function(event) {
        event.preventDefault();

        var email = document.getElementById('loginEmail').value;
        var password = document.getElementById('loginPassword').value;

        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({email: email, password: password})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Check if the user needs to complete the setup
                fetch('/check-user-data')
                .then(response => response.json())
                .then(data => {
                    if (data.needs_setup) {
                        window.location.href = '/setup';
                    } else {
                        // Since user is logged in, go to main page
                        // The main page will handle loading the calendar
                        window.location.href = '/main';
                    }
                });
            } else {
                throw new Error('Login failed: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error during login:', error);
            alert(error.message);
        });
    });
});







