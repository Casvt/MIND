import { createIcon, hide } from "../general"
import { nsEls } from "./elements"

type ParameterElement = HTMLInputElement | HTMLSelectElement | HTMLDivElement

type BaseParameter = {
    name: string
    required: boolean
    map_to: string
    prefix: string | null
    regex: string[] | null
}

type BasicParameter = BaseParameter & {
    type: "string" | "int" | "float" | "bool"
    min: number | null
    max: number | null
    default: any
}

type ChoiceParameter = BaseParameter & {
    type: "choice"
    options: string[]
    default: string
}

type ListEntry = {
    type: "string" | "int" | "float" | "bool"
    name: string
    required: boolean
    prefix: string | null
    regex: string[] | null
}

type ListParameter = BaseParameter & {
    type: "list"
    delim: string
    content: ListEntry[]
}

type Parameter = BasicParameter | ChoiceParameter | ListParameter

export type ServiceTemplate = {
    name: string
    doc_url: string
    details: {
        templates: string[]
        tokens: Parameter[]
        args: Parameter[]
    }
}

function createTitleInput(): HTMLInputElement {
	const title = document.createElement('input')
	title.classList.add('input-style')
	title.type = 'text'
	title.id = 'service-title'
	title.placeholder = 'Service Title'
	title.required = true
	return title
}

function createStringInput(param: BasicParameter): HTMLInputElement {
    const input = document.createElement('input')
    input.classList.add('input-style')
    input.type = 'text'
    input.required = param.required
    input.placeholder = `${param.name}${!param.required ? ' (Optional)' : ''}`
    return input
}

function createIntInput(param: BasicParameter): HTMLInputElement {
    const input = document.createElement('input')
    input.classList.add('input-style')
    input.type = 'number'
    input.required = param.required
    input.placeholder = `${param.name}${!param.required ? ' (Optional)' : ''}`
    if (param.min !== null)
        input.min = param.min.toString()
    if (param.max !== null)
        input.max = param.max.toString()
    return input
}

function createFloatInput(param: BasicParameter): HTMLInputElement {
    const input = document.createElement('input')
    input.classList.add('input-style')
    input.type = 'number'
    input.step = '0.1'
    input.required = param.required
    input.placeholder = `${param.name}${!param.required ? ' (Optional)' : ''}`
    if (param.min !== null)
        input.min = param.min.toString()
    if (param.max !== null)
        input.max = param.max.toString()
    return input
}

function createBoolInput(param: BasicParameter): HTMLSelectElement {
    const input = document.createElement('select')
    input.classList.add('input-style')
    // input.placeholder = param.name
    input.required = param.required

    const yesEntry = document.createElement("option")
    yesEntry.value = "true"
    yesEntry.innerText = "Yes"
    if (param.default === true)
        yesEntry.selected = true
    input.appendChild(yesEntry)

    const noEntry = document.createElement("option")
    noEntry.value = "false"
    noEntry.innerText = "No"
    if (param.default === false)
        noEntry.selected = true
    input.appendChild(noEntry)

    return input
}

function createChoiceInput(param: ChoiceParameter): HTMLSelectElement {
	const choice = document.createElement('select')
	choice.classList.add('input-style')
	choice.required = param.required
	// choice.placeholder = token.name
	param.options.forEach(option => {
		const entry = document.createElement('option')
		entry.value = option
		entry.innerText = option
        if (option === param.default)
            entry.selected = true
		choice.appendChild(entry)
	})

	return choice
}

function createEntriesList(param: ListParameter | ListEntry): HTMLDivElement {
	const list = document.createElement('div')
	list.classList.add('entries-list')

	const desc = document.createElement('p')
	desc.innerText = param.name
	list.appendChild(desc)

	const entries = document.createElement('div')
	entries.classList.add('input-entries')
	list.appendChild(entries)

	const addRow = document.createElement('div')
	addRow.classList.add('add-row', 'hidden')
	const addInput = document.createElement('input')
	addInput.classList.add('input-style')
	addInput.type = 'text'
	addInput.onkeydown = e => {
		if (e.key === "Enter") {
			e.preventDefault()
			e.stopImmediatePropagation()
			addEntry(entries, addInput.value, addRow)
		}
	}
	addRow.appendChild(addInput)
	const addRowButton = document.createElement('button')
	addRowButton.classList.add('input-style')
	addRowButton.type = 'button'
	addRowButton.innerText = 'Add'
	addRowButton.onclick = () => addEntry(entries, addInput.value, addRow)
	addRow.appendChild(addRowButton)
	list.appendChild(addRow)

	const toggleAddButton = document.createElement('button')
	toggleAddButton.classList.add('input-style')
	toggleAddButton.type = 'button'
	toggleAddButton.appendChild(createIcon("icon-plus"))
	toggleAddButton.onclick = () => toggleAddRow(addRow)
	list.appendChild(toggleAddButton)

	return list
}

function toggleAddRow(row: HTMLDivElement): void {
	if (row.classList.contains('hidden')) {
		// Show row
		const addInput = row.querySelector('input')!
		addInput.value = ''
        hide({to_show: [row]})
		addInput.focus()
	} else {
		// Hide row
        hide({to_hide: [row]})
	}
}

function addEntry(
    entriesList: HTMLDivElement,
    value: string,
    addRow: HTMLDivElement
): void {
	const entry = document.createElement('div')
	entry.innerText = value
	entriesList.appendChild(entry)
	toggleAddRow(addRow)
}

function createAdvancedToggle(): HTMLButtonElement {
    const button = document.createElement("button")
    button.classList.add("input-style")
    button.type = "button"
    button.innerText = "Show Advanced Settings"
    button.onclick = () => {
        nsEls.add.form.querySelectorAll('[data-is_arg="true"]').forEach(
            el => el.classList.toggle("hidden")
        )
        button.innerText = button.innerText === "Show Advanced Settings"
                        ? "Hide Advanced Settings"
                        : "Show Advanced Settings"
    }

    return button
}

function insertParameter(param: Parameter, index: number, isArg: boolean): void {
    let result: ParameterElement | null = null

    switch (param.type) {
        case "string":
            result = createStringInput(param)
            break

        case "int":
            result = createIntInput(param)
            break

        case "float":
            result = createFloatInput(param)
            break

        case "bool":
            const boolDesc = document.createElement("p")
            boolDesc.innerText = `${param.name}${!param.required ? ' (Optional)' : ''}`
            boolDesc.dataset.is_arg = isArg.toString()
            nsEls.add.form.appendChild(boolDesc)

            result = createBoolInput(param)
            break

        case "choice":
            const choiceDesc = document.createElement("p")
            choiceDesc.innerText = `${param.name}${!param.required ? ' (Optional)' : ''}`
            choiceDesc.dataset.is_arg = isArg.toString()
            nsEls.add.form.appendChild(choiceDesc)

            result = createChoiceInput(param)
            break

        case "list":
            result = document.createElement("div")

            const listDesc = document.createElement("p")
            listDesc.innerText = `${param.name}${!param.required ? ' (Optional)' : ''}`
            result.appendChild(listDesc)

            if (param.content.length === 0)
                result.appendChild(createEntriesList(param))
            else
                param.content.forEach((c, i) =>{
                    const list = createEntriesList(c)
                    list.dataset.content_index = i.toString()
                    result!.appendChild(list)
                })

            break

        default:
            return
    }

    result.dataset.index = index.toString()
    result.dataset.is_arg = isArg.toString()

    nsEls.add.form.appendChild(result)
}

export function createURLBuilder(data: ServiceTemplate): void {
    nsEls.add.form.innerHTML = ''

    const title = document.createElement("h3")
    title.innerText = data.name
    nsEls.add.form.appendChild(title)

    if (data.doc_url) {
        const docs = document.createElement("a")
        docs.href = data.doc_url
        docs.target = "_blank"
        docs.innerText = "Documentation"
        nsEls.add.form.appendChild(docs)
    }

    nsEls.add.form.appendChild(createTitleInput())

    data.details.tokens.forEach((param, idx) => insertParameter(param, idx, false))

    if (data.details.args.length > 0) {
        nsEls.add.form.appendChild(createAdvancedToggle())
        data.details.args.forEach((param, idx) => insertParameter(param, idx, true))

        hide({to_hide: [
            ...nsEls.add.form.querySelectorAll<HTMLElement>("[data-is_arg='true']")
        ]})
    }
}

export function buildURL(data: ServiceTemplate): string | null {
    console.debug(data)

    const tokens: Record<number, ParameterElement> = {}
    const args: Record<number, ParameterElement> = {}
    nsEls.add.form.querySelectorAll<ParameterElement>(":where(input, select, div)[data-index]").forEach(el => {
        const index = parseInt(el.dataset.index || '')
        if (el.dataset.is_arg === "false")
            tokens[index] = el
        else
            args[index] = el
    })

    const values: Record<string, string> = {}
    // Gather all values and format
	Object.entries(tokens).forEach(([idx, el]) => {
        const inputData = data.details.tokens[parseInt(idx)]

		if (inputData.type !== "list") {
			// Standard input
            //@ts-expect-error
			let value = `${inputData.prefix || ''}${el.value}`;
			if (value)
				values[inputData.map_to] = value;
		}

        else {
            // List input
			let value =
				[...el.querySelectorAll<HTMLElement>('.entries-list')]
				.map(l => {
                    let prefix = null
                    if (l.dataset.content_index)
                        prefix = inputData.content[
                                    parseInt(l.dataset.content_index)
                                ].prefix

					return [...l.querySelectorAll<HTMLDivElement>('.input-entries > div')]
                        .map(e => `${prefix || ''}${e.innerText}`)
                })
				.flat()
				.join(inputData.delim)

			if (value)
				values[inputData.map_to] = value
		}
	})

    // Find template(s) that match the given tokens
	const inputKeys = Object.keys(values).sort().join();
	const matchingTemplates = data.details.templates.filter(template =>
		inputKeys === template
            .replaceAll('}', '{')
            .split('{')
            .filter((e, i) => i % 2)
            .sort()
            .join()
	);

	if (!matchingTemplates.length)
		return null;

    // Build URL with template and values
	let template = matchingTemplates[0];

	for (const [key, value] of Object.entries(values))
		template = template.replace(`{${key}}`, value);

	// Add args
    const inputArgs = new URLSearchParams()
    Object.entries(args).forEach(([idx, el]) => {
        const inputData = data.details.args[parseInt(idx)]

        if (inputData.type !== "list") {
			// Standard input
            //@ts-expect-error
            const elValue = el.value
            if (
                elValue
                && (
                    [undefined, null, ''].includes(inputData.default)
                    || elValue !== inputData.default.toString()
                )
            )
                inputArgs.append(
                    inputData.map_to,
                    `${inputData.prefix || ''}${elValue}`
                )
		}

        else {
            // List input
			let value =
				[...el.querySelectorAll<HTMLElement>('.entries-list')]
				.map(l => {
                    let prefix = null
                    if (l.dataset.content_index)
                        prefix = inputData.content[
                                    parseInt(l.dataset.content_index)
                                ].prefix

					return [...l.querySelectorAll<HTMLDivElement>('.input-entries > div')]
                        .map(e => `${prefix || ''}${e.innerText}`)
                })
				.flat()
				.join(inputData.delim)

			if (value)
                inputArgs.append(inputData.map_to, value)
		}
    })

    if (inputArgs.size > 0)
        template += (template.includes("?") ? "&" : "?") + inputArgs.toString()

    template.replace(" ", "%20")

    console.debug(matchingTemplates)
    console.debug(template)

    return template
}

export function validateInputRegexes(data: ServiceTemplate): boolean {
    const faultyInputs: (HTMLInputElement | HTMLSelectElement)[] = []
    nsEls.add.form.querySelectorAll<HTMLInputElement | HTMLSelectElement>(":where(input, select)[data-index]").forEach(el => {
        el.classList.remove("error-input")

        const index = parseInt(el.dataset.index || '')
        let tokenData: Parameter;
        if (el.dataset.is_arg === "false")
            tokenData = data.details.tokens[index]
        else
            tokenData = data.details.args[index]

        const regex = tokenData.regex
        if (!regex)
            // No regex to validate against
            return

        if (!tokenData.required && el.value === "")
            // Not required and empty, so allowed
            return

        if (new RegExp(regex[0], regex[1]).test(el.value))
            // Valid value
            return

        // Invalid value
        faultyInputs.push(el)
    })

    faultyInputs.forEach(el => el.classList.add("error-input"))

    return faultyInputs.length === 0
}
