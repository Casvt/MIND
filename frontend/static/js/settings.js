function changePassword() {
	const data = {
		'new_password': document.getElementById('password-input').value
	};
	fetch(`/api/user?api_key=${api_key}`, {
		'method': 'PUT',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		window.location.reload();
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		} else {
			console.log(e);
		};
	});
};

function deleteAccount() {
	fetch(`/api/user?api_key=${api_key}`, {
		'method': 'DELETE'
	})
	.then(response => {
		window.location.href = '/';
	});
};

// code run on load

document.getElementById('change-password-form').setAttribute('action', 'javascript:changePassword()');
document.getElementById('delete-account-button').addEventListener('click', e => deleteAccount());
