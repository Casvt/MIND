const login_inputs = {
	'username': document.querySelector('#login-form > input[type="text"]'),
	'password': document.querySelector('#login-form > input[type="password"]')
};

const login_errors = {
	'username': document.getElementById('username-error'),
	'password': document.getElementById('password-error')
};

const create_inputs = {
	'username': document.querySelector('#create-form > input[type="text"]'),
	'password': document.querySelector('#create-form > input[type="password"]')
}

const create_errors = {
	'username_invalid': document.getElementById('new-username-error'),
	'username_taken': document.getElementById('taken-username-error'),
};

function toggleWindow() {
	document.querySelector('main').classList.toggle('show-create');
};

function login(data=null) {
	login_inputs.username.classList.remove('error-input');
	login_errors.username.classList.add('hidden');
	login_inputs.password.classList.remove('error-input');
	login_errors.password.classList.add('hidden');

	if (data === null)
		data = {
			'username': login_inputs.username.value,
			'password': login_inputs.password.value
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
		localStorage.setItem('MIND_api_key', json.result.api_key);
		window.location.href = `${url_prefix}/reminders`;
	})
	.catch(e => {
		if (e === 401) {
			login_inputs.password.classList.add('error-input');
			login_errors.password.classList.remove('hidden');
		} else if (e === 404) {
			login_inputs.username.classList.add('error-input');
			login_errors.username.classList.remove('hidden');
		} else {
			console.log(e);
		};
	});
};

function create() {
	create_inputs.username.classList.remove('error-input');
	create_errors.username_invalid.classList.add('hidden');
	create_errors.username_taken.classList.add('hidden');

	const data = {
		'username': create_inputs.username.value,
		'password': create_inputs.password.value
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
			create_inputs.username.classList.add('error-input');
			create_errors.username_invalid.classList.remove('hidden');
		} else if (e === 'UsernameTaken') {
			create_inputs.username.classList.add('error-input');
			create_errors.username_taken.classList.remove('hidden');
		} else {
			console.log(e);
		};
	});
};

function checkLogin() {
	fetch(`${url_prefix}/api/auth/status?api_key=${localStorage.getItem('MIND_api_key')}`)
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);
		window.location.href = '/reminders';
	})
	.catch(e => {
		if (e === 401)
			console.log('API key expired')
		else
			console.log(e);
	});
};

// code run on load

const url_prefix = document.getElementById('url_prefix').dataset.value;

checkLogin();

document.getElementById('login-form').setAttribute('action', 'javascript:login();');
document.getElementById('create-form').setAttribute('action', 'javascript:create();');
document.querySelectorAll('.switch-button').forEach(e => e.addEventListener('click', e => toggleWindow()));
