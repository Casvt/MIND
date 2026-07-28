import "../base/base";
import { Constants, getLocalStorage, OnLoadRunner } from "../general";
import { activeTab, evaluateSizing, fillLibrary, getSorting, setSorting, showTab, toggleWideView } from "./actions";
import { libEls, ReminderType } from "./elements";

Object.values(libEls.tabSelectors).forEach(
    b => b.onclick = () => {
        const oldTab = activeTab
        showTab(b.id)
        if (libEls.search.input.value) {
            libEls.search.input.value = ''
            fillLibrary(oldTab)
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

    fillLibrary(activeTab)
}

let autoSearchTimer: number | null = null
libEls.search.input.onkeydown = () => {
    if (autoSearchTimer !== null)
        clearTimeout(autoSearchTimer)

    autoSearchTimer = setTimeout(
        () => fillLibrary(activeTab),
        Constants.autoSearchTimeout
    )
}
document.body.addEventListener("keydown", (e: KeyboardEvent) => {
    if (
        e.key === "/"
        && document.activeElement !== libEls.search.input
    ) {
        e.preventDefault()
        libEls.search.input.focus()
    }
})

libEls.search.clear.onclick = () => {
    libEls.search.input.value = ''
    fillLibrary(activeTab)
}

libEls.search.sort.value = getSorting(activeTab)
libEls.search.sort.onchange = () => {
    setSorting(activeTab, libEls.search.sort.value)
    fillLibrary(activeTab)
}

libEls.search.wide.onclick = () => toggleWideView()

{
    const storage = getLocalStorage()
    if (storage.wide_library_view)
        toggleWideView()
}

setInterval(
    () => fillLibrary(ReminderType.REMINDER),
    Constants.libraryRefreshInterval
)

OnLoadRunner.add(
    () => fillLibrary(ReminderType.REMINDER),
    () => fillLibrary(ReminderType.STATIC_REMINDER),
    () => fillLibrary(ReminderType.TEMPLATE)
)

OnLoadRunner.runOnLoad()
