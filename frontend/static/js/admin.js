//
// region Elements
//
const windows = {
	resetSettings: {
		dialog: document.querySelector("#reset-settings-dialog"),
		form: document.querySelector("#reset-settings-form"),
		close: document.querySelector("#close-reset-settings"),
		submit: document.querySelector("#submit-reset-button")
	},
	addUser: {
		dialog: document.querySelector("#add-user-dialog"),
		form: document.querySelector("#add-user-form"),
		close: document.querySelector("#close-add-user"),
		inputContainers: {
			username: document.querySelector("#add-user-form .checked-input-container:has(input[type='text'])")
		},
		inputs: {
			username: document.querySelector("#add-user-username-input"),
			password: document.querySelector("#add-user-password-input")
		},
		errors: {
			usernameInvalid: document.querySelector('#add-invalid-username-error'),
			usernameTaken: document.querySelector('#add-taken-username-error')
		}
	},
	editUser: {
		dialog: document.querySelector("#edit-user-dialog"),
		username: document.querySelector("#username-edit-user"),
		form: document.querySelector("#edit-user-form"),
		close: document.querySelector("#close-edit-user"),
		inputContainers: {
			username: document.querySelector("#edit-user-form .checked-input-container:has(input[type='text'])")
		},
		inputs: {
			username: document.querySelector("#edit-user-username-input"),
			password: document.querySelector("#edit-user-password-input")
		},
		errors: {
			usernameInvalid: document.querySelector('#edit-invalid-username-error'),
			usernameTaken: document.querySelector('#edit-taken-username-error')
		}
	},
	deleteUser: {
		dialog: document.querySelector("#delete-user-dialog"),
		username: document.querySelector("#username-delete-user"),
		close: document.querySelector("#close-delete-user"),
		confirm: document.querySelector("#confirm-delete-user")
	},
	uploadDb: {
		dialog: document.querySelector("#upload-db-dialog"),
		form: document.querySelector("#upload-db-form"),
		close: document.querySelector("#close-upload-db"),
		submit: document.querySelector("#upload-db-dialog button[type='submit']"),
		inputContainers: {
			file: document.querySelector("#upload-db-form .checked-input-container:has(input[type='file'])")
		},
		inputs: {
			file: document.querySelector("#upload-db-form input[type='file']"),
			keepHostingSettings: document.querySelector("#upload-db-form input[type='checkbox']")
		},
		errors: {
			invalidFile: document.querySelector('#upload-invalid-db-error'),
		}
	},
	importDb: {
		dialog: document.querySelector("#import-db-dialog"),
		form: document.querySelector("#import-db-form"),
		close: document.querySelector("#close-import-db"),
		submit: document.querySelector("#import-db-dialog button[type='submit']"),
		backupName: document.querySelector("#db-backup-name"),
		backupCreation: document.querySelector("#db-creation-date"),
		inputs: {
			keepHostingSettings: document.querySelector("#import-db-form input[type='checkbox']")
		}
	}
}

const els = {
	logout: document.querySelector("#logout-button"),
	settingsSubmit: document.querySelector('#save-button'),
	changesCount: document.querySelector('#changes-count'),
	settingsForm: document.querySelector('#settings-form'),
	downloadLogs: document.querySelector("#download-logs-button"),
	startResetSettings: document.querySelector("#open-reset-button"),
	userList: document.querySelector("#user-list"),
	dbBackupFolderContainer: document.querySelector('div.checked-input-container:has(#db-backup-folder-input)'),
	backupList: document.querySelector("#backup-list"),
	startAddUser: document.querySelector("#add-user-button"),
	uploadDb: document.querySelector("#upload-db-button"),
	downloadDb: document.querySelector("#download-db-button"),
	about: {
		mindVersion: document.querySelector("#mind-version"),
		pythonVersion: document.querySelector("#python-version"),
		dbVersion: document.querySelector("#db-version"),
		dbLocation: document.querySelector("#db-location"),
		dataFolder: document.querySelector("#data-folder")
	},
	power: {
		restart: document.querySelector('#restart-button'),
		shutdown: document.querySelector('#shutdown-button')
	}
}

const settings = {
	allowNewAccounts: document.querySelector('#allow-new-accounts-input'),
	loginTime: document.querySelector('#login-time-input'),
	loginTimeReset: document.querySelector('#login-time-reset-input'),
	host: document.querySelector('#host-input'),
	port: document.querySelector('#port-input'),
	urlPrefix: document.querySelector('#url-prefix-input'),
	logLevel: document.querySelector('#log-level-input'),
	dbBackupInterval: document.querySelector('#db-backup-interval-input'),
	dbBackupAmount: document.querySelector('#db-backup-amount-input'),
	dbBackupFolder: document.querySelector('#db-backup-folder-input')
}

//
// region About
//
function loadAbout() {
	fetchAPI('/about')
	.then(json => {
		els.about.mindVersion.innerText = json.result.version
		els.about.pythonVersion.innerText = json.result.python_version
		els.about.dbVersion.innerText = json.result.database_version
		els.about.dbLocation.innerText = json.result.database_location
		els.about.dataFolder.innerText = json.result.data_folder
	})
}

//
// region Power
//
function restartApp() {
	els.power.restart.innerHTML = icons.loading
	els.power.restart.classList.add('spinning')
	sendAPI("POST", "/admin/restart")
	.then(response => 
		setTimeout(
			() => window.location.reload(),
			1000
		)
	)
}

function shutdownApp() {
	els.power.shutdown.innerHTML = icons.loading
	els.power.shutdown.classList.add('spinning')
	sendAPI("POST", "/admin/shutdown")
	.then(response => 
		setTimeout(
			() => window.location.reload(),
			1000
		)
	)
}

//
// region Settings
//
function increaseChangeCount() {
	const newCount = parseInt(els.changesCount.dataset.count) + 1
	els.changesCount.dataset.count = newCount
	if (newCount === 1)
		els.changesCount.innerText = `${newCount} change`
	else
		els.changesCount.innerText = `${newCount} changes`
}

function decreaseChangeCount() {
	const newCount = parseInt(els.changesCount.dataset.count) - 1
	els.changesCount.dataset.count = newCount
	if (newCount === 1)
		els.changesCount.innerText = `${newCount} change`
	else
		els.changesCount.innerText = `${newCount} changes`
}

function clearChangeCount() {
	els.changesCount.dataset.count = 0
	els.changesCount.innerText = '0 changes'
}

function changesPresent() {
	return parseInt(els.changesCount.dataset.count) !== 0
}

function initInputChangeDetection() {
	clearChangeCount()
	Object.values(settings).forEach(s => {
		const settingValue = s.type === 'checkbox' ? s.checked : s.value
		s.dataset.currentvalue = encodeURI(settingValue)

		s.classList.remove('changed')

		s.oninput = e => {
			const newValue = encodeURI(s.type === 'checkbox' ? s.checked : s.value)
			if (
				newValue !== s.dataset.currentvalue
				&& !s.classList.contains('changed')
			) {
				// Setting has changed from current value to new value
				increaseChangeCount()
				s.classList.add('changed')
			}
			else if (
				newValue === s.dataset.currentvalue
				&& s.classList.contains('changed')
			) {
				// Setting has changed from new value back to current value
				decreaseChangeCount()
				s.classList.remove('changed')
			}
		}
	})
}

function loadSettings() {
	fetchAPI('/settings')
	.then(json => {
		settings.allowNewAccounts.checked = json.result.allow_new_accounts
		settings.loginTime.value = Math.round(json.result.login_time / 60)
		settings.loginTimeReset.value = json.result.login_time_reset.toString()
		settings.host.value = json.result.host
		settings.port.value = json.result.port
		settings.urlPrefix.value = json.result.url_prefix
		settings.logLevel.value = json.result.log_level
		settings.dbBackupInterval.value = json.result.db_backup_interval / 3600
		settings.dbBackupAmount.value = json.result.db_backup_amount
		settings.dbBackupFolder.value = json.result.db_backup_folder

		initInputChangeDetection()
	})
}

function submitSettings() {
	els.dbBackupFolderContainer.classList.remove('error-input-container')
	els.settingsSubmit.classList.remove('submit-error')

	if (!changesPresent())
		return

	let hostChanged = false,
		portChanged = false,
		urlPrefixChanged = false
	const data = {}

	if (settings.allowNewAccounts.classList.contains('changed'))
		data.allow_new_accounts = settings.allowNewAccounts.checked

	if (settings.loginTime.classList.contains('changed'))
		data.login_time = settings.loginTime.value * 60

	if (settings.loginTimeReset.classList.contains('changed'))
		data.login_time_reset = settings.loginTimeReset.value === 'true'

	if (settings.host.classList.contains('changed')) {
		data.host = settings.host.value
		hostChanged = true
	}

	if (settings.port.classList.contains('changed')) {
		data.port = parseInt(settings.port.value)
		portChanged = true
	}

	if (settings.urlPrefix.classList.contains('changed')) {
		data.url_prefix = settings.urlPrefix.value
		urlPrefixChanged = true
	}

	if (settings.logLevel.classList.contains('changed'))
		data.log_level = parseInt(settings.logLevel.value)

	if (settings.dbBackupInterval.classList.contains('changed'))
		data.db_backup_interval = parseInt(settings.dbBackupInterval.value) * 3600

	if (settings.dbBackupAmount.classList.contains('changed'))
		data.db_backup_amount = parseInt(settings.dbBackupAmount.value)

	if (settings.dbBackupFolder.classList.contains('changed'))
		data.db_backup_folder = settings.dbBackupFolder.value

	if (hostChanged || portChanged || urlPrefixChanged) {
		// Notify about restart and revert timer
		const restartMessage = "MIND has detected changes to the hosting settings. "
			+ "It is required to login into MIND within 1 minute in order to keep the new hosting settings. "
			+ "Otherwise, MIND will go back to the old hosting settings."
		if (!confirm(restartMessage))
			return
	}

	sendAPI("PUT", "/admin/settings", {}, data)
	.then(response => {
		if (hostChanged) {
			setTimeout(
				() => window.location.reload(),
				1000
			)
		}
		else if (portChanged || urlPrefixChanged) {
			const newUrl = new URL(window.location.href)
			if (portChanged)
				newUrl.port = parseInt(settings.port.value)
			if (urlPrefixChanged)
				newUrl.pathname = settings.urlPrefix.value + newUrl.pathname.slice(settings.urlPrefix.dataset.currentvalue.length)

			setTimeout(
				() => window.location.href = newUrl.toString(),
				1000
			)
		}
		
		initInputChangeDetection()
	})
	.catch(response => {
		response.json().then(json => {
			if (['ApiKeyInvalid', 'ApiKeyExpired'].includes(json.error))
				window.location.href = `${urlPrefix}/`

			if (
				json.error === 'InvalidKeyValue'
				&& json.result.key === 'db_backup_folder'
			) {
				els.dbBackupFolderContainer.classList.add('error-input-container')
				els.settingsSubmit.classList.add('submit-error')
			}
		})
	})
}

function openResetSettings() {
	windows.resetSettings.dialog.showModal()
}

function closeResetSettings() {
	windows.resetSettings.dialog.close()
}

function resetSettings() {
	const resetSettings = [...windows.resetSettings.form.querySelectorAll('input')]
		.filter(i => i.checked)
		.map(i => i.dataset.setting)

	windows.resetSettings.submit.innerHTML = icons.loading
	windows.resetSettings.submit.classList.add('spinning')

	const hostChanged = resetSettings.includes("host"),
		portChanged = resetSettings.includes("port"),
		urlPrefixChanged = resetSettings.includes("url_prefix")

	if (hostChanged || portChanged || urlPrefixChanged) {
		// Notify about restart and revert timer
		const restartMessage = "MIND has detected changes to the hosting settings. "
			+ "It is required to login into MIND within 1 minute in order to keep the new hosting settings. "
			+ "Otherwise, MIND will go back to the old hosting settings."
		if (!confirm(restartMessage)) {
			windows.resetSettings.submit.innerText = "Reset"
			windows.resetSettings.submit.classList.remove('spinning')
			return
		}
	}

	sendAPI("DELETE", "/admin/settings", {}, {
		setting_keys: resetSettings
	})
	.then(response => {
		if (portChanged || urlPrefixChanged) {
			const newUrl = new URL(window.location.href)
			if (portChanged)
				newUrl.port = 8080
			if (urlPrefixChanged)
				newUrl.pathname = "/"
	
			setTimeout(
				() => window.location.href = newUrl.toString(),
				1000
			)
	
		} else {
			setTimeout(
				() => window.location.reload(),
				1000
			)
		}
	})
}

//
// region Add user
//
function openAddUser() {
	windows.addUser.inputContainers.username.classList.remove('error-input-container')
	hide([windows.addUser.errors.usernameInvalid, windows.addUser.errors.usernameTaken])
	windows.addUser.inputs.username.value = ''
	windows.addUser.inputs.password.value = ''

	windows.addUser.dialog.showModal()
}

function closeAddUser() {
	windows.addUser.dialog.close()
}

function addUser() {
	windows.addUser.inputContainers.username.classList.remove('error-input-container')
	hide([windows.addUser.errors.usernameInvalid, windows.addUser.errors.usernameTaken])

	const data = {
		username: windows.addUser.inputs.username.value,
		password: windows.addUser.inputs.password.value
	}

	sendAPI("POST", "/admin/users", {}, data)
	.then(json => {
		loadUsers()
		closeAddUser()
	})
	.catch(e => {
		e.json().then(e => {
			if (e.error === 'UsernameInvalid') {
				windows.addUser.errors.usernameInvalid.innerText = e.result.reason
				hide([], [windows.addUser.errors.usernameInvalid])
				windows.addUser.inputContainers.username.classList.add('error-input-container')

			} else if (e.error === 'UsernameTaken') {
				hide([], [windows.addUser.errors.usernameTaken])
				windows.addUser.inputContainers.username.classList.add('error-input-container')

			} else {
				console.log(e)
			}
		})
	})
}

//
// region Edit user
//
function openEditUser(id, username, isAdmin) {
	windows.editUser.dialog.dataset.id = id
	windows.editUser.username.innerText = username

	windows.editUser.inputContainers.username.classList.remove('error-input-container')
	hide([windows.editUser.errors.usernameInvalid, windows.editUser.errors.usernameTaken])
	windows.editUser.inputs.username.value = ''
	windows.editUser.inputs.password.value = ''

	if (isAdmin)
		hide([windows.editUser.inputContainers.username])
	else
		hide([], [windows.editUser.inputContainers.username])

	windows.editUser.dialog.showModal()
}

function closeEditUser() {
	windows.editUser.dialog.close()
}

function editUser() {
	windows.editUser.inputContainers.username.classList.remove('error-input-container')
	hide([windows.editUser.errors.usernameInvalid, windows.editUser.errors.usernameTaken])

	const data = {}

	if (windows.editUser.inputs.username.value !== '')
		data.new_username = windows.editUser.inputs.username.value

	if (windows.editUser.inputs.password.value !== '')
		data.new_password = windows.editUser.inputs.password.value

	if (Object.keys(data).length === 0) {
		// Nothing changed
		closeEditUser()
		return
	}

	const id = parseInt(windows.editUser.dialog.dataset.id)
	sendAPI("PUT", `/admin/users/${id}`, {}, data)
	.then(json => {
		loadUsers()
		closeEditUser()
	})
	.catch(e => {
		e.json().then(e => {
			if (e.error === 'UsernameInvalid') {
				windows.editUser.errors.usernameInvalid.innerText = e.result.reason
				hide([], [windows.editUser.errors.usernameInvalid])
				windows.editUser.inputContainers.username.classList.add('error-input-container')

			} else if (e.error === 'UsernameTaken') {
				hide([], [windows.editUser.errors.usernameTaken])
				windows.editUser.inputContainers.username.classList.add('error-input-container')

			} else {
				console.log(e)
			}
		})
	})
}

//
// region Delete user
//
function openDeleteUser(id, username) {
	windows.deleteUser.dialog.dataset.id = id
	windows.deleteUser.username.innerText = username
	windows.deleteUser.dialog.showModal()
}

function closeDeleteUser() {
	windows.deleteUser.dialog.close()
}

function deleteUser() {
	const id = parseInt(windows.deleteUser.dialog.dataset.id)
	sendAPI("DELETE", `/admin/users/${id}`)
	.then(response => {
		els.userList.querySelector(`tr[data-id="${id}"]`).remove()
		closeDeleteUser()
	})
}

//
// region Load users
//
function loadUsers() {
	els.userList.innerHTML = ''
	fetchAPI("/admin/users")
	.then(json => {
		json.result.forEach(user => {
			const entry = document.createElement('tr')
			entry.dataset.id = user.id

			const username = document.createElement('td')
			username.innerText = user.username
			entry.appendChild(username)

			const actions = document.createElement('td')
			entry.appendChild(actions)

			const edit_user = document.createElement('button')
			edit_user.onclick = e => openEditUser(user.id, user.username, user.admin)
			edit_user.innerHTML = icons.edit
			actions.appendChild(edit_user)

			if (user.username !== 'admin') {
				const delete_user = document.createElement('button')
				delete_user.onclick = e => openDeleteUser(user.id, user.username)
				delete_user.innerHTML = icons.delete
				actions.appendChild(delete_user)
			}

			els.userList.appendChild(entry)
		})
	})
}

//
// region Database management
//
function openUploadDb() {
	windows.uploadDb.inputs.file.value = ''
	windows.uploadDb.inputContainers.file.classList.remove('error-input-container')
	windows.uploadDb.inputs.keepHostingSettings.checked = false
	windows.uploadDb.dialog.showModal()
}

function closeUploadDb() {
	windows.uploadDb.dialog.close()
}

function uploadDb() {
	const copyHosting = windows.uploadDb.inputs.keepHostingSettings ? 'true' : 'false'
	const formData = new FormData()
	formData.append('file', windows.uploadDb.inputs.file.files[0])

	windows.uploadDb.submit.innerHTML = icons.loading
	windows.uploadDb.submit.classList.add('spinning')
	windows.uploadDb.inputContainers.file.classList.remove('error-input-container')
	fetch(`${urlPrefix}/api/admin/database?api_key=${apiKey}&copy_hosting_settings=${copyHosting}`, {
		method: 'POST',
		body: formData
	})
	.then(response => {
		if (!response.ok) return Promise.reject(response.status)
		setTimeout(
			() => window.location.reload(),
			1000
		)
	})
	.catch(e => {
		if (e === 400) {
			windows.uploadDb.inputs.file.value = ''
			windows.uploadDb.submit.innerText = 'Import'
			windows.uploadDb.submit.classList.remove('spinning')
			windows.uploadDb.inputContainers.file.classList.add('error-input-container')

		} else
			console.log(e)
	})
}

function openImportDb(index, filename, creation) {
	windows.importDb.dialog.dataset.index = index
	windows.importDb.backupName.innerText = filename
	windows.importDb.backupCreation.innerText = new
		Date(creation * 1000)
			.toLocaleString(getLocalStorage('locale')['locale'])
	windows.importDb.inputs.keepHostingSettings.checked = false
	windows.importDb.dialog.showModal()
}

function closeImportDb() {
	windows.importDb.dialog.close()
}

function importDb() {
	const index = parseInt(windows.importDb.dialog.dataset.index)
	const copyHosting = windows.importDb.inputs.keepHostingSettings ? 'true' : 'false'
	windows.importDb.submit.innerHTML = icons.loading
	windows.importDb.submit.classList.add('spinning')
	sendAPI("POST", `/admin/database/backups/${index}`, {
		copy_hosting_settings: copyHosting
	})
	.then(response => {
		setTimeout(
			() => window.location.reload(),
			1000
		)
	})
}

function loadBackups() {
	els.backupList.innerHTML = ''
	fetchAPI("/admin/database/backups")
	.then(json => {
		json.result.forEach(backup => {
			const entry = document.createElement('tr')
			entry.dataset.index = backup.index

			const filename = document.createElement('td')
			filename.innerText = backup.filename
			entry.appendChild(filename)

			const creation = document.createElement('td')
			let formatted_datetime = new
				Date(backup.creation_date * 1000)
				.toLocaleString(getLocalStorage('locale')['locale'])
			creation.innerText = formatted_datetime
			entry.appendChild(creation)

			const actions = document.createElement('td')
			entry.appendChild(actions)

			const download = document.createElement('button')
			download.onclick =
				e => window.location.href =
					`${urlPrefix}/api/admin/database/backups/${backup.index}?api_key=${apiKey}`
			download.innerHTML = icons.download
			download.title = "Download database backup"
			actions.appendChild(download)

			const importDb = document.createElement('button')
			importDb.onclick = e => openImportDb(backup.index, backup.filename, backup.creation_date)
			importDb.innerHTML = icons.upload
			importDb.title = "Import database backup"
			actions.appendChild(importDb)

			els.backupList.appendChild(entry)
		})
	})
}

//
// region On load
//
checkLogin()

loadAbout()
loadSettings()
loadUsers()
loadBackups()

els.logout.onclick = e => {
	if (changesPresent())
		if (!confirm("You have unsaved changes. Are you sure you want to leave?"))
			return
		window.onbeforeunload = null

	logout()
}
els.settingsForm.action = 'javascript:submitSettings();'

window.onbeforeunload = e => {
	if (!changesPresent())
		// No changes
		return undefined

	// Changes detected. Returning string instead of undefined
	// will make browser show confirmation message before leaving.
	// Showing custom message is not allowed, so an empty string is
	// good enough
	e.returnValue = ''
	return ''
}

els.power.restart.onclick = e => restartApp()
els.power.shutdown.onclick = e => shutdownApp()

els.downloadLogs.onclick = e =>
	window.location.href = `${urlPrefix}/api/admin/logs?api_key=${apiKey}`

els.startResetSettings.onclick = e => openResetSettings()
windows.resetSettings.dialog.onclick = e => {
	if (e.target === e.currentTarget) {
		e.stopPropagation()
		closeResetSettings()
	}
}
windows.resetSettings.form.action = 'javascript:resetSettings()'
windows.resetSettings.close.onclick = e => closeResetSettings()

els.startAddUser.onclick = e => openAddUser()
windows.addUser.dialog.onclick = e => {
	if (e.target === e.currentTarget) {
		e.stopPropagation()
		closeAddUser()
	}
}
windows.addUser.form.action = 'javascript:addUser()'
windows.addUser.close.onclick = e => closeAddUser()

windows.editUser.dialog.onclick = e => {
	if (e.target === e.currentTarget) {
		e.stopPropagation()
		closeEditUser()
	}
}
windows.editUser.form.action = 'javascript:editUser()'
windows.editUser.close.onclick = e => closeEditUser()

windows.deleteUser.dialog.onclick = e => {
	if (e.target === e.currentTarget) {
		e.stopPropagation()
		closeDeleteUser()
	}
}
windows.deleteUser.close.onclick = e => closeDeleteUser()
windows.deleteUser.confirm.onclick = e => deleteUser()

els.uploadDb.onclick = e => openUploadDb()
windows.uploadDb.dialog.onclick = e => {
	if (e.target === e.currentTarget) {
		e.stopPropagation()
		closeUploadDb()
	}
}
windows.uploadDb.form.action = 'javascript:uploadDb()'
windows.uploadDb.close.onclick = e => closeUploadDb()

els.downloadDb.onclick = e =>
	window.location.href = `${urlPrefix}/api/admin/database?api_key=${apiKey}`

windows.importDb.dialog.onclick = e => {
	if (e.target === e.currentTarget) {
		e.stopPropagation()
		closeImportDb()
	}
}
windows.importDb.form.action = 'javascript:importDb()'
windows.importDb.close.onclick = e => closeImportDb()
