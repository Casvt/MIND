const forms = {
	'login': {
		'form': document.querySelector('#login-form'),
		'inputs': {
			'username': document.querySelector('#login-form input[type="text"]'),
			'password': document.querySelector('#login-form input[type="password"]')
		},
		'errors': {
			'username': document.querySelector("#username-error-container"),
			'password': document.querySelector("#password-error-container")
		}
	},
	'create': {
		'form': document.querySelector('#create-form'),
		'inputs': {
			'username': document.querySelector('#create-form input[type="text"]'),
			'password': document.querySelector('#create-form input[type="password"]')
		},
		'errors': {
			'username_invalid': document.querySelector('#new-username-error'),
			'username_taken': document.querySelector('#taken-username-error')
		}
	}
};

function login(data=null) {
	forms.login.errors.username.classList.remove('error-container');
	forms.login.errors.password.classList.remove('error-container');

	if (data === null)
		data = {
			'username': forms.login.inputs.username.value,
			'password': forms.login.inputs.password.value
		};

	fetch(`${url_prefix}/api/auth/login`, {
		'method': 'POST',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);
		return response.json();
	})
	.then(json => {
		const new_stor = JSON.parse(localStorage.getItem('MIND'));
		new_stor.api_key = json.result.api_key;
		localStorage.setItem('MIND', JSON.stringify(new_stor));
		if (json.result.admin)
			window.location.href = `${url_prefix}/admin`;
		else
			window.location.href = `${url_prefix}/reminders`;
	})
	.catch(e => {
		if (e === 404)
			forms.login.errors.username.classList.add('error-container');
		else if (e === 401)
			forms.login.errors.password.classList.add('error-container');
		else
			console.log(e);
	});
};

function create() {
	forms.create.inputs.username.classList.remove('error-input');
	forms.create.errors.username_invalid.classList.add('hidden');
	forms.create.errors.username_taken.classList.add('hidden');

	const data = {
		'username': forms.create.inputs.username.value,
		'password': forms.create.inputs.password.value
	};
	fetch(`${url_prefix}/api/user/add`, {
		'method': 'POST',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => response.json())
	.then(json => {
		if (json.error !== null) return Promise.reject(json.error);
		login(data);
	})
	.catch(e => {
		if (e === 'UsernameInvalid') {
			forms.create.inputs.username.classList.add('error-input');
			forms.create.errors.username_invalid.classList.remove('hidden');
		} else if (e === 'UsernameTaken') {
			forms.create.inputs.username.classList.add('error-input');
			forms.create.errors.username_taken.classList.remove('hidden');
		} else {
			console.log(e);
		};
	});
};

function checkLogin() {
	fetch(`${url_prefix}/api/auth/status?api_key=${api_key}`)
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);
		return response.json();
	})
	.then(json => {
		if (json.result.admin)
			window.location.href = `${url_prefix}/admin`;
		else
			window.location.href = `${url_prefix}/reminders`;
	})
	.catch(e => {
		if (e === 401)
			console.log('API key expired')
		else
			console.log(e);
	});
};

function checkAllowNewAccounts() {
	fetch(`${url_prefix}/api/settings`)
	.then(response => response.json())
	.then(json => {
		if (!json.result.allow_new_accounts)
			document.querySelector('.switch-button').classList.add('hidden');
	});
};

// code run on load

if (localStorage.getItem('MIND') === null)
	localStorage.setItem('MIND', JSON.stringify(
		{'api_key': null, 'locale': 'en-GB', 'default_service': null}
	))

const url_prefix = document.getElementById('url_prefix').dataset.value;
const api_key = JSON.parse(localStorage.getItem('MIND')).api_key;

checkLogin();
checkAllowNewAccounts();

forms.login.form.action = 'javascript:login();';
forms.create.form.action = 'javascript:create();';
