const els = {
    switchButton: document.querySelector(".switch-button"),
	login: {
		form: document.querySelector('#login-form'),
        inputContainers: {
			username: document.querySelector('#login-form .checked-input-container:has(input[type="text"])'),
			password: document.querySelector('#login-form .checked-input-container:has(input[type="password"])')
        },
		inputs: {
			username: document.querySelector('#login-username-input'),
			password: document.querySelector('#login-password-input')
		}
	},
	create: {
		form: document.querySelector('#register-form'),
        inputContainers: {
			username: document.querySelector('#register-form .checked-input-container:has(input[type="text"])'),
        },
		inputs: {
			username: document.querySelector('#register-username-input'),
			password: document.querySelector('#register-password-input')
		},
		errors: {
			usernameInvalid: document.querySelector('#invalid-username-error'),
			usernameTaken: document.querySelector('#taken-username-error')
		}
	}
}

function login(data = null) {
	els.login.inputContainers.username.classList.remove('error-input-container')
	els.login.inputContainers.password.classList.remove('error-input-container')

	if (data === null)
		data = {
			username: els.login.inputs.username.value,
			password: els.login.inputs.password.value
		}

	sendAPI("POST", "/auth/login", {}, data, true, false)
	.then(json => {
		setLocalStorage({api_key: json.result.api_key})
		if (json.result.admin)
			window.location.href = `${urlPrefix}/admin`
		else
			window.location.href = `${urlPrefix}/reminders`
	})
	.catch(e => {
		if (e.status === 404)
			els.login.inputContainers.username.classList.add('error-input-container')
		else if (e.status === 401)
			els.login.inputContainers.password.classList.add('error-input-container')
		else
			console.log(e)
	})
}

function create() {
	els.create.inputContainers.username.classList.remove('error-input-container')
	hide([els.create.errors.usernameInvalid, els.create.errors.usernameTaken])

	const data = {
		username: els.create.inputs.username.value,
		password: els.create.inputs.password.value
	}

	sendAPI("POST", "/user/add", {}, data)
	.then(json => login(data))
	.catch(e => {
		e.json().then(e => {
			if (e.error === 'UsernameInvalid') {
				els.create.errors.usernameInvalid.innerText = e.result.reason
				hide([], [els.create.errors.usernameInvalid])
				els.create.inputContainers.username.classList.add('error-input-container')

			} else if (e.error === 'UsernameTaken') {
				hide([], [els.create.errors.usernameTaken])
				els.create.inputContainers.username.classList.add('error-input-container')

			} else {
				console.log(e)
			}
		})
	})
}

function checkAllowNewAccounts() {
	const cachedValue = getLocalStorage("allow_new_accounts_cache").allow_new_accounts_cache
	if (!cachedValue)
		hide([els.switchButton])

	fetchAPI("/settings")
	.then(json => {
		if (!json.result.allow_new_accounts)
			hide([els.switchButton])
		else
			hide([], [els.switchButton])

		if (cachedValue !== json.result.allow_new_accounts)
			setLocalStorage({
				allow_new_accounts_cache: json.result.allow_new_accounts
			})
	})
}

if (apiKey !== null)
	checkLogin()

checkAllowNewAccounts()

els.login.form.action = 'javascript:login();'
els.create.form.action = 'javascript:create();'
