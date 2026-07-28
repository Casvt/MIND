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
    }
}
