// region Definitions
export enum ReminderType {
    REMINDER,
    STATIC_REMINDER,
    TEMPLATE
}

// region Elements
export const libEls = {
    tabSelectors: {
        "reminder-tab-selector": document.getElementById("reminder-tab-selector") as HTMLButtonElement,
        "static-tab-selector": document.getElementById("static-tab-selector") as HTMLButtonElement,
        "template-tab-selector": document.getElementById("template-tab-selector") as HTMLButtonElement
    } as Record<string, HTMLButtonElement>,
    
    tabTypes: {
        "reminder-tab-selector": ReminderType.REMINDER,
        "static-tab-selector": ReminderType.STATIC_REMINDER,
        "template-tab-selector": ReminderType.TEMPLATE
    } as Record<string, ReminderType>,

    search: {
        form: document.getElementById("search-form") as HTMLFormElement,
        input: document.getElementById("search-input") as HTMLInputElement,
        clear: document.getElementById("clear-button") as HTMLButtonElement,
        sort: document.getElementById("sort-input") as HTMLSelectElement,
        wide: document.getElementById("wide-toggle") as HTMLButtonElement
    },

    tabs: {
        [ReminderType.REMINDER]: document.getElementById("reminder-tab") as HTMLDivElement,
        [ReminderType.STATIC_REMINDER]: document.getElementById("static-reminder-tab") as HTMLDivElement,
        [ReminderType.TEMPLATE]: document.getElementById("template-tab") as HTMLDivElement
    },

    addButtons: {
        [ReminderType.REMINDER]: document.getElementById("add-reminder") as HTMLButtonElement,
        [ReminderType.STATIC_REMINDER]: document.getElementById("add-static-reminder") as HTMLButtonElement,
        [ReminderType.TEMPLATE]: document.getElementById("add-template") as HTMLButtonElement
    },

    editor: {
        dialog: document.getElementById("editor-dialog") as HTMLDialogElement,
        cancel: document.getElementById("close-editor") as HTMLButtonElement,
        activity: document.getElementById("editor-activity") as HTMLHeadingElement,
        form: document.getElementById("editor-form") as HTMLFormElement,
        testButton: document.getElementById("test-editor") as HTMLButtonElement,
        deleteButton: document.getElementById("delete-editor") as HTMLButtonElement,

        inputs: {
            template: document.getElementById("template-selection") as HTMLSelectElement,
            enabled: document.getElementById("enabled-toggle") as HTMLInputElement,
            color: document.getElementById("color-selection") as HTMLSelectElement,
            repetition: document.getElementById("repetition-selection") as HTMLSelectElement,
            time: document.getElementById("time-input") as HTMLInputElement,
            repeatInterval: document.getElementById("repeat-interval") as HTMLInputElement,
            repeatQuantity: document.getElementById("repeat-quantity") as HTMLSelectElement,
            weekday: [...document.querySelectorAll("#weekday-container input")] as HTMLInputElement[],
            cron: document.getElementById("cron-schedule") as HTMLInputElement,
            ns: document.getElementById("ns-selection") as HTMLSelectElement,
            title: document.getElementById("title-input") as HTMLInputElement,
            body: document.getElementById("body-input") as HTMLTextAreaElement
        },
        containers: {
            enabled: document.getElementById("enabled-container") as HTMLLabelElement,
            time: document.getElementById("time-container") as HTMLDivElement,
            interval: document.getElementById("repeat-container") as HTMLDivElement,
            weekday: document.getElementById("weekday-container") as HTMLDivElement,
            cron: document.getElementById("cron-container") as HTMLDivElement,
            ns: document.getElementById("ns-container") as HTMLDetailsElement
        }
    }
}
