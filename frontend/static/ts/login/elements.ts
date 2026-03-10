export const loginEls = {
    switchButtons: [...document.querySelectorAll(".switch-button")] as HTMLButtonElement[],
    formSwitch: document.getElementById("form-switch") as HTMLInputElement,
    mfaSwitch: document.getElementById("mfa-switch") as HTMLInputElement,
    login: {
        form: document.getElementById("login-form") as HTMLFormElement,
        inputContainers: {
			username: document.querySelector("#login-form .checked-input-container:has(#login-username)") as HTMLElement,
			password: document.querySelector("#login-form .checked-input-container:has(#login-password)") as HTMLElement
        },
		inputs: {
			username: document.getElementById("login-username") as HTMLInputElement,
			password: document.getElementById("login-password") as HTMLInputElement
		}
    },
    mfa: {
        form: document.getElementById("mfa-form") as HTMLFormElement,
        error: document.getElementById("invalid-mfa-code") as HTMLElement,
        inputContainer: document.getElementById("mfa-container") as HTMLElement
    },
    register: {
        form: document.getElementById("register-form") as HTMLFormElement,
        inputContainers: {
			username: document.querySelector("#register-form .checked-input-container:has(#register-username)") as HTMLElement,
        },
		inputs: {
			username: document.getElementById("register-username") as HTMLInputElement,
            password: document.getElementById("register-password") as HTMLInputElement
		},
		errors: {
			usernameInvalid: document.getElementById("invalid-username") as HTMLElement,
			usernameTaken: document.getElementById("taken-username") as HTMLElement
		}
    }
}
