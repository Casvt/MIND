function loadSettings() {
	document.getElementById('locale-input').value = JSON.parse(localStorage.getItem('MIND')).locale;
};

function changePassword() {
	const data = {
		'new_password': document.getElementById('password-input').value
	};
	fetch(`${url_prefix}/api/user?api_key=${api_key}`, {
		'method': 'PUT',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);
		window.location.reload();
	})
	.catch(e => {
		if (e === 401)
			window.location.href = `${url_prefix}/`;
		else
			console.log(e);
	});
};

function updateLocale(e) {
	const new_stor = JSON.parse(localStorage.getItem('MIND'));
	new_stor.locale = e.target.value;
	localStorage.setItem('MIND', JSON.stringify(new_stor));
	window.location.reload();
};

function deleteAccount() {
	fetch(`${url_prefix}/api/user?api_key=${api_key}`, {
		'method': 'DELETE'
	})
	.then(response => {
		window.location.href = `${url_prefix}/`;
	});
};

// code run on load

loadSettings();

document.getElementById('change-password-form').setAttribute('action', 'javascript:changePassword()');
document.getElementById('locale-input').addEventListener('change', updateLocale);
document.getElementById('delete-account-button').addEventListener('click', e => deleteAccount());
