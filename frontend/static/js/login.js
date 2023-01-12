function login(data=null) {
	document.getElementById('username-error').classList.add('hidden');
	document.getElementById('username-input').classList.remove('error-input');
	document.getElementById('password-error').classList.add('hidden');
	document.getElementById('password-input').classList.remove('error-input');

	if (data === null) {
		data = {
			'username': document.getElementById('username-input').value,
			'password': document.getElementById('password-input').value
		};
	};
	fetch(`/api/auth/login`, {
		'method': 'POST',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		
		return response.json();
	})
	.then(json => {
		sessionStorage.setItem('api_key', json.result.api_key);
		window.location.href = '/reminders';
	})
	.catch(e => {
		if (e === 401) {
			document.getElementById('password-error').classList.remove('hidden');
			document.getElementById('password-input').classList.add('error-input');
		} else if (e === 404) {
			document.getElementById('username-error').classList.remove('hidden');
			document.getElementById('username-input').classList.add('error-input');
		} else {
			console.log(e);
		};
	});
};

function create() {
	document.getElementById('new-username-error').classList.add('hidden');
	document.getElementById('new-username-input').classList.remove('error-input');
	document.getElementById('taken-username-error').classList.add('hidden');

	const data = {
		'username': document.getElementById('new-username-input').value,
		'password': document.getElementById('new-password-input').value
	};
	fetch(`/api/user/add`, {
		'method': 'POST',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => response.json() )
	.then(json => {
		// catch errors
		if (json.error !== null) {
			return Promise.reject(json.error);
		};
		login(data);
	})
	.catch(e => {
		if (e === 'UsernameInvalid') {
			document.getElementById('new-username-error').classList.remove('hidden');
			document.getElementById('new-username-input').classList.add('error-input');
		} else if (e === 'UsernameTaken') {
			document.getElementById('taken-username-error').classList.remove('hidden');
			document.getElementById('new-username-input').classList.add('error-input');
		} else {
			console.log(e);
		};
	});
}

function toggleWindow() {
	document.querySelector('main').classList.toggle('show-create');
};

// code run on load

document.getElementById('login-form').setAttribute('action', 'javascript:login();');
document.getElementById('create-form').setAttribute('action', 'javascript:create();');
document.querySelectorAll('.switch-button').forEach(e => e.addEventListener('click', e => toggleWindow()));
