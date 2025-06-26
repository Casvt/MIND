const settingsEls = {
	settings: {
		locale: document.querySelector('#locale-input'),
		defaultService: document.querySelector('#default-service-input'),
	},
	changePassword: {
		form: document.querySelector('#change-password-form'),
		input: document.querySelector('#change-password-input'),
		submit: document.querySelector('#change-password-form button')
	},
	deleteAccount: {
		dialog: document.querySelector('#delete-user-dialog'),
		close: document.querySelector('#close-delete-user'),
		confirm: document.querySelector('#confirm-delete-user'),
		button: document.querySelector('#delete-account-button')
	}
}

function loadSettings() {
	settingsEls.settings.locale.value =
		getLocalStorage('locale')['locale']
	// Default Service is handled by notification.fillNotificationSelection()
}

function updateLocale() {
	setLocalStorage({'locale': settingsEls.settings.locale.value})
	fillLibrary(reminderTypes.reminder)
}

function updateDefaultService() {
	setLocalStorage({'default_service': parseInt(settingsEls.settings.defaultService.value)})
	// Add window is handled by show.showAdd()
}

function changePassword() {
	const data = {
		'new_password': settingsEls.changePassword.input.value
	}
	sendAPI("PUT", "/user", {}, data)
	.then(response => {
		settingsEls.changePassword.input.value = ""
		settingsEls.changePassword.submit.style.backgroundColor = "var(--color-success)"
		settingsEls.changePassword.submit.innerText = "Changed"
		setTimeout(() => {
				settingsEls.changePassword.submit.style.backgroundColor = ""
				settingsEls.changePassword.submit.innerText = "Change"
			},
			2000
		)
	})
	.catch(e => console.log(e))
}

function deleteAccount() {
	sendAPI("DELETE", "/user")
	.then(response => {
		window.location.href = `${urlPrefix}/`
	})
}

loadSettings()

settingsEls.settings.locale.onchange = e => updateLocale()
settingsEls.settings.defaultService.onchange = e => updateDefaultService()
settingsEls.changePassword.form.action = 'javascript:changePassword();'
settingsEls.deleteAccount.button.onclick = e => 
	settingsEls.deleteAccount.dialog.showModal()

settingsEls.deleteAccount.dialog.onclick = e => {
	if (e.target === e.currentTarget) {
		e.stopPropagation()
		settingsEls.deleteAccount.dialog.close()
	}
}
settingsEls.deleteAccount.close.onclick = e => settingsEls.deleteAccount.dialog.close()
settingsEls.deleteAccount.confirm.onclick = e => deleteAccount()
