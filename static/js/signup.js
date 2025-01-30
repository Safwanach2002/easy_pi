//signup_section

document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    /*console.log('Form:', form);*/

    if (!form) {
        console.error('Form element not found. Ensure the form selector is correct.');
        return;
    }

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const formData = new FormData(form);

        // Append referral code if already provided in the popup
        const referralCodeInput = document.getElementById('referralCodeInput');
        if (referralCodeInput && referralCodeInput.value.trim() !== '') {
            formData.append('referred_by', referralCodeInput.value.trim());
        }

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
            });

            // Validate response
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Result JSON:',result);

            if (result.success) {
                const referralCode = result.referral_code;
                document.getElementById('Who_referred_by').textContent = referralCode;
                openReferralPopup();
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

function openReferralPopup() {
    const overlay = document.getElementById('referralOverlay');
    const popup = document.getElementById('referralPopup');

    if (overlay && popup) {
        overlay.style.display = 'block';
        popup.style.display = 'block';
    } else {
        console.warn('Referral popup elements not found.');
    }
}

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

// Show the referral popup with the user's referral code
function showReferralPopup(referralCode) {
    document.getElementById('Who_referred_by').innerText = referralCode;
    document.getElementById('referralOverlay').style.display = 'block';
    document.getElementById('referralPopup').style.display = 'block';
}

function submitReferralCode() {
    const referralCodeInput = document.getElementById('referralCodeInput');
    const referralCode = referralCodeInput ? referralCodeInput.value.trim() : '';

    if (referralCode === '') {
        alert('Please enter a referral code or click skip.');
        return;
    }

    // Attach the referral code to the form as a hidden input
    const form = document.querySelector('form');
    if (!form) {
        console.error('Form element not found. Ensure the form selector is correct.');
        return;
    }

    let referredByInput = document.querySelector('input[name="referred_by"]');

    if (!referredByInput) {
        referredByInput = document.createElement('input');
        referredByInput.type = 'hidden';
        referredByInput.name = 'referred_by';
        form.appendChild(referredByInput);
    }

    referredByInput.value = referralCode.trim();

    alert(`Referral code ${referralCode} submitted!`);
    closeReferralPopup();

       // Redirect to the home page
       window.location.href = '/';
    }
    function skipReferral() {
        closeReferralPopup();

        // Redirect to the home page
        window.location.href = '/';
    }