export const settingsEls = {
    settings: {
        showClock: document.getElementById("clock-input") as HTMLSelectElement,
        locale: document.getElementById("locale-input") as HTMLSelectElement,
        defaultService: document.getElementById("default-service-input") as HTMLSelectElement
    },

    editAcc: {
        open: document.getElementById("open-edit-account") as HTMLButtonElement,
        dialog: document.getElementById("edit-account-dialog") as HTMLDialogElement,
        form: document.getElementById("edit-account-form") as HTMLFormElement,

        containers: {
            username: document.getElementById("edit-username-container") as HTMLDivElement,
            mfa: document.getElementById("edit-mfa-container") as HTMLDivElement
        },
        inputs: {
            username: document.getElementById("edit-username") as HTMLInputElement,
            password: document.getElementById("edit-password") as HTMLInputElement,
            mfa: document.getElementById("edit-user-mfa") as HTMLInputElement
        },
        errors: {
            usernameInvalid: document.getElementById("invalid-username-error") as HTMLParagraphElement,
            usernameTaken: document.getElementById("username-taken-error") as HTMLParagraphElement
        }
    },

    delAcc: {
        confirm: document.getElementById("confirm-delete-account") as HTMLButtonElement
    }
}
