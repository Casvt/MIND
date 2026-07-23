import "../base/base";
import { Constants, OnLoadRunner } from "../general";
import { loadServices, windowInstances } from "./actions";
import { nsEls } from "./elements";

nsEls.options.open.onclick = () => windowInstances.options.show()
nsEls.options.dialog.onclick = e => {
    if (e.target === e.currentTarget) {
        e.stopPropagation()
        windowInstances.options.hide()
    }
}
nsEls.options.close.onclick = () => windowInstances.options.hide()
nsEls.options.search.oninput = () => {
    if (windowInstances.options.autoSearchTimer !== null)
        clearTimeout(windowInstances.options.autoSearchTimer)

    windowInstances.options.autoSearchTimer = setTimeout(
        windowInstances.options.searchOptions,
        Constants.autoSearchTimeoutNs
    )
}
document.body.addEventListener("keydown", (e: KeyboardEvent) => {
    if (
        e.key === "/"
        && windowInstances.options.isShown
        && document.activeElement !== nsEls.options.search
    ) {
        e.preventDefault()
        nsEls.options.search.focus()
    }
})

nsEls.add.dialog.onclick = e => {
    if (e.target === e.currentTarget) {
        e.stopPropagation()
        windowInstances.add.hide()
    }
}
nsEls.add.back.onclick = () => windowInstances.add.hide()
nsEls.add.test.onclick = () => windowInstances.add.test()
nsEls.add.form.onsubmit = e => {
    e.preventDefault()
    windowInstances.add.submit()
}

nsEls.edit.dialog.onclick = e => {
    if (e.target === e.currentTarget) {
        e.stopPropagation()
        windowInstances.edit.hide()
    }
}
nsEls.edit.close.onclick = () => windowInstances.edit.hide()
nsEls.edit.form.onsubmit = e => {
    e.preventDefault()
    windowInstances.edit.submit()
}

nsEls.delete.dialog.onclick = e => {
    if (e.target === e.currentTarget) {
        e.stopPropagation()
        windowInstances.delete.hide()
    }
}
nsEls.delete.close.onclick = () => windowInstances.delete.hide()
nsEls.delete.confirm.onclick = () => windowInstances.delete.submit()

OnLoadRunner.add(loadServices, windowInstances.options.prepare)

OnLoadRunner.runOnLoad()
