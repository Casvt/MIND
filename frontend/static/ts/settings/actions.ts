import { setupClock } from "../base/actions";
import { fetchAPI, getLocalStorage, hide, setLocalStorage, Window } from "../general";
import { settingsEls } from "./elements";

// region Settings
export async function loadSettings() {
    const values = getLocalStorage()
    settingsEls.settings.showClock.value = values.show_clock
    settingsEls.settings.locale.value = values.locale

    settingsEls.settings.defaultService.innerHTML = ''
    const json = await fetchAPI("/notificationservices")
    json.result.forEach((service: {id: number, title: string}) => {
        const entry = document.createElement("option")
        entry.value = service.id.toString()
        entry.innerText = service.title

        if (values.default_service === service.id)
            entry.selected = true

        settingsEls.settings.defaultService.appendChild(entry)
    })

    if (
        !json.result.map((s: {id: number, title: string}) => s.id)
            .includes(values.default_service)
    ) {
        values.default_service = json.result[0]?.id || null
        setLocalStorage(values)
    }
}

export function updateClockSetting() {
    const storage = getLocalStorage()
    storage.show_clock = settingsEls.settings.showClock.value
    setLocalStorage(storage)
    
    setupClock()
}

export function updateLocale() {
    const storage = getLocalStorage()
    storage.locale = settingsEls.settings.locale.value
    setLocalStorage(storage)

    setupClock()
}

export function updateDefaultService() {
    const storage = getLocalStorage()
    storage.default_service = parseInt(settingsEls.settings.defaultService.value)
    setLocalStorage(storage)
}

// region Edit Account
export class EditAccountWindow implements Window {
    public dialog = settingsEls.editAcc.dialog
    
    public prepare(): void {}
    
    public show(args: object = {}): void {
        settingsEls.editAcc.usernameContainer.classList.remove("error-input-container")
        hide({to_hide: [
            settingsEls.editAcc.errors.usernameInvalid,
            settingsEls.editAcc.errors.usernameTaken
        ]})
        
        settingsEls.editAcc.inputs.username.value = ''
        settingsEls.editAcc.inputs.password.value = ''
        
        settingsEls.editAcc.dialog.showModal()
    }
    
    public hide(): void {
        settingsEls.editAcc.dialog.close()
    }
    
    public submit(): void {
        settingsEls.editAcc.usernameContainer.classList.remove("error-input-container")
        hide({to_hide: [
            settingsEls.editAcc.errors.usernameInvalid,
            settingsEls.editAcc.errors.usernameTaken
        ]})
        
        const data: Record<string, string> = {}

        if (settingsEls.editAcc.inputs.username.value !== '')
            data.new_username = settingsEls.editAcc.inputs.username.value

        if (settingsEls.editAcc.inputs.password.value !== '')
            data.new_password = settingsEls.editAcc.inputs.password.value
        
        if (!Object.keys(data).length) {
            // Nothing changed
            this.hide()
            return
        }
        
        fetchAPI("/user", {
            method: "PUT",
            body: data
        })
        .then(() => this.hide())
        .catch(json => {
            if (json.error === "UsernameInvalid") {
                settingsEls.editAcc.errors.usernameInvalid.innerText = json.result.reason
                hide({to_show: [settingsEls.editAcc.errors.usernameInvalid]})
                settingsEls.editAcc.usernameContainer.classList.add("error-input-container")
            }
            else if (json.error === "UsernameTaken") {
                hide({to_show: [settingsEls.editAcc.errors.usernameTaken]})
                settingsEls.editAcc.usernameContainer.classList.add("error-input-container")
            }
            else
                console.log(json)
        })
    }
}
