import { OnLoadRunner } from "../general";
import { checkNewAccountsAllowed, login, register } from "./actions";
import { loginEls } from "./elements";

loginEls.switchButtons.forEach(
    el => el.onclick = e => loginEls.formSwitch.checked = !loginEls.formSwitch.checked
)
loginEls.mfa.inputContainer.querySelectorAll<HTMLInputElement>("input:not(:last-of-type)").forEach(
    el => el.oninput = e => {
        if (['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'].includes(el.value)) {
            const nextInput = el.nextElementSibling as HTMLInputElement
            nextInput.focus()
        }
    }
)

loginEls.login.form.onsubmit = e => {
    e.preventDefault()
    login()
}
loginEls.mfa.form.onsubmit = e => {
    e.preventDefault()
    login()
}
loginEls.register.form.onsubmit = e => {
    e.preventDefault()
    register()
}

OnLoadRunner.add(checkNewAccountsAllowed)
OnLoadRunner.runOnLoad()
