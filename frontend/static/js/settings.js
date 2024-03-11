const SettingsEls = {
	locale_input: document.querySelector('#locale-input'),
	default_service_input: document.querySelector('#default-service-input'),
	change_password_form: document.querySelector('#change-password-form'),
	delete_account_button: document.querySelector('#delete-account-button')
};

function loadSettings() {
	// Default Service is handled by notification.fillNotificationSelection()
	document.getElementById('locale-input').value =
		getLocalStorage('locale')['locale'];
};

function updateLocale(e) {
	setLocalStorage({'locale': e.target.value});
	fillLibrary(Types.reminder);
};

function updateDefaultService(e) {
	setLocalStorage({'default_service': parseInt(e.target.value)});
	// Add window is handled by show.showAdd()
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

SettingsEls.locale_input.onchange = updateLocale;
SettingsEls.default_service_input.onchange = updateDefaultService;
SettingsEls.change_password_form.action = 'javascript:changePassword();';
SettingsEls.delete_account_button.onclick = e => deleteAccount();