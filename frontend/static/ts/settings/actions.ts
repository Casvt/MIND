import { setupClock } from "../base/actions";
import { Constants, fetchAPI, getLocalStorage, hide, setLocalStorage, UserData, Window } from "../general";
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
    private userData: UserData | null = null

    public prepare(): void {}

    public async show(args: object = {}): Promise<void> {
        this.userData = (await fetchAPI('/user')).result as UserData

        settingsEls.editAcc.containers.username.classList.remove("error-input-container")
        settingsEls.editAcc.containers.mfa.classList.remove("error-input-container")
        hide({to_hide: [
            settingsEls.editAcc.errors.usernameInvalid,
            settingsEls.editAcc.errors.usernameTaken
        ]})

        settingsEls.editAcc.inputs.username.value = this.userData.username
        settingsEls.editAcc.inputs.password.value = Constants.passwordReplacement
        settingsEls.editAcc.inputs.mfa.value = this.userData.mfa_apprise_url || ''

        settingsEls.editAcc.dialog.showModal()
    }

    public hide(): void {
        settingsEls.editAcc.dialog.close()
    }

    public submit(): void {
        const userData = this.userData
        if (userData === null)
            throw new Error("Account editor submitted before being opened")

        settingsEls.editAcc.containers.username.classList.remove("error-input-container")
        settingsEls.editAcc.containers.mfa.classList.remove("error-input-container")
        hide({to_hide: [
            settingsEls.editAcc.errors.usernameInvalid,
            settingsEls.editAcc.errors.usernameTaken
        ]})

        const data: Partial<{
                new_username: string,
                new_password: string,
                new_mfa_apprise_url: string | null
            }> = {},
            usernameValue = settingsEls.editAcc.inputs.username.value,
            passwordValue = settingsEls.editAcc.inputs.password.value,
            mfaValue = settingsEls.editAcc.inputs.mfa.value || null

        if (usernameValue && usernameValue !== userData.username)
            data.new_username = usernameValue
        if (passwordValue && passwordValue !== Constants.passwordReplacement)
            data.new_password = passwordValue
        if (mfaValue !== userData.mfa_apprise_url)
            data.new_mfa_apprise_url = mfaValue

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
                settingsEls.editAcc.containers.username.classList.add("error-input-container")
            }

            else if (json.error === "UsernameTaken") {
                hide({to_show: [settingsEls.editAcc.errors.usernameTaken]})
                settingsEls.editAcc.containers.username.classList.add("error-input-container")
            }

            else if (json.error === "InvalidKeyValue")
                settingsEls.editAcc.containers.mfa.classList.add("error-input-container")

            else
                console.log(json)
        })
    }
}
