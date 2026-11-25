import { Constants, downloadCurrentDatabase, downloadLogs, hide, logout, OnLoadRunner } from "../general";
import { loadAbout, loadBackups, loadSettings, loadUsers, restart, SettingsChanges, shutdown, submitSettings, windowInstances } from "./actions";
import { adminEls } from "./elements";

adminEls.settingsForm.onsubmit = e => {
    e.preventDefault()
    submitSettings()
}
adminEls.logout.onclick = () => {
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

adminEls.power.restart.onclick = () => restart()
adminEls.power.shutdown.onclick = () => shutdown()

adminEls.downloadLogs.onclick = () => downloadLogs()

adminEls.resetSettings.open.onclick = () => windowInstances.reset.show()
adminEls.resetSettings.form.onsubmit = e => {
    e.preventDefault()
    windowInstances.reset.submit()
}

adminEls.plugins.open.onclick = () => windowInstances.plugins.show()
adminEls.plugins.add.onclick = () => {
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

adminEls.addUser.open.onclick = () => windowInstances.addUser.show()
adminEls.addUser.form.onsubmit = e => {
    e.preventDefault()
    windowInstances.addUser.submit()
}

adminEls.editUser.form.onsubmit = e => {
    e.preventDefault()
    windowInstances.editUser.submit()
}

adminEls.deleteUser.confirm.onclick = () => windowInstances.deleteUser.submit()

adminEls.uploadDb.open.onclick = () => windowInstances.uploadDatabase.show()
adminEls.uploadDb.form.onsubmit = e => {
    e.preventDefault()
    windowInstances.uploadDatabase.submit()
}

adminEls.downloadCurrentDatabase.onclick = () => downloadCurrentDatabase()

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
