import { Constants, downloadCurrentDatabase, downloadLogs, hide, logout, OnLoadRunner } from "../general";
import { loadAbout, loadBackups, loadSettings, loadUsers, restart, SettingsChanges, shutdown, submitSettings, windowInstances } from "./actions";
import { adminEls } from "./elements";

adminEls.settingsForm.onsubmit = e => {
    e.preventDefault()
    submitSettings()
}
adminEls.logout.onclick = e => {
    if (SettingsChanges.changesCount > 0) {
        if (!confirm(Constants.unsavedChangesMessage))
            return
        window.onbeforeunload = null
    }

    logout()
}
window.onbeforeunload = e => {
    if (SettingsChanges.changesCount === 0)
        // No changes
        return undefined

	// Changes detected
    // This call triggers the built-in confirm() window
    e.preventDefault()
}

adminEls.power.restart.onclick = e => restart()
adminEls.power.shutdown.onclick = e => shutdown()

adminEls.downloadLogs.onclick = e => downloadLogs()

adminEls.resetSettings.open.onclick = e => windowInstances.reset.show()
adminEls.resetSettings.cancel.onclick = e => windowInstances.reset.hide()
adminEls.resetSettings.dialog.onclick = e => {
    if (e.target === e.currentTarget) {
        e.stopPropagation()
        windowInstances.reset.hide()
    }
}
adminEls.resetSettings.form.onsubmit = e => {
    e.preventDefault()
    windowInstances.reset.submit()
}

adminEls.plugins.open.onclick = e => windowInstances.plugins.show()
adminEls.plugins.cancel.onclick = e => windowInstances.plugins.hide()
adminEls.plugins.dialog.onclick = e => {
    if (e.target === e.currentTarget) {
        e.stopPropagation()
        windowInstances.plugins.hide()
    }
}
adminEls.plugins.add.onclick = e => {
    if (adminEls.plugins.addRow.classList.contains("hidden")) {
        adminEls.plugins.addInput.value = ''
        hide({
            to_show: [adminEls.plugins.addRow],
            to_hide: [adminEls.plugins.error]
        })
        adminEls.plugins.addInput.focus()
    }
    else {
        hide({
            to_hide: [adminEls.plugins.addRow, adminEls.plugins.error],
        })
    }
}
adminEls.plugins.form.onsubmit = e => {
    e.preventDefault()
    windowInstances.plugins.submit()
}

adminEls.addUser.open.onclick = e => windowInstances.addUser.show()
adminEls.addUser.cancel.onclick = e => windowInstances.addUser.hide()
adminEls.addUser.dialog.onclick = e => {
    if (e.target === e.currentTarget) {
        e.stopPropagation()
        windowInstances.addUser.hide()
    }
}
adminEls.addUser.form.onsubmit = e => {
    e.preventDefault()
    windowInstances.addUser.submit()
}

adminEls.editUser.cancel.onclick = e => windowInstances.editUser.hide()
adminEls.editUser.dialog.onclick = e => {
    if (e.target === e.currentTarget) {
        e.stopPropagation()
        windowInstances.editUser.hide()
    }
}
adminEls.editUser.form.onsubmit = e => {
    e.preventDefault()
    windowInstances.editUser.submit()
}

adminEls.deleteUser.cancel.onclick = e => windowInstances.deleteUser.hide()
adminEls.deleteUser.dialog.onclick = e => {
    if (e.target === e.currentTarget) {
        e.stopPropagation()
        windowInstances.deleteUser.hide()
    }
}
adminEls.deleteUser.confirm.onclick = e => windowInstances.deleteUser.submit()

adminEls.uploadDb.open.onclick = e => windowInstances.uploadDatabase.show()
adminEls.uploadDb.cancel.onclick = e => windowInstances.uploadDatabase.hide()
adminEls.uploadDb.dialog.onclick = e => {
    if (e.target === e.currentTarget) {
        e.stopPropagation()
        windowInstances.uploadDatabase.hide()
    }
}
adminEls.uploadDb.form.onsubmit = e => {
    e.preventDefault()
    windowInstances.uploadDatabase.submit()
}

adminEls.downloadCurrentDatabase.onclick = e => downloadCurrentDatabase()

adminEls.importDb.cancel.onclick = e => windowInstances.importDatabase.hide()
adminEls.importDb.dialog.onclick = e => {
    if (e.target === e.currentTarget) {
        e.stopPropagation()
        windowInstances.importDatabase.hide()
    }
}
adminEls.importDb.form.onclick = e => {
    e.preventDefault()
    windowInstances.importDatabase.submit()
}

OnLoadRunner.add(
    loadAbout, loadSettings,
    loadUsers, loadBackups,
    windowInstances.reset.prepare
)
OnLoadRunner.runOnLoad()
