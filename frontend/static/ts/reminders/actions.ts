import { fetchAPI, getLocalStorage, setLocalStorage } from "../general";
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
    // TODO: OPEN EDIT
    // entry.onclick = e => showEdit(r.id, table)
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

export async function fillLibrary(reminderType: ReminderType): Promise<void> {
    let url: string;
    switch (reminderType) {
        case ReminderType.REMINDER:
            url = '/reminders'
            break

        case ReminderType.STATIC_REMINDER:
            url = '/staticreminders'
            break

        case ReminderType.TEMPLATE:
            url = '/templates'
            break

        default:
            const exhaustive: never = reminderType
            throw new Error(`Handling of ${exhaustive} missing`)
    }

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
        json.result.forEach(
            (entry: ReminderData) => container.appendChild(buildLibraryEntry(entry))
        )
    else
        json.result.forEach(
            (entry: TimelessReminderData) => container.appendChild(
                buildTimelessLibraryEntry(entry)
            )
        )

    const table = libEls.tabs[reminderType]
    table.querySelectorAll("button.entry:not(.add-entry)").forEach(
        e => e.remove()
    )
    table.appendChild(container)

    evaluateSizing()
}
