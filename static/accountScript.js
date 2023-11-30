function confirmDelete() {
        if (confirm("Are you sure you want to delete your account? It is permanent and you will lose all your information.")) {
            fetch('/delete_account', { method: 'POST' , headers: {'Content-Type': 'application/json'}})
            .then(response => response.json())
             .then(data => {
             if (data.success) {
             alert(data.message);
             window.location.href = '/';
             }
             })
             .catch(error => console.error('Error:', error))

        }
    }