const reminderTypes = {
    reminder: document.getElementById('reminder-tab'),
    static_reminder: document.getElementById('static-reminder-tab'),
    template: document.getElementById('template-tab')
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
    }
}

checkLogin()
