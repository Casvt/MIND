export const adminEls = {
    logout: document.getElementById("logout") as HTMLButtonElement,

    about: {
        mindVersion: document.getElementById("mind-version") as HTMLElement,
        pythonVersion: document.getElementById("python-version") as HTMLElement,
        dbVersion: document.getElementById("db-version") as HTMLElement,
        dbLocation: document.getElementById("db-location") as HTMLElement,
        dataFolder: document.getElementById("data-folder") as HTMLElement
    },

    settingsSubmit: document.getElementById("save-settings") as HTMLButtonElement,
    changesCount: document.getElementById("changes-count") as HTMLSpanElement,
    settingsForm: document.getElementById("settings-form") as HTMLFormElement,
    dbBackupFolderInputContainer: document.querySelector("div.checked-input-container:has(#db-backup-folder)") as HTMLElement,
    settings: {
        allowNewAccounts: document.getElementById("allow-new-accounts") as HTMLInputElement,
        loginTime: document.getElementById("login-time") as HTMLInputElement,
        loginTimeReset: document.getElementById("login-time-reset") as HTMLInputElement,
        host: document.getElementById("host") as HTMLInputElement,
        port: document.getElementById("port") as HTMLInputElement,
        urlPrefix: document.getElementById("url-prefix") as HTMLInputElement,
        logLevel: document.getElementById("log-level") as HTMLInputElement,
        dbBackupInterval: document.getElementById("db-backup-interval") as HTMLInputElement,
        dbBackupAmount: document.getElementById("db-backup-amount") as HTMLInputElement,
        dbBackupFolder: document.getElementById("db-backup-folder") as HTMLInputElement
    },

    power: {
		restart: document.getElementById("restart-button") as HTMLButtonElement,
		shutdown: document.getElementById("shutdown-button") as HTMLButtonElement
	},

	downloadLogs: document.getElementById("download-logs") as HTMLButtonElement,
    downloadCurrentDatabase: document.getElementById("download-db") as HTMLButtonElement,

    resetSettings: {
        dialog: document.getElementById("reset-settings-dialog") as HTMLDialogElement,
        open: document.getElementById("open-reset-settings") as HTMLButtonElement,
        cancel: document.getElementById("close-reset-settings") as HTMLButtonElement,
        submit: document.getElementById("submit-reset-settings") as HTMLButtonElement,
        list: document.getElementById("reset-list") as HTMLDivElement,
        form: document.getElementById("reset-settings-form") as HTMLFormElement
    },

    userList: document.getElementById("user-list") as HTMLTableElement,
    addUser: {
        dialog: document.getElementById("add-user-dialog") as HTMLDialogElement,
        open: document.getElementById("open-add-user") as HTMLButtonElement,
        cancel: document.getElementById("close-add-user") as HTMLButtonElement,
        form: document.getElementById("add-user-form") as HTMLFormElement,

        inputContainers: {
            username: document.querySelector("#add-user-form .checked-input-container:has(input[type='text'])") as HTMLDivElement
        },
        inputs: {
            username: document.getElementById("add-user-username") as HTMLInputElement,
            password: document.getElementById("add-user-password") as HTMLInputElement
        },
        errors: {
            usernameInvalid: document.getElementById("add-invalid-username") as HTMLParagraphElement,
            usernameTaken: document.getElementById("add-taken-username") as HTMLParagraphElement
        }
    },
	editUser: {
		dialog: document.getElementById("edit-user-dialog") as HTMLDialogElement,
		username: document.getElementById("edit-target-username") as HTMLSpanElement,
		cancel: document.getElementById("close-edit-user") as HTMLButtonElement,
		form: document.getElementById("edit-user-form") as HTMLFormElement,

        inputContainers: {
			username: document.querySelector("#edit-user-form .checked-input-container:has(input[type='text'])") as HTMLDivElement
		},
		inputs: {
			username: document.getElementById("edit-user-username") as HTMLInputElement,
			password: document.getElementById("edit-user-password") as HTMLInputElement
		},
		errors: {
			usernameInvalid: document.getElementById("edit-invalid-username") as HTMLParagraphElement,
			usernameTaken: document.getElementById("edit-taken-username") as HTMLParagraphElement
		}
	},
    deleteUser: {
		dialog: document.getElementById("delete-user-dialog") as HTMLDialogElement,
		username: document.getElementById("delete-target-username") as HTMLSpanElement,
		cancel: document.getElementById("close-delete-user") as HTMLButtonElement,
		confirm: document.getElementById("confirm-delete-user") as HTMLButtonElement
	},

    backupList: document.getElementById("backup-list") as HTMLTableElement,
    downloadDb: document.getElementById("download-db-button") as HTMLButtonElement,
	uploadDb: {
		dialog: document.getElementById("upload-db-dialog") as HTMLDialogElement,
        open: document.getElementById("open-upload-db") as HTMLButtonElement,
		cancel: document.getElementById("close-upload-db") as HTMLButtonElement,
		submit: document.getElementById("submit-upload-db") as HTMLButtonElement,
		form: document.getElementById("upload-db-form") as HTMLFormElement,

        inputContainers: {
			file: document.querySelector("#upload-db-form .checked-input-container:has(input[type='file'])") as HTMLDivElement
		},
        inputs: {
			file: document.getElementById("database-file") as HTMLInputElement,
			keepHostingSettings: document.getElementById("copy-hosting-upload") as HTMLInputElement
		}
	},
	importDb: {
        dialog: document.getElementById("import-db-dialog") as HTMLDialogElement,
		backupName: document.getElementById("db-backup-name") as HTMLSpanElement,
		backupCreation: document.getElementById("db-creation-date") as HTMLSpanElement,
		cancel: document.getElementById("close-import-db") as HTMLButtonElement,
		submit: document.getElementById("submit-import-db") as HTMLButtonElement,
		form: document.getElementById("import-db-form") as HTMLFormElement,

        inputs: {
			keepHostingSettings: document.getElementById("copy-hosting-import") as HTMLInputElement
		}
	}
}
