const reminderTypes = {
    reminder: document.getElementById('reminder-tab'),
    static_reminder: document.getElementById('static-reminder-tab'),
    template: document.getElementById('template-tab')
}

const clockElements = {
    time: document.querySelector('#clock-time'),
    date: document.querySelector('#clock-date')
}

const infoClasses = [
    'show-add-reminder', 'show-add-template', 'show-add-static-reminder',
    'show-edit-reminder', 'show-edit-template', 'show-edit-static-reminder'
]

function showWindow(id) {
    const window_container = document.querySelector('.window-container')
    if (id === "home") {
        window_container.classList.remove(
            'show-window',
            'inter-window-ani'
        )

        document.body.onkeydown = e => {
            if (
                e.key === '/'
                && document.activeElement !== LibEls.search_bar.input
            ) {
                LibEls.search_bar.input.focus()
                e.preventDefault()
            }
        }

    } else {
        const extra_window_container = document.querySelector('.extra-window-container')

        const offset = [
            ...extra_window_container.children
        ].indexOf(document.getElementById(id)) * -100

        extra_window_container.style.setProperty(
            '--y-offset',
            `${offset}%`
        )
        window_container.classList.add('show-window')
        setTimeout(
            () => window_container.classList.add('inter-window-ani'),
            constants.windowAnimationDuration
        )

        document.body.onkeydown = null
    }
}

function setMinutesClock(locale) {
    const currentTime = new Date()
    clockElements.date.innerText = currentTime.toLocaleDateString(locale)
    clockElements.time.innerText = currentTime.toLocaleTimeString(locale, {
        "timeStyle": "short"
    })
    clockTimer = setTimeout(
        () => setMinutesClock(locale),
        // Time until next minute
        (60 - currentTime.getSeconds()) * 1000
    )
}

function setSecondsClock(locale) {
    const currentTime = new Date()
    clockElements.date.innerText = currentTime.toLocaleDateString(locale)
    clockElements.time.innerText = currentTime.toLocaleTimeString(locale, {
        "timeStyle": "medium"
    })
    clockTimer = setTimeout(
        () => setSecondsClock(locale),
        1000
    )
}

var clockTimer = null
function setupClock() {
    const settings = getLocalStorage()

    if (clockTimer !== null) {
        clearTimeout(clockTimer)
        clockTimer = null
    }

    switch (settings['show_clock']) {
        case 'no':
            clockElements.time.innerText = ''
            clockElements.date.innerText = ''
            break

        case 'without_seconds':
            setMinutesClock(settings['locale'])
            break

        case 'with_seconds':
            setSecondsClock(settings['locale'])
            break

        default:
            break
    }

}

checkLogin()

showWindow("home")
document.querySelector("header img").onclick = e => showWindow("home")
setupClock()
