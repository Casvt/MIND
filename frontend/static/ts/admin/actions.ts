import { Constants, createIcon, downloadBackupDatabase, fetchAPI, getLocalStorage, hide, invalidUsernameReasonMap, Window } from "../general";
import { adminEls } from "./elements";

// region About
export function loadAbout(): void {
    fetchAPI("/about")
    .then(json => {
        adminEls.about.mindVersion.innerText = json.result.version
		adminEls.about.pythonVersion.innerText = json.result.python_version
		adminEls.about.dbVersion.innerText = json.result.database_version
		adminEls.about.dbLocation.innerText = json.result.database_location
		adminEls.about.dataFolder.innerText = json.result.data_folder
    })
}

// region Power
export function restart(): void {
    adminEls.power.restart.replaceChildren(createIcon("icon-loading"))
    adminEls.power.restart.classList.add("spinning")

    fetchAPI("/admin/restart", {method: "POST"})
    .then(json => {
        setTimeout(
            () => window.location.reload(),
            1000
        )
    })
}

export function shutdown(): void {
    adminEls.power.shutdown.replaceChildren(createIcon("icon-loading"))
    adminEls.power.shutdown.classList.add("spinning")

    fetchAPI("/admin/shutdown", {method: "POST"})
    .then(json => {
        setTimeout(
            () => window.location.reload(),
            1000
        )
    })
}

// region Setting Changes
export class SettingsChanges {
    public static changesCount: number = 0

    public static setChangeCount(count: number): void {
        this.changesCount = count
        if (count === 1)
            adminEls.changesCount.innerText = `${count} change`
        else
            adminEls.changesCount.innerText = `${count} changes`
    }

    public static initInputChangeDetection(): void {
        this.setChangeCount(0)

        Object.values(adminEls.settings).forEach(s => {
            const settingValue = s.type === "checkbox" ? s.checked : s.value
            s.dataset.currentValue = encodeURI(settingValue.toString())
            s.classList.remove("changed")

            s.oninput = e => {
                const newValue = encodeURI((
                    s.type === "checkbox" ? s.checked : s.value
                ).toString())

                if (
                    newValue !== s.dataset.currentValue
                    && !s.classList.contains("changed")
                ) {
                    // Setting has changed from current value to new value
                    this.setChangeCount(this.changesCount + 1)
                    s.classList.add("changed")
                }
                else if (
                    newValue === s.dataset.currentValue
                    && s.classList.contains("changed")
                ) {
                    // Setting has changed from new value back to current value
                    this.setChangeCount(this.changesCount - 1)
                    s.classList.remove("changed")
                }
            }
        })
    }
}

// region Setting Handling
export function loadSettings(): void {
    fetchAPI("/settings")
    .then(json => {
        let el = adminEls.settings.allowNewAccounts
		el.checked = json.result[el.name]

        el = adminEls.settings.loginTime
		el.value = Math.round(json.result[el.name] / 60).toString()

        el = adminEls.settings.loginTimeReset
        el.value = json.result[el.name].toString()

        el = adminEls.settings.host
        el.value = json.result[el.name]

        el = adminEls.settings.port
        el.value = json.result[el.name]

        el = adminEls.settings.urlPrefix
        el.value = json.result[el.name]

        el = adminEls.settings.logLevel
        el.value = json.result[el.name]

        el = adminEls.settings.dbBackupInterval
        el.value = (json.result[el.name] / 3600).toString()

        el = adminEls.settings.dbBackupAmount
        el.value = json.result[el.name]

        el = adminEls.settings.dbBackupFolder
        el.value = json.result[el.name]

        loadPlugins(json.result["apprise_plugin_paths"])

		SettingsChanges.initInputChangeDetection()
    })
}

export function submitSettings(): void {
    adminEls.dbBackupFolderInputContainer.classList.remove("error-input-container")
	adminEls.settingsSubmit.classList.remove("submit-error")

	if (SettingsChanges.changesCount === 0)
		return

    const data: Record<string, any> = {}
	let hostChanged = false,
		portChanged = false,
		urlPrefixChanged = false

    if (adminEls.settings.allowNewAccounts.classList.contains("changed")) {
        const el = adminEls.settings.allowNewAccounts
		data[el.name] = el.checked
    }

	if (adminEls.settings.loginTime.classList.contains("changed")) {
        const el = adminEls.settings.loginTime
		data[el.name] = parseInt(el.value) * 60
    }

	if (adminEls.settings.loginTimeReset.classList.contains("changed")) {
        const el = adminEls.settings.loginTimeReset
		data[el.name] = el.value === "true"
    }

	if (adminEls.settings.host.classList.contains("changed")) {
        const el = adminEls.settings.host
		data[el.name] = el.value
		hostChanged = true
	}

	if (adminEls.settings.port.classList.contains("changed")) {
        const el = adminEls.settings.port
		data[el.name] = parseInt(el.value)
		portChanged = true
	}

	if (adminEls.settings.urlPrefix.classList.contains("changed")) {
        const el = adminEls.settings.urlPrefix
		data[el.name] = el.value
		urlPrefixChanged = true
	}

	if (adminEls.settings.logLevel.classList.contains("changed")) {
        const el = adminEls.settings.logLevel
		data[el.name] = parseInt(el.value)
    }

	if (adminEls.settings.dbBackupInterval.classList.contains("changed")) {
        const el = adminEls.settings.dbBackupInterval
		data[el.name] = parseInt(el.value) * 3600
    }

	if (adminEls.settings.dbBackupAmount.classList.contains("changed")) {
        const el = adminEls.settings.dbBackupAmount
		data[el.name] = parseInt(el.value)
    }

	if (adminEls.settings.dbBackupFolder.classList.contains("changed")) {
        const el = adminEls.settings.dbBackupFolder
		data[el.name] = el.value
    }

	if (hostChanged || portChanged || urlPrefixChanged) {
		// Notify about restart and revert timer
		if (!confirm(Constants.restartMessage))
			return
	}

    fetchAPI("/admin/settings", {method: "PUT", body: data})
	.then(_ => {
		if (hostChanged) {
			setTimeout(
				() => window.location.reload(),
				1000
			)
		}
		else if (portChanged || urlPrefixChanged) {
			const newUrl = new URL(window.location.href)
			if (portChanged)
				newUrl.port = adminEls.settings.port.value
			if (urlPrefixChanged)
				newUrl.pathname = (
                    adminEls.settings.urlPrefix.value
                    + newUrl.pathname.slice(
                        adminEls.settings.urlPrefix.dataset.currentValue?.length || 0
                    )
                )

			setTimeout(
				() => window.location.href = newUrl.toString(),
				1000
			)
		}

		SettingsChanges.initInputChangeDetection()
	})
	.catch(json => {
        if (
            json.error === "InvalidKeyValue"
            && json.result.key === adminEls.settings.dbBackupFolder.name
        ) {
            adminEls.dbBackupFolderInputContainer.classList.add("error-input-container")
            adminEls.settingsSubmit.classList.add("submit-error")
        }
	})
}

// region Setting Resetting
class ResetWindow implements Window {
    public dialog = adminEls.resetSettings.dialog

    public prepare(): void {
        Object.values(adminEls.settings).forEach(el => {
            let parent = el.parentElement as HTMLElement
            if (parent.nodeName === "DIV")
                parent = parent.parentElement as HTMLElement
            parent = parent.parentElement as HTMLElement
            //@ts-expect-error
            const title = parent.firstElementChild.firstElementChild.innerText
            const tr = document.createElement("tr")
            const checkboxContainer = document.createElement("td")
            const checkbox = document.createElement("input")
            checkbox.type = "checkbox"
            checkbox.dataset.setting = el.name
            checkboxContainer.appendChild(checkbox)
            const titleContainer = document.createElement("td")
            titleContainer.innerText = title
            tr.appendChild(checkboxContainer)
            tr.appendChild(titleContainer)
            adminEls.resetSettings.list.appendChild(tr)
        })
    }

    public show(args: object = {}): void {
        adminEls.resetSettings.list.querySelectorAll("input").forEach(
            el => el.checked = false
        )
        this.dialog.showModal()
    }

    public hide(): void {
        this.dialog.close()
    }

    public submit(): void {
        const resetSettings = [...adminEls.resetSettings.list.querySelectorAll('input')]
            .filter(i => i.checked)
            .map(i => i.dataset.setting)

        if (!resetSettings.length)
            return

        adminEls.resetSettings.submit.replaceChildren(createIcon("icon-loading"))
        adminEls.resetSettings.submit.classList.add("spinning")

        const hostChanged = resetSettings.includes(
                adminEls.settings.host.name
            ),
            portChanged = resetSettings.includes(
                adminEls.settings.port.name
            ),
            urlPrefixChanged = resetSettings.includes(
                adminEls.settings.urlPrefix.name
            )

        if (hostChanged || portChanged || urlPrefixChanged) {
            // Notify about restart and revert timer
            if (!confirm(Constants.restartMessage)) {
                adminEls.resetSettings.submit.innerText = "Reset"
                adminEls.resetSettings.submit.classList.remove("spinning")
                return
            }
        }

        fetchAPI("/admin/settings", {
            method: "DELETE",
            body: {setting_keys: resetSettings}
        })
        .then(_ => {
            if (portChanged || urlPrefixChanged) {
                const newUrl = new URL(window.location.href)
                if (portChanged)
                    newUrl.port = (8080).toString()
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
}

// region Plugin Management
const plugins: string[] = []

function loadPlugins(plugins: string[]): void {
    adminEls.plugins.list.innerHTML = ''
    plugins.forEach(plugin => {
        const tr = document.createElement("tr")

        const path = document.createElement("td")
        path.innerText = plugin
        tr.appendChild(path)

        const action = document.createElement("td")
        const deletePlugin = document.createElement("button")
        deletePlugin.appendChild(createIcon("icon-delete"))
        deletePlugin.title = "Remove the plugin path"
        deletePlugin.onclick = e => {
            plugins.shift()
            loadPlugins(plugins)
            fetchAPI("/admin/settings", {method: "PUT", body: {
                apprise_plugin_paths: plugins
            }})
        }
        action.appendChild(deletePlugin)
        tr.appendChild(action)

        adminEls.plugins.list.appendChild(tr)
    })
}

class PluginsWindow implements Window {
    public dialog = adminEls.plugins.dialog

    public prepare(): void {}

    public show(args: object = {}): void {
        hide({to_hide: [adminEls.plugins.addRow, adminEls.plugins.error]})
        this.dialog.showModal()
    }

    public hide(): void {
        this.dialog.close()
    }

    public submit(): void {
        hide({to_hide: [adminEls.plugins.error]})

        plugins.unshift(adminEls.plugins.addInput.value)

        fetchAPI("/admin/settings", {method: "PUT", body: {
            apprise_plugin_paths: plugins
        }})
        .then(_ => {
            loadPlugins(plugins)
            hide({to_hide: [adminEls.plugins.addRow]})
        })
        .catch(json => {
            if (json.error === "InvalidKeyValue") {
                plugins.shift()
                hide({to_show: [adminEls.plugins.error]})
            }
            else
                console.log(json)
        })
    }
}

// region User Management
export const users: Record<number, {username: string, admin: boolean}> = {}

export function loadUsers(): void {
    adminEls.userList.innerHTML = ''
    fetchAPI("/admin/users")
    .then(json => {
        json.result.forEach((
            user: {id: number, username: string, admin: boolean}
        ) => {
            users[user.id] = {username: user.username, admin: user.admin}

            const entry = document.createElement("tr")
            entry.dataset.id = user.id.toString()

            const username = document.createElement("td")
            username.innerText = user.username
            entry.appendChild(username)

            const actions = document.createElement("td")
            entry.appendChild(actions)

            const editUser = document.createElement("button")
            editUser.appendChild(createIcon("icon-edit"))
            editUser.title = "Edit the user"
            editUser.onclick = e => windowInstances.editUser.show({
                userId: user.id
            })
            actions.appendChild(editUser)

            const deleteUser = document.createElement("button")
            deleteUser.appendChild(createIcon("icon-delete"))
            deleteUser.title = "Delete the user"
            deleteUser.onclick = e => windowInstances.deleteUser.show({
                userId: user.id
            })
            actions.appendChild(deleteUser)

            if (user.username === "admin") {
                deleteUser.classList.add("hidden")
            }

            adminEls.userList.appendChild(entry)
        })
    })
}

class AddUserWindow implements Window {
    public dialog = adminEls.addUser.dialog

    public prepare(): void {}

    public show(args: object = {}): void {
        adminEls.addUser.inputContainers.username.classList.remove("error-input-container")
        hide({to_hide: [
            adminEls.addUser.errors.usernameInvalid, adminEls.addUser.errors.usernameTaken
        ]})
        adminEls.addUser.inputs.username.value = ''
        adminEls.addUser.inputs.password.value = ''

        this.dialog.showModal()
    }

    public hide(): void {
        this.dialog.close()
    }

    public submit(): void {
        adminEls.addUser.inputContainers.username.classList.remove("error-input-container")
        hide({to_hide: [
            adminEls.addUser.errors.usernameInvalid, adminEls.addUser.errors.usernameTaken
        ]})

        const data = {
            username: adminEls.addUser.inputs.username.value,
            password: adminEls.addUser.inputs.password.value
        }

        fetchAPI("/admin/users", {
            method: "POST",
            body: data
        })
        .then(_ => {
            loadUsers()
            this.hide()
        })
        .catch(json => {
            if (json.error === "UsernameInvalid") {
                adminEls.addUser.errors.usernameInvalid.innerText = invalidUsernameReasonMap[json.result.reason]
                hide({to_show: [adminEls.addUser.errors.usernameInvalid]})
                adminEls.addUser.inputContainers.username.classList.add("error-input-container")

            } else if (json.error === "UsernameTaken") {
                hide({to_show: [adminEls.addUser.errors.usernameTaken]})
                adminEls.addUser.inputContainers.username.classList.add("error-input-container")

            } else {
                console.log(json)
            }
        })
    }
}

class EditUserWindow implements Window {
    private state = {
        userId: null as number | null
    }

    public dialog = adminEls.editUser.dialog

    public prepare(): void {}

    public show(args: {userId: number}): void {
        this.state.userId = args.userId
        const {username, admin} = users[args.userId]

        adminEls.editUser.username.innerText = username

        adminEls.editUser.inputContainers.username.classList.remove("error-input-container")
        hide({to_hide: [
            adminEls.editUser.errors.usernameInvalid,
            adminEls.editUser.errors.usernameTaken
        ]})
        adminEls.editUser.inputs.username.value = ''
        adminEls.editUser.inputs.password.value = ''

        if (admin)
            hide({to_hide: [adminEls.editUser.inputContainers.username]})
        else
            hide({to_show: [adminEls.editUser.inputContainers.username]})

        this.dialog.showModal()
    }

    public hide(): void {
        this.dialog.close()
    }

    public submit(): void {
        adminEls.editUser.inputContainers.username.classList.remove("error-input-container")
        hide({to_hide: [
            adminEls.editUser.errors.usernameInvalid,
            adminEls.editUser.errors.usernameTaken
        ]})

        const data: Partial<{new_username: string, new_password: string}> = {},
            usernameValue = adminEls.editUser.inputs.username.value,
            passwordValue = adminEls.editUser.inputs.password.value

        if (usernameValue)
            data.new_username = usernameValue
        if (passwordValue)
            data.new_password = passwordValue

        if (!Object.keys(data).length) {
            // Nothing changed
            this.hide()
            return
        }

        const userId = this.state.userId
        if (!userId)
            throw new Error("Trying to submit editing a user without having the dialog open")

        fetchAPI(`/admin/users/${userId}`, {
            method: "PUT",
            body: data
        })
        .then(_ => {
            loadUsers()
            this.hide()
        })
        .catch(json => {
            if (json.error === "UsernameInvalid") {
                adminEls.editUser.errors.usernameInvalid.innerText = invalidUsernameReasonMap[json.result.reason]
                hide({to_show: [adminEls.editUser.errors.usernameInvalid]})
                adminEls.editUser.inputContainers.username.classList.add("error-input-container")

            } else if (json.error === "UsernameTaken") {
                hide({to_show: [adminEls.editUser.errors.usernameTaken]})
                adminEls.editUser.inputContainers.username.classList.add("error-input-container")

            } else {
                console.log(json)
            }
        })
    }
}

class DeleteUserWindow implements Window {
    private state = {
        userId: null as number | null
    }

    public dialog = adminEls.deleteUser.dialog

    public prepare(): void {}

    public show(args: {userId: number}): void {
        this.state.userId = args.userId
        const username = users[args.userId].username

        adminEls.deleteUser.username.innerText = username
        adminEls.deleteUser.dialog.showModal()
    }

    public hide(): void {
        adminEls.deleteUser.dialog.close()
    }

    public submit(): void {
        const userId = this.state.userId
        if (!userId)
            throw new Error("Trying to submit deleting a user without having the dialog open")

        fetchAPI(`/admin/users/${userId}`, {method: "DELETE"})
        .then(_ => {
            adminEls.userList.querySelector(`tr[data-id="${userId}"]`)?.remove()
            this.hide()
        })
    }
}

// region Backup Management
export const backups: Record<number, {filename: string, creationDate: number}> = {}

export function loadBackups(): void {
    adminEls.backupList.innerHTML = ''
    fetchAPI("/admin/database/backups")
    .then(json => {
        json.result.forEach((
            backup: {index: number, filename: string, creation_date: number}
        ) => {
            backups[backup.index] = {
                filename: backup.filename,
                creationDate: backup.creation_date
            }

            const entry = document.createElement("tr")
            entry.dataset.index = backup.index.toString()

            const filename = document.createElement("td")
            filename.innerText = backup.filename
            entry.appendChild(filename)

            const creation = document.createElement("td")
            let formattedDate = new Date(backup.creation_date * 1000)
                .toLocaleString(getLocalStorage().locale)
            creation.innerText = formattedDate
            entry.appendChild(creation)

            const actions = document.createElement("td")
            entry.appendChild(actions)

            const downloadBackup = document.createElement("button")
            downloadBackup.appendChild(createIcon("icon-download"))
            downloadBackup.title = "Download database backup"
            downloadBackup.onclick = e => downloadBackupDatabase(backup.index)
            actions.appendChild(downloadBackup)

            const importBackup = document.createElement("button")
            importBackup.appendChild(createIcon("icon-upload"))
            importBackup.title = "Import database backup"
            importBackup.onclick = e => windowInstances.importDatabase.show({
                backupIndex: backup.index
            })
            actions.appendChild(importBackup)

            adminEls.backupList.appendChild(entry)
        })
    })
}

class UploadDatabaseWindow implements Window {
    public dialog = adminEls.uploadDb.dialog

    public prepare(): void {}

    public show(args: object = {}): void {
        adminEls.uploadDb.inputs.file.value = ''
        adminEls.uploadDb.inputContainers.file.classList.remove("error-input-container")
        adminEls.uploadDb.inputs.keepHostingSettings.checked = false
        this.dialog.showModal()
    }

    public hide(): void {
        this.dialog.close()
    }

    public submit(): void {
        const formData = new FormData()

        if (!adminEls.uploadDb.inputs.file.files)
            return
        formData.append('file', adminEls.uploadDb.inputs.file.files[0])

        adminEls.uploadDb.submit.replaceChildren(createIcon("icon-loading"))
        adminEls.uploadDb.submit.classList.add("spinning")
        adminEls.uploadDb.inputContainers.file.classList.remove("error-input-container")

        fetchAPI("/admin/database", {
            method: "POST",
            params: {
                copy_hosting_settings: adminEls.uploadDb.inputs.keepHostingSettings
            },
            body: formData
        })
        .then(_ => setTimeout(
            () => window.location.reload(),
            1000
        ))
        .catch(json => {
            if (json.error === "InvalidDatabaseFile") {
                adminEls.uploadDb.inputs.file.value = ''
                adminEls.uploadDb.submit.innerText = "Import"
                adminEls.uploadDb.submit.classList.remove("spinning")
                adminEls.uploadDb.inputContainers.file.classList.add("error-input-container")

            } else
                console.log(json)
        })
    }
}

class ImportDatabaseWindow implements Window {
    private state = {
        backupIndex: null as number | null
    }

    public dialog = adminEls.importDb.dialog

    public prepare(): void {}

    public show(args: {backupIndex: number}): void {
        this.state.backupIndex = args.backupIndex
        const {filename, creationDate} = backups[args.backupIndex]

        adminEls.importDb.backupName.innerText = filename
        adminEls.importDb.backupCreation.innerText = new Date(creationDate * 1000)
            .toLocaleString(getLocalStorage().locale)
        adminEls.importDb.inputs.keepHostingSettings.checked = false

        adminEls.importDb.dialog.showModal()
    }

    public hide(): void {
        this.dialog.close()
    }

    public submit(): void {
        const backupIndex = this.state.backupIndex
        if (!backupIndex)
            throw new Error("Trying to submit importing a db without having the dialog open")

        adminEls.importDb.submit.replaceChildren(createIcon("icon-loading"))
        adminEls.importDb.submit.classList.add("spinning")

        fetchAPI(`/admin/database/backups/${backupIndex}`, {
            method: "POST",
            params: {
                copy_hosting_settings: adminEls.importDb.inputs.keepHostingSettings.checked
            }
        })
        .then(_ => setTimeout(
            () => window.location.reload(),
            1000
        ))
    }
}

// region Window Instances
export const windowInstances = {
    reset: new ResetWindow(),
    plugins: new PluginsWindow(),
    addUser: new AddUserWindow(),
    editUser: new EditUserWindow(),
    deleteUser: new DeleteUserWindow(),
    uploadDatabase: new UploadDatabaseWindow(),
    importDatabase: new ImportDatabaseWindow()
}
