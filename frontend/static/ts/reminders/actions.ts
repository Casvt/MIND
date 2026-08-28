import { fetchAPI, getLocalStorage, hide, setLocalStorage, Window } from "../general";
import { libEls, ReminderType } from "./elements";

// region Tab Management
export let activeTab: ReminderType = ReminderType.REMINDER

export function showTab(selectedId: string): void {
    Object.values(libEls.tabSelectors).forEach(
        b => delete b.dataset.selected
    )
    libEls.tabSelectors[selectedId].dataset.selected = "true"
    activeTab = libEls.tabTypes[selectedId]
}

// region Search Bar
export function toggleWideView(): void {
    const storage = getLocalStorage()

    if (libEls.search.wide.dataset.selected) {
        // Currently wide, make slim
        storage.wide_library_view = false
        delete libEls.search.wide.dataset.selected
    }
    else
    {
        // Currently slim, make wide
        storage.wide_library_view = true
        libEls.search.wide.dataset.selected = "true"
    }

    setLocalStorage(storage)
}

// region Entry List
type TimelessReminderData = {
    id: number
    title: string
    text: string | null
    color: string | null
    notification_services: number[]
}

type ReminderData = TimelessReminderData & {
    time: number
    original_time: number | null
    repeat_quantity: string | null
    repeat_interval: number | null
    weekdays: number[] | null
    cron_schedule: string | null
    enabled: boolean
}

const weekDays = Array(7)
    .fill(0)
    .map(
        (_, idx) => new Date(Date.UTC(2017, 0, 2 + idx))
            .toLocaleDateString("en-US", {weekday: 'short'})
    )

export function getSorting(reminderType: ReminderType): string {
    const storage = getLocalStorage()
    switch (reminderType) {
        case ReminderType.REMINDER:
            return storage.sorting_reminders

        case ReminderType.STATIC_REMINDER:
            return storage.sorting_static

        case ReminderType.TEMPLATE:
            return storage.sorting_templates

        default:
            const exhaustive: never = reminderType
            throw new Error(`Handling of ${exhaustive} missing`)
    }
}

export function setSorting(reminderType: ReminderType, value: string): void {
    const storage = getLocalStorage()
    switch (reminderType) {
        case ReminderType.REMINDER:
            storage.sorting_reminders = value
            break

        case ReminderType.STATIC_REMINDER:
            storage.sorting_static = value
            break

        case ReminderType.TEMPLATE:
            storage.sorting_templates = value
            break

        default:
            const exhaustive: never = reminderType
            throw new Error(`Handling of ${exhaustive} missing`)
    }

    setLocalStorage(storage)
}

function buildTimelessLibraryEntry(data: TimelessReminderData): HTMLButtonElement {
    const entry = document.createElement('button')
    entry.classList.add('entry')
    entry.dataset.id = data.id.toString()
    if (data.color !== null)
        entry.style.setProperty('--color', data.color)

    const title = document.createElement('h2')
    title.innerText = data.title
    entry.appendChild(title)

    return entry
}

function buildLibraryEntry(data: ReminderData): HTMLButtonElement {
    const entry = buildTimelessLibraryEntry(data)

    const time = document.createElement('p')
    const offset = new Date(data.time * 1000).getTimezoneOffset() * -60
    const d = new Date((data.time + offset) * 1000)
    let formattedDate = d.toLocaleString(getLocalStorage().locale)

    if (data.repeat_interval !== null && data.repeat_quantity !== null) {
        var intervalText: string
        if (data.repeat_interval === 1) {
            const quantity = data.repeat_quantity.slice(0, -1)
            intervalText = ` (each ${quantity})`
        } else {
            intervalText = ` (every ${data.repeat_interval} ${data.repeat_quantity})`
        }
        formattedDate += intervalText

    } else if (data.weekdays !== null)
        formattedDate += ` (each ${data.weekdays.map(d => weekDays[d]).join(', ')})`

    if (!data.enabled)
        formattedDate += ' (Disabled)'

    time.innerText = formattedDate
    entry.appendChild(time)

    return entry
}

export function evaluateSizing(): void {
    const entries = [...libEls.tabs[activeTab].querySelectorAll<HTMLButtonElement>(
        "button:not(.add-entry)"
    )]
    entries.forEach(e => {
        const title = e.querySelector("h2")!
        e.classList.remove("expand")
        if (title.clientHeight < title.scrollHeight)
            e.classList.add("expand")
    })
}

function reminderTypeToUrl(reminderType: ReminderType): string {
    switch (reminderType) {
        case ReminderType.REMINDER:
            return '/reminders'

        case ReminderType.STATIC_REMINDER:
            return '/staticreminders'

        case ReminderType.TEMPLATE:
            return '/templates'

        default:
            const exhaustive: never = reminderType
            throw new Error(`Handling of ${exhaustive} missing`)
    }
}

const templates: Record<number, TimelessReminderData> = {}

export async function loadLibrary(reminderType: ReminderType): Promise<void> {
    let url = reminderTypeToUrl(reminderType)

    const params: Record<string, string> = {
        sort_by: getSorting(reminderType)
    }
    if (libEls.search.input.value) {
        url += '/search'
        params.query = libEls.search.input.value
    }

    const container = document.createDocumentFragment()
    const json = await fetchAPI(url, {params: params})
    if (reminderType === ReminderType.REMINDER)
        json.result.forEach((entry: ReminderData) => {
            const result = buildLibraryEntry(entry);
            result.onclick = () => windowInstances.editor.show({
                reminderType: reminderType,
                entryId: entry.id
            })
            container.appendChild(result)
        })
    else
        json.result.forEach((entry: TimelessReminderData) => {
            if (reminderType === ReminderType.TEMPLATE)
                templates[entry.id] = entry

            const result = buildTimelessLibraryEntry(entry)
            result.onclick = () => windowInstances.editor.show({
                reminderType: reminderType,
                entryId: entry.id
            })
            container.appendChild(result)
        })

    const table = libEls.tabs[reminderType]
    table.querySelectorAll("button.entry:not(.add-entry)").forEach(
        e => e.remove()
    )
    table.appendChild(container)

    evaluateSizing()
}

// region Editor
const reminderTypeToName = {
    [ReminderType.REMINDER]: "reminder",
    [ReminderType.STATIC_REMINDER]: "static reminder",
    [ReminderType.TEMPLATE]: "template",
}

const colorOptions = {
    "#232323": "Gray",
    "#49191e": "Red",
    "#171a42": "Blue",
    "#083b06": "Green",
    "#3b3506": "Yellow",
    "#300e40": "Purple"
}

export let nsExists = false

class EditorWindow implements Window {
    private state = {
        reminderType: null as ReminderType | null,
        entryId: null as number | null
    }
    public isShown: boolean = false

    public dialog = libEls.editor.dialog

    private prepareTemplates(): void {
        libEls.editor.inputs.template.querySelectorAll("option:not([value='0'])")
            .forEach(option => option.remove())
        Object.values(templates).forEach(template => {
            const option = document.createElement("option")
            option.value = template.id.toString()
            option.innerText = template.title
            libEls.editor.inputs.template.appendChild(option)
        })
    }

    public async prepare(): Promise<void> {
        // Templates
        this.prepareTemplates()

        // Colors
        Object.entries(colorOptions).forEach(([color, desc]) => {
            const option = document.createElement("option")
            option.value = color
            const container = document.createElement("div")
            container.setAttribute('style', `--color: ${color};`)
            container.innerText = desc
            option.appendChild(container)
            libEls.editor.inputs.color.appendChild(option)
        })

        // Notification Services
        return fetchAPI("/notificationservices")
        .then(json => {
            if (json.result.length > 0)
                nsExists = true

            json.result.forEach((ns: {id: number, title: string}) => {
                const option = document.createElement("option")
                option.value = ns.id.toString()
                option.innerText = ns.title
                libEls.editor.inputs.ns.appendChild(option)
            })
        })
    }

    public updateInputVisibility(hideAll: boolean): void {
        const inputs = libEls.editor.inputs,
            containers = libEls.editor.containers

        hide({to_hide: [
            containers.time, containers.interval,
            containers.weekday, containers.cron
        ]})
        inputs.time.required = false
        inputs.repeatInterval.required = false
        inputs.cron.required = false

        if (hideAll)
            return

        switch (inputs.repetition.value) {
            case "normal":
                inputs.time.required = true
                hide({to_show: [containers.time]})
                break

            case "repeated":
                inputs.time.required = true
                inputs.repeatInterval.required = true
                hide({to_show: [containers.time, containers.interval]})
                break

            case "week_days":
                inputs.time.required = true
                hide({to_show: [containers.time, containers.weekday]})
                break

            case "cron":
                inputs.cron.required = true
                hide({to_show: [containers.cron]})
                break

            default:
                break
        }
    }

    private resetForm(applyingTemplate: boolean): void {
        if (!applyingTemplate)
            libEls.editor.inputs.template.value = '0'
        libEls.editor.inputs.enabled.checked = true
        libEls.editor.inputs.color.value = Object.keys(colorOptions)[0]
        if (!applyingTemplate) {
            libEls.editor.inputs.repetition.value = 'normal'
            this.updateInputVisibility(
                this.state.reminderType !== ReminderType.REMINDER
            )
        }
        libEls.editor.inputs.time.value = ''
        libEls.editor.containers.time.classList.remove("error-input-container")
        libEls.editor.inputs.repeatInterval.value = ''
        libEls.editor.inputs.repeatQuantity.value = 'days'
        libEls.editor.inputs.weekday.forEach(w => w.checked = false)
        libEls.editor.containers.weekday.classList.remove("error-input")
        libEls.editor.inputs.cron.value = ''
        libEls.editor.containers.cron.classList.remove("error-input-container")
        libEls.editor.inputs.ns.value = getLocalStorage().default_service?.toString() || ''
        libEls.editor.containers.ns.classList.remove("error-input")
        if (!applyingTemplate)
            libEls.editor.containers.ns.open = false
        libEls.editor.inputs.title.value = ''
        libEls.editor.inputs.body.value = ''
    }

    private fillTimelessForm(data: TimelessReminderData): void {
        libEls.editor.inputs.color.value = Object.keys(colorOptions).includes(data.color || '')
            ? data.color || ''
            : Object.keys(colorOptions)[0]
        libEls.editor.inputs.ns.querySelectorAll("option").forEach(option => {
            option.selected = data.notification_services.includes(parseInt(option.value))
        })
        libEls.editor.inputs.title.value = data.title
        libEls.editor.inputs.body.value = data.text || ''

        this.updateInputVisibility(true)
    }

    private fillForm(data: ReminderData): void {
        this.fillTimelessForm(data)

        libEls.editor.inputs.enabled.checked = data.enabled
        const triggerDate = new Date(
            (data.time + new Date(data.time * 1000).getTimezoneOffset() * -60)
            * 1000
        )
        libEls.editor.inputs.time.value =
            triggerDate.toLocaleString("en-CA").slice(0, 10)
            + "T"
            + triggerDate.toTimeString().slice(0, 5)

        if (data.repeat_interval !== null && data.repeat_quantity !== null) {
            libEls.editor.inputs.repetition.value = 'repeated'
            libEls.editor.inputs.repeatInterval.value = data.repeat_interval.toString()
            libEls.editor.inputs.repeatQuantity.value = data.repeat_quantity
        }

        else if (data.weekdays !== null) {
            libEls.editor.inputs.repetition.value = 'week_days'
            libEls.editor.inputs.weekday.forEach(
                (c, idx) => c.checked = data.weekdays!.includes(idx)
            )
        }

        else if (data.cron_schedule !== null) {
            libEls.editor.inputs.repetition.value = 'cron'
            libEls.editor.inputs.cron.value = data.cron_schedule
        }

        this.updateInputVisibility(false)
    }

    private async getEntryData<T extends TimelessReminderData>(
        entryId: number,
        reminderType: ReminderType
    ): Promise<T> {
        const response = await fetchAPI(`${reminderTypeToUrl(reminderType)}/${entryId}`)
        return response.result
    }

    public async show(
        args: {reminderType: ReminderType, entryId: number | null}
    ): Promise<void> {
        this.isShown = true
        this.state.reminderType = args.reminderType
        this.state.entryId = args.entryId

        const actionTerm = args.entryId === null ? "Add" : "Edit"
        const typeTerm = reminderTypeToName[args.reminderType]
        libEls.editor.activity.innerText = `${actionTerm} a ${typeTerm}`

        libEls.editor.dialog.removeAttribute("class")
        if (args.reminderType === ReminderType.REMINDER)
            libEls.editor.dialog.classList.add("reminder-type")
        else if (args.reminderType === ReminderType.STATIC_REMINDER)
            libEls.editor.dialog.classList.add("static-type")
        else if (args.reminderType === ReminderType.TEMPLATE)
            libEls.editor.dialog.classList.add("template-type")
        if (args.entryId === null)
            libEls.editor.dialog.classList.add("add-type")
        else
            libEls.editor.dialog.classList.add("edit-type")

        this.resetForm(false)

        libEls.editor.testButton.classList.remove("show-sent")

        if (args.entryId !== null) {
            if (args.reminderType === ReminderType.REMINDER) {
                const data = await this.getEntryData<ReminderData>(
                    args.entryId, args.reminderType
                )
                this.fillForm(data)
            }

            else {
                const data = await this.getEntryData<TimelessReminderData>(
                    args.entryId, args.reminderType
                )
                this.fillTimelessForm(data)
            }
        }

        this.dialog.showModal()
    }

    public applyTemplate(templateId: number): void {
        const data = templates[templateId]
        this.resetForm(true)
        if (data !== undefined)
            this.fillTimelessForm(data)

        this.updateInputVisibility(
            this.state.reminderType !== ReminderType.REMINDER
        )
    }

    public hide(): void {
        this.isShown = false
        this.dialog.close()
    }

    public test(): void {
        let url: string,
            args: {method: string, body: any}

        libEls.editor.testButton.classList.remove("show-sent")
        libEls.editor.containers.ns.classList.remove("error-input")

        if (
            this.state.reminderType === ReminderType.STATIC_REMINDER
            && this.state.entryId !== null
        ) {
            // Trigger static reminder
            url = `${reminderTypeToUrl(this.state.reminderType)}/${this.state.entryId}`
            args = {method: "POST", body: ""}
        }

        else {
            // Test draft
            const ns = [...libEls.editor.inputs.ns.selectedOptions].map(
                option => parseInt(option.value)
            )
            if (!ns.length) {
                libEls.editor.containers.ns.classList.add("error-input")
                libEls.editor.containers.ns.open = true
                return
            }

            url = "/reminders/test"
            args = {
                method: "POST",
                body: {
                    title: libEls.editor.inputs.title.value,
                    text: libEls.editor.inputs.body.value,
                    notification_services: ns
                }
            }
        }

        libEls.editor.testButton.classList.add("show-sent")
        setTimeout(() => libEls.editor.testButton.classList.remove("show-sent"), 5000)
        fetchAPI(url, args)
    }

    public submit(): void {
        const reminderType = this.state.reminderType
        const entryId = this.state.entryId
        if (reminderType === null)
            throw new Error("Trying to submit reminder editor without having the dialog open")

        libEls.editor.containers.time.classList.remove("error-input-container")
        libEls.editor.containers.weekday.classList.remove("error-input")
        libEls.editor.containers.cron.classList.remove("error-input-container")
        libEls.editor.containers.ns.classList.remove("error-input")

        let url: string,
            method: string,
            data: Partial<TimelessReminderData | ReminderData>

        if (entryId === null) {
            // Add entry
            url = `${reminderTypeToUrl(reminderType)}`
            method = "POST"
        }
        else {
            // Edit entry
            url = `${reminderTypeToUrl(reminderType)}/${entryId}`
            method = "PUT"
        }

        const ns = [...libEls.editor.inputs.ns.selectedOptions].map(
            option => parseInt(option.value)
        )
        if (!ns.length) {
            libEls.editor.containers.ns.classList.add("error-input")
            libEls.editor.containers.ns.open = true
            return
        }
        if (reminderType === ReminderType.REMINDER) {
            let time: number,
                repeatQuantity: string | null = null,
                repeatInterval: number | null = null,
                weekDays: number[] | null = null,
                cronSchedule: string | null = null

            if (libEls.editor.inputs.repetition.value === "cron")
                time = Date.now() / 1000 + 5 + new Date().getTimezoneOffset() * 60
            else
                time = new Date(libEls.editor.inputs.time.value).getTime() / 1000
                    + new Date(libEls.editor.inputs.time.value).getTimezoneOffset() * 60

            switch (libEls.editor.inputs.repetition.value) {
                case "repeated":
                    repeatQuantity = libEls.editor.inputs.repeatQuantity.value
                    repeatInterval = libEls.editor.inputs.repeatInterval.valueAsNumber
                    break

                case "week_days":
                    weekDays = [] as number[]
                    libEls.editor.inputs.weekday.forEach((day, index) => {
                        if (day.checked)
                            weekDays?.push(index)
                    })
                    if (weekDays.length === 0) {
                        // Nothing selected while being required
                        libEls.editor.containers.weekday.classList.add("error-input")
                        return
                    }
                    break

                case "cron":
                    cronSchedule = libEls.editor.inputs.cron.value
                    break

                default:
                    break
            }

            data = {
                enabled: libEls.editor.inputs.enabled.checked,
                color: libEls.editor.inputs.color.value,
                time: time,
                repeat_quantity: repeatQuantity,
                repeat_interval: repeatInterval,
                weekdays: weekDays,
                cron_schedule: cronSchedule,
                notification_services: ns,
                title: libEls.editor.inputs.title.value,
                text: libEls.editor.inputs.body.value,
            }
        }

        else {
            data = {
                color: libEls.editor.inputs.color.value,
                notification_services: ns,
                title: libEls.editor.inputs.title.value,
                text: libEls.editor.inputs.body.value
            }
        }

        fetchAPI(url, {
            method: method,
            body: data
        })
        .then(() => {
            loadLibrary(reminderType)
            if (reminderType === ReminderType.TEMPLATE)
                this.prepareTemplates()

            this.hide()
        })
        .catch(json => {
            if (json.error === "InvalidTime")
                libEls.editor.containers.time.classList.add("error-input-container")

            else if (json.error === "InvalidKeyValue" && json.result.key === "cron_schedule")
                libEls.editor.containers.cron.classList.add("error-input-container")

            else
                console.log(json)
        })
    }

    public async remove(): Promise<void> {
        const reminderType = this.state.reminderType
        const entryId = this.state.entryId
        if (reminderType === null || entryId === null)
            throw new Error("Trying to delete reminder editor entry without having the dialog open")

        await fetchAPI(`${reminderTypeToUrl(reminderType)}/${entryId}`, {
            method: "DELETE"
        })

        loadLibrary(reminderType)
        if (reminderType === ReminderType.TEMPLATE)
            this.prepareTemplates()

        this.hide()
    }
}

export const windowInstances = {
    editor: new EditorWindow()
}
