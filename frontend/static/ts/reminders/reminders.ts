import "../base/base";
import { Constants, getLocalStorage, OnLoadRunner } from "../general";
import { activeTab, evaluateSizing, loadLibrary, getSorting, setSorting, showTab, toggleWideView, windowInstances, nsExists } from "./actions";
import { libEls, ReminderType } from "./elements";

// region Library
Object.values(libEls.tabSelectors).forEach(
    b => b.onclick = () => {
        const oldTab = activeTab
        showTab(b.id)
        if (libEls.search.input.value) {
            libEls.search.input.value = ''
            loadLibrary(oldTab)
        }
        else
            evaluateSizing()

        libEls.search.sort.value = getSorting(activeTab)
    }
)

libEls.search.form.onsubmit = e => {
    e.preventDefault()

    if (autoSearchTimer !== null)
        clearTimeout(autoSearchTimer)

    loadLibrary(activeTab)
}

let autoSearchTimer: number | null = null
libEls.search.input.onkeydown = () => {
    if (autoSearchTimer !== null)
        clearTimeout(autoSearchTimer)

    autoSearchTimer = setTimeout(
        () => loadLibrary(activeTab),
        Constants.autoSearchTimeout
    )
}
document.body.addEventListener("keydown", (e: KeyboardEvent) => {
    if (
        e.key === "/"
        && document.activeElement !== libEls.search.input
        && !windowInstances.editor.isShown
    ) {
        e.preventDefault()
        libEls.search.input.focus()
    }
})

libEls.search.clear.onclick = () => {
    libEls.search.input.value = ''
    loadLibrary(activeTab)
}

libEls.search.sort.value = getSorting(activeTab)
libEls.search.sort.onchange = () => {
    setSorting(activeTab, libEls.search.sort.value)
    loadLibrary(activeTab)
}

libEls.search.wide.onclick = () => toggleWideView()

function bindAddButtons(): void {
    Object.entries(libEls.addButtons).forEach(([type, button]) => {
        if (nsExists)
            button.onclick = () => windowInstances.editor.show({
                reminderType: parseInt(type),
                entryId: null
            })

        else {
            button.onclick = () => window.location.href = '/notificationservices'
            button.classList.add("error")
        }
    })
}

// region Editor
libEls.editor.cancel.onclick = () => windowInstances.editor.hide()
libEls.editor.dialog.onclick = e => {
    if (e.target === e.currentTarget) {
        e.stopPropagation()
        windowInstances.editor.hide()
    }
}
libEls.editor.form.onsubmit = e => {
    e.preventDefault()
    windowInstances.editor.submit()
}

libEls.editor.inputs.template.onchange = () => {
    windowInstances.editor.applyTemplate(
        parseInt(libEls.editor.inputs.template.value)
    )
}
libEls.editor.inputs.repetition.onchange = () => windowInstances.editor.updateInputVisibility(false)
libEls.editor.deleteButton.onclick = () => windowInstances.editor.remove()
libEls.editor.testButton.onclick = () => windowInstances.editor.test()

// region On Load
{
    const storage = getLocalStorage()
    if (storage.wide_library_view)
        toggleWideView()
}

setInterval(
    () => loadLibrary(ReminderType.REMINDER),
    Constants.libraryRefreshInterval
)

OnLoadRunner.add(
    () => {
        loadLibrary(ReminderType.REMINDER)
        loadLibrary(ReminderType.STATIC_REMINDER)
        return loadLibrary(ReminderType.TEMPLATE)
    },
    () => windowInstances.editor.prepare(),
    bindAddButtons
)

OnLoadRunner.runOnLoad()
