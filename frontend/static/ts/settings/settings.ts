import "../base/base";
import { deleteAccount, OnLoadRunner } from "../general";
import { EditAccountWindow, loadSettings, updateClockSetting, updateDefaultService, updateLocale } from "./actions";
import { settingsEls } from "./elements";

settingsEls.settings.showClock.onchange = () => updateClockSetting()
settingsEls.settings.locale.onchange = () => updateLocale()
settingsEls.settings.defaultService.onchange = () => updateDefaultService()

const editWindow = new EditAccountWindow()
settingsEls.editAcc.open.onclick = () => editWindow.show()
settingsEls.editAcc.dialog.onclick = e => {
    if (e.target === e.currentTarget) {
        e.stopPropagation()
        editWindow.hide()
    }
}
settingsEls.editAcc.close.onclick = () => editWindow.hide()
settingsEls.editAcc.form.onsubmit = e => {
    e.preventDefault()
    editWindow.submit()
}

settingsEls.delAcc.open.onclick = () => settingsEls.delAcc.dialog.showModal()
settingsEls.delAcc.dialog.onclick = e => {
    if (e.target === e.currentTarget) {
        e.stopPropagation()
        settingsEls.delAcc.dialog.close()
    }
}
settingsEls.delAcc.close.onclick = () => settingsEls.delAcc.dialog.close()
settingsEls.delAcc.confirm.onclick = () => deleteAccount()

OnLoadRunner.add(loadSettings)

OnLoadRunner.runOnLoad()
