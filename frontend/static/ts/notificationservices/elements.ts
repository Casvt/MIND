export const nsEls = {
    servicesList: document.getElementById("services-list") as HTMLTableSectionElement,

    options: {
        open: document.getElementById("open-service-options") as HTMLButtonElement,
        dialog: document.getElementById("ns-options-dialog") as HTMLDialogElement,
        close: document.getElementById("close-ns-options") as HTMLButtonElement,

        list: document.getElementById("options-list") as HTMLDivElement,
        search: document.getElementById("ns-search-input") as HTMLInputElement
    },

    add: {
        dialog: document.getElementById("add-ns-dialog") as HTMLDialogElement,
        back: document.getElementById("close-add-ns") as HTMLButtonElement,
        test: document.getElementById("test-service") as HTMLButtonElement,
        submit: document.getElementById("submit-add-ns") as HTMLButtonElement,

        typeTitle: document.getElementById("add-type") as HTMLSpanElement,
        form: document.getElementById("builder-form") as HTMLFormElement,
        
        testError: document.getElementById("test-ns-error") as HTMLDivElement,
        submitError: document.getElementById("submit-ns-error") as HTMLDivElement
    },

    edit: {
        dialog: document.getElementById("edit-ns-dialog") as HTMLDialogElement,
        form: document.getElementById("edit-ns-form") as HTMLFormElement,
        close: document.getElementById("close-edit-ns") as HTMLButtonElement,

        urlContainer: document.querySelector("#edit-ns-form .checked-input-container:has(#edit-url)") as HTMLDivElement,
        inputs: {
            title: document.getElementById("edit-title") as HTMLInputElement,
            url: document.getElementById("edit-url") as HTMLInputElement
        },
        error: document.getElementById("edit-invalid-url") as HTMLParagraphElement
    },

    delete: {
        dialog: document.getElementById("delete-ns-dialog") as HTMLDialogElement,
        close: document.getElementById("close-delete-ns") as HTMLButtonElement,
        confirm: document.getElementById("confirm-delete-ns") as HTMLButtonElement,
        error: document.getElementById("delete-ns-error") as HTMLParagraphElement
    }
}
