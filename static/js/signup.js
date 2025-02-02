document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');

    if (!form) {
        console.error('Form element not found. Ensure the form selector is correct.');
        return;
    }

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest', // To identify AJAX requests
                },
            });

            if (!response.ok) {
                throw new Error('HTTP error! Status: ${response.status}');
            }

            const result = await response.json();
            console.log('Result JSON:', result);

            if (result.success) {
                // Show the referral popup with the generated referral code
                showReferralPopup(result.referral_code);
            } else {
                let errorMessage = 'Signup failed. Please try again.';
                if (result.errors) {
                    errorMessage = Object.values(result.errors).join(', ');
                }
                alert(errorMessage);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred. Please try again later.');
        }
    });
});

// Show the referral popup with the user's referral code
function showReferralPopup(referralCode) {
    const referralCodeElement = document.getElementById('Who_referred_by');
    const overlay = document.getElementById('referralOverlay');
    const popup = document.getElementById('referralPopup');

    if (referralCodeElement && overlay && popup) {
        referralCodeElement.textContent = referralCode;
        overlay.style.display = 'block';
        popup.style.display = 'block';
    } else {
        console.warn('Referral popup elements not found.');
    }
}

// Close the referral popup
function closeReferralPopup() {
    const overlay = document.getElementById('referralOverlay');
    const popup = document.getElementById('referralPopup');

    if (overlay && popup) {
        overlay.style.display = 'none';
        popup.style.display = 'none';
    } else {
        console.warn('Referral popup elements not found.');
    }
}

// Submit the referral code
function submitReferralCode() {
    const referralCodeInput = document.getElementById('referralCodeInput');
    const referralCode = referralCodeInput ? referralCodeInput.value.trim() : '';

    if (referralCode === '') {
        alert('Please enter a referral code or click skip.');
        return;
    }

    // Send the referral code to the server
    fetch('/EPI_App/submit-referral/', {  // Include the prefix
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ referral_code: referralCode }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert('Referral code submitted successfully!');
            closeReferralPopup();
            window.location.href = '/'; // Redirect to home page
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please try again later.');
    });
}

// Skip the referral process
function skipReferral() {
    closeReferralPopup();
    window.location.href = '/'; // Redirect to home page
}

// Helper function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}