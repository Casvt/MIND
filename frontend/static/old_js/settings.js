const settingsEls = {
	settings: {
		showClock: document.querySelector('#clock-input'),
		locale: document.querySelector('#locale-input'),
		defaultService: document.querySelector('#default-service-input'),
	},
	editAccount: {
		start: document.querySelector("#start-edit-account"),
		dialog: document.querySelector("#edit-account-dialog"),
		form: document.querySelector("#edit-account-form"),
		close: document.querySelector("#close-edit-account"),
		inputContainers: {
			username: document.querySelector("#edit-account-form .checked-input-container:has(input[type='text'])")
		},
		inputs: {
			username: document.querySelector("#edit-account-username-input"),
			password: document.querySelector("#edit-account-password-input")
		},
		errors: {
			usernameInvalid: document.querySelector('#edit-invalid-username-error'),
			usernameTaken: document.querySelector('#edit-taken-username-error')
		}
	},
	deleteAccount: {
		dialog: document.querySelector('#delete-user-dialog'),
		close: document.querySelector('#close-delete-user'),
		confirm: document.querySelector('#confirm-delete-user'),
		button: document.querySelector('#delete-account-button')
	}
}

function loadSettings() {
	const values = getLocalStorage()
	settingsEls.settings.locale.value = values['locale']
	settingsEls.settings.showClock.value = values['show_clock']
	// Default Service is handled by notification.fillNotificationSelection()
}

function updateLocale() {
	setLocalStorage({'locale': settingsEls.settings.locale.value})
	fillLibrary(reminderTypes.reminder)
	setupClock()
}

function updateDefaultService() {
	setLocalStorage({'default_service': parseInt(settingsEls.settings.defaultService.value)})
	// Add window is handled by show.showAdd()
}

function updateClockSetting() {
	setLocalStorage({'show_clock': settingsEls.settings.showClock.value})
	setupClock()
}

function openEditAccount() {
	settingsEls.editAccount.inputContainers.username.classList.remove('error-input-container')
	hide([settingsEls.editAccount.errors.usernameInvalid, settingsEls.editAccount.errors.usernameTaken])
	settingsEls.editAccount.inputs.username.value = ''
	settingsEls.editAccount.inputs.password.value = ''

	settingsEls.editAccount.dialog.showModal()
}

function closeEditAccount() {
	settingsEls.editAccount.dialog.close()
}

function editAccount() {
	settingsEls.editAccount.inputContainers.username.classList.remove('error-input-container')
	hide([settingsEls.editAccount.errors.usernameInvalid, settingsEls.editAccount.errors.usernameTaken])

	const data = {}

	if (settingsEls.editAccount.inputs.username.value !== '')
		data.new_username = settingsEls.editAccount.inputs.username.value

	if (settingsEls.editAccount.inputs.password.value !== '')
		data.new_password = settingsEls.editAccount.inputs.password.value

	if (Object.keys(data).length === 0) {
		// Nothing changed
		closeEditAccount()
		return
	}

	sendAPI("PUT", "/user", {}, data)
	.then(json => {
		closeEditAccount()
	})
	.catch(e => {
		e.json().then(e => {
			if (e.error === 'UsernameInvalid') {
				settingsEls.editAccount.errors.usernameInvalid.innerText = e.result.reason
				hide([], [settingsEls.editAccount.errors.usernameInvalid])
				settingsEls.editAccount.inputContainers.username.classList.add('error-input-container')

			} else if (e.error === 'UsernameTaken') {
				hide([], [settingsEls.editAccount.errors.usernameTaken])
				settingsEls.editAccount.inputContainers.username.classList.add('error-input-container')

			} else {
				console.log(e)
			}
		})
	})
}

function deleteAccount() {
	sendAPI("DELETE", "/user")
	.then(response => {
		window.location.href = `${urlPrefix}/`
	})
}

loadSettings()

settingsEls.settings.showClock.onchange = e => updateClockSetting()
settingsEls.settings.locale.onchange = e => updateLocale()
settingsEls.settings.defaultService.onchange = e => updateDefaultService()
settingsEls.deleteAccount.button.onclick = e => 
	settingsEls.deleteAccount.dialog.showModal()

settingsEls.editAccount.start.onclick = e => openEditAccount()
settingsEls.editAccount.dialog.onclick = e => {
	if (e.target === e.currentTarget) {
		e.stopPropagation()
		closeEditAccount()
	}
}
settingsEls.editAccount.form.action = 'javascript:editAccount()'
settingsEls.editAccount.close.onclick = e => closeEditAccount()

settingsEls.deleteAccount.dialog.onclick = e => {
	if (e.target === e.currentTarget) {
		e.stopPropagation()
		settingsEls.deleteAccount.dialog.close()
	}
}
settingsEls.deleteAccount.close.onclick = e => settingsEls.deleteAccount.dialog.close()
settingsEls.deleteAccount.confirm.onclick = e => deleteAccount()
