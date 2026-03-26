import { fetchAPI, getLocalStorage, hide, invalidUsernameReasonMap, setLocalStorage } from "../general";
import { loginEls } from "./elements";

/**
 * Get the currently entered MFA code.
 * @returns The code.
 */
function getMFACode(): string {
    return [
        ...loginEls.mfa.inputContainer.querySelectorAll<HTMLInputElement>('input[type="number"]')
    ].map(el => el.value).join('')
}

/**
 * Try to log in with the credentials in the fields. If successful, redirect
 * to proper page. If MFA code is needed, that window is shown and this function
 * can be called again once it's entered. If a field has an invalid value, the
 * appropriate error is shown.
 * @param username Override the username used to attempt to log in. Use when
 *                  creating an account.
 * @param password Same as with username, but for password.
 */
export function login(username?: string, password?: string): void {
    loginEls.login.inputContainers.username.classList.remove("error-input-container")
    loginEls.login.inputContainers.password.classList.remove("error-input-container")

    if (!username)
        username = loginEls.login.inputs.username.value
    if (!password)
        password = loginEls.login.inputs.password.value

    let body: Record<string, string> = {
        username: username,
        password: password
    }
    if (loginEls.mfaSwitch.checked)
        body.mfa_code = getMFACode()

    fetchAPI("/auth/login", {
        redirectUnauth: false,
        method: "POST",
        body: body
    })
    .then(json => {
        if (json.error === "MFACodeRequired") {
            loginEls.mfa.error.classList.add("hidden")
            loginEls.mfaSwitch.checked = true
            loginEls.mfa.inputContainer.querySelector<HTMLInputElement>("input")?.focus()
            return
        }

        const storage = getLocalStorage()
        storage.api_key = json.result.api_key
        setLocalStorage(storage)

        if (json.result.admin)
            window.location.href = "./admin"
        else
            window.location.href = "./reminders"
    })
    .catch(json => {
        if (json.error === "UserNotFound")
            loginEls.login.inputContainers.username.classList.add("error-input-container")
        else if (json.error === "AccessUnauthorized") {
            loginEls.login.inputContainers.password.classList.add("error-input-container")
            loginEls.mfa.error.classList.remove("hidden")
        }
        else
            console.log(json)
    })
}

/**
 * Try to create a new account with the credentials in the fields. If successful,
 * redirect to the proper page. If a field has an invalid value, the appropriate
 * error is shown.
 */
export function register(): void {
    loginEls.register.inputContainers.username.classList.remove("error-input-container")
    hide({to_hide: [
        loginEls.register.errors.usernameInvalid,
        loginEls.register.errors.usernameTaken
    ]})

    const body = {
        username: loginEls.register.inputs.username.value,
        password: loginEls.register.inputs.password.value
    }

    fetchAPI("/user/add", {
        method: "POST",
        body: body
    })
    .then(_ => login(body.username, body.password))
    .catch(json => {
        if (json.error === "UsernameInvalid") {
            loginEls.register.errors.usernameInvalid.innerText = invalidUsernameReasonMap[json.result.reason]
            hide({to_show: [loginEls.register.errors.usernameInvalid]})
            loginEls.register.inputContainers.username.classList.add("error-input-container")
        }
        else if (json.error === "UsernameTaken") {
            hide({to_show: [loginEls.register.errors.usernameTaken]})
            loginEls.register.inputContainers.username.classList.add("error-input-container")
        }
        else
            console.log(json)
    })
}

/**
 * Check whether the creation of new accounts is allowed according to the admin
 * settings. If not, hide the button to switch to registering a new account.
 */
export function checkNewAccountsAllowed(): void {
    const storage = getLocalStorage()
    if (!storage.allow_new_accounts_cache)
        hide({to_hide: [loginEls.switchButtons[0]]})

    fetchAPI("/settings")
    .then(json => {
        if (!json.result.allow_new_accounts)
            hide({to_hide: [loginEls.switchButtons[0]]})
        else
            hide({to_show: [loginEls.switchButtons[0]]})

        if (storage.allow_new_accounts_cache !== json.result.allow_new_accounts) {
            storage.allow_new_accounts_cache = json.result.allow_new_accounts
            setLocalStorage(storage)
        }
    })
}
