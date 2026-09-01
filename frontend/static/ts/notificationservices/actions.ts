import { createIcon, fetchAPI, hide, nsTestFailReasonMap, Window } from "../general";
import { nsEls } from "./elements";
import { buildURL, createURLBuilder, ServiceTemplate, validateInputRegexes } from "./urlbuilder";

type ServiceData = {id: number, title: string, url: string}

const services: Record<number, ServiceData> = {}
const options: ServiceTemplate[] = []

class NSOptionsWindow implements Window {
    public dialog = nsEls.options.dialog
    public isShown: boolean = false

    public autoSearchTimer: number | null = null

    public prepare(): void {
        fetchAPI("/notificationservices/available")
        .then(json => {
            json.result.forEach((result: ServiceTemplate, index: number) => {
                options.push(result)

                const entry = document.createElement("button")
                entry.innerText = result.name
                entry.onclick = () => windowInstances.add.show({index: index})
                entry.style.viewTransitionName = `ns-${index}`
                nsEls.options.list.appendChild(entry)
            })
        })
    }

    public show(): void {
        this.isShown = true
        nsEls.options.search.value = ''
        this.searchOptions()
        this.dialog.showModal()
    }

    public hide(): void {
        this.isShown = false
        this.dialog.close()
    }

    public submit(): void { }

    public searchOptions() {
        if (this.autoSearchTimer !== null)
            clearTimeout(this.autoSearchTimer)

        const f = () => {
            const query = nsEls.options.search.value
                .toLowerCase()
                .replace('-', '')
                .replace('_', '')
                .replace(' ', '');

            if (query === '')
                hide({to_show: [...nsEls.options.list.querySelectorAll("button")]})

            else
                nsEls.options.list.querySelectorAll('button').forEach(
                    e => e.classList.toggle(
                        'hidden',
                        !e.innerText
                            .toLowerCase()
                            .replace('-', '')
                            .replace('_', '')
                            .replace(' ', '')
                            .includes(query)
                    )
                );
        };

        f()
        // View Transitions fully work, but the browser has
        // a bug that makes it look ugly currently. Once that's
        // fixed, we can enable it again.
        // if (!document.startViewTransition)
        //     f()
        // else
        //     document.startViewTransition(f)
    }
}

class AddNSWindow implements Window {
    public dialog = nsEls.add.dialog
    private serviceIndex: number | null = null

    public prepare(): void { }

    public show(args: {index: number}): void {
        this.serviceIndex = args.index
        nsEls.add.typeTitle.innerText = options[args.index].name

        createURLBuilder(options[args.index])

        nsEls.add.test.classList.remove("error-input")
        nsEls.add.submit.classList.remove("error-input")
        hide({to_hide: [nsEls.add.testError, nsEls.add.submitError]})

        windowInstances.options.hide()
        this.dialog.showModal()
    }

    public hide(): void {
        this.dialog.close()
        windowInstances.options.show()
    }

    public test(): void {
        const testButton = nsEls.add.test

        if (this.serviceIndex === null)
            throw new Error("Testing service before builder is opened")

        nsEls.add.test.classList.remove("error-input")
        nsEls.add.submit.classList.remove("error-input")
        hide({to_hide: [nsEls.add.testError, nsEls.add.submitError]})

        if (!validateInputRegexes(options[this.serviceIndex]))
            return

        const data = {
            url: buildURL(options[this.serviceIndex])
        }
        if (!data.url) {
            testButton.classList.add("error-input")
            nsEls.add.testError.innerText = "Can't create URL from combination of inputs"
            hide({to_show: [nsEls.add.testError]})
            return
        }

        fetchAPI("/notificationservices/test", {
            method: "POST",
            body: data
        })
        .then(json => {
            if (json.result.success) {
                testButton.classList.add("show-sent")
            } else {
                testButton.classList.add("error-input")
                nsEls.add.testError.innerText = nsTestFailReasonMap[json.result.description]
                hide({to_show: [nsEls.add.testError]})
            }
        })
    }

    public submit(): void {
        const addButton = nsEls.add.submit

        if (this.serviceIndex === null)
            throw new Error("Adding service before builder is opened")

        nsEls.add.test.classList.remove("error-input")
        nsEls.add.submit.classList.remove("error-input")
        hide({to_hide: [nsEls.add.testError, nsEls.add.submitError]})

        if (!validateInputRegexes(options[this.serviceIndex]))
            return

        const titleEl = document.getElementById("service-title") as HTMLInputElement | null
        if (!titleEl)
            throw new Error("Service Title element not found")

        const data = {
            title: titleEl.value,
            url: buildURL(options[this.serviceIndex])
        }
        if (!data.url) {
            addButton.classList.add("error-input")
            nsEls.add.submitError.innerText = "Can't create URL from combination of inputs"
            hide({to_show: [nsEls.add.submitError]})
            return
        }

        fetchAPI("/notificationservices", {
            method: "POST",
            body: data
        })
        .then(() => {
            addButton.classList.remove("error-input")

            loadServices()
            this.hide()
            windowInstances.options.hide()
        })
        .catch(json => {
            if (json.error === "URLInvalid") {
                addButton.classList.add("error-input")
                nsEls.add.submitError.innerText = nsTestFailReasonMap[json.result.reason]
                hide({to_show: [nsEls.add.submitError]})
            }
            else
                console.log(json)
        })
    }
}

class EditNSWindow implements Window {
    private serviceId: number | null = null

    public dialog = nsEls.edit.dialog

    public prepare(): void { }

    public show(args: {id: number}): void {
        this.serviceId = args.id
        nsEls.edit.inputs.title.value = services[args.id].title
        nsEls.edit.inputs.url.value = services[args.id].url
        nsEls.edit.urlContainer.classList.remove("error-input-container")
        this.dialog.showModal()
    }

    public hide(): void {
        this.dialog.close()
    }

    public submit(): void {
        nsEls.edit.urlContainer.classList.remove("error-input-container")

        const data = {
            title: nsEls.edit.inputs.title.value,
            url: nsEls.edit.inputs.url.value
        }

        fetchAPI(`/notificationservices/${this.serviceId}`, {
            method: "PUT",
            body: data
        })
        .then(() => {
            loadServices()
            this.hide()
        })
        .catch(json => {
            if (json.error === "URLInvalid" || json.error === "InvalidKeyValue") {
                nsEls.edit.error.innerText = nsTestFailReasonMap[json.result.reason] || "Syntax of URL invalid"
                hide({to_show: [nsEls.edit.error]})
                nsEls.edit.urlContainer.classList.add("error-input-container")
            }
            else
                console.log(json)
        })
    }
}

class DeleteNSWindow implements Window {
    private serviceId: number | null = null
    private deleteRemindersUsing: boolean = false

    public dialog = nsEls.delete.dialog

    public prepare(): void { }

    public show(args: {id: number}): void {
        this.serviceId = args.id
        nsEls.delete.confirm.innerText = "Delete"
        hide({to_hide: [nsEls.delete.error]})
        this.dialog.showModal()
    }

    public hide(): void {
        this.deleteRemindersUsing = false
        this.dialog.close()
    }

    public submit(): void {
        fetchAPI(`/notificationservices/${this.serviceId}`, {
            method: "DELETE",
            params: {delete_reminders_using: this.deleteRemindersUsing}
        })
        .then(() => {
            hide({to_hide: [nsEls.delete.error]})
            loadServices()
            this.hide()
        })
        .catch(json => {
            if (json.error === "NotificationServiceInUse") {
                nsEls.delete.error.innerText =
                    `The notification service is still in use by a ${json.result.reminder_type.toLowerCase()}. Do you want to delete all ${json.result.reminder_type.toLowerCase()}s that are using the notification service?`
                hide({to_show: [nsEls.delete.error]})

                nsEls.delete.confirm.innerText = "Delete Anyway"
                this.deleteRemindersUsing = true
            }
            else
                console.log(json)
        })
    }
}

export const windowInstances = {
    options: new NSOptionsWindow(),
    add: new AddNSWindow(),
    edit: new EditNSWindow(),
    delete: new DeleteNSWindow()
}

export async function loadServices(): Promise<void> {
    const json = await fetchAPI("/notificationservices")

    nsEls.servicesList.querySelectorAll("tr:not(.empty-row)").forEach(
        e => e.remove()
    )

    json.result.forEach((service: ServiceData) => {
        services[service.id] = service

        const entry = document.createElement("tr")
        entry.dataset.id = service.id.toString()

        const title = document.createElement("td")
        title.classList.add("title-column")
        title.innerText = service.title
        entry.appendChild(title)

        const url = document.createElement("td")
        url.classList.add("url-column")
        url.innerText = service.url
        entry.appendChild(url)

        const actions = document.createElement("td")
        actions.classList.add("action-column")
        entry.appendChild(actions)

        const editEntry = document.createElement("button")
        editEntry.title = "Edit service"
        editEntry.appendChild(createIcon("icon-edit"))
        editEntry.onclick = () => windowInstances.edit.show({id: service.id})
        actions.appendChild(editEntry)

        const deleteEntry = document.createElement("button")
        deleteEntry.title = "Delete service"
        deleteEntry.appendChild(createIcon("icon-delete"))
        deleteEntry.onclick = () => windowInstances.delete.show({id: service.id})
        actions.appendChild(deleteEntry)

        nsEls.servicesList.appendChild(entry)
    })
}
