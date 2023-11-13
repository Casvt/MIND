const setting_inputs = {
	'allow_new_accounts': document.querySelector('#allow-new-accounts-input')
};

function checkLogin() {
	fetch(`${url_prefix}/api/auth/status?api_key=${api_key}`)
	.then(response => {
		if (!response.ok) return Promise.reject(response.status)
		return response.json();
	})
	.then(json => {
		if (!json.result.admin)
			window.location.href = `${url_prefix}/reminders`;
	})
	.catch(e => {
		if (e === 401)
			window.location.href = `${url_prefix}/`;
		else
			console.log(e);
	});
};

function loadSettings() {
	fetch(`${url_prefix}/api/settings`)
	.then(response => response.json())
	.then(json => {
		setting_inputs.allow_new_accounts.checked = json.result.allow_new_accounts;
	});
};

function submitSettings() {
	const data = {
		'allow_new_accounts': setting_inputs.allow_new_accounts.checked
	};
	console.log(data);
	fetch(`${url_prefix}/api/admin/settings?api_key=${api_key}`, {
		'method': 'PUT',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => response.json())
	.then(json => {
		if (json.error !== null)
			return Promise.reject(json)
	})
	.catch(json => {
		if (['ApiKeyInvalid', 'ApiKeyExpired'].includes(json.error))
			window.location.href = `${url_prefix}/`;
	});
};

// code run on load

checkLogin();
loadSettings();

document.querySelector('#logout-button').onclick = (e) => logout();
document.querySelector('#settings-form').action = 'javascript:submitSettings();';
