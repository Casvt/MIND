import { getLocalStorage } from "../general"
import { baseEls } from "./elements"

var clockTimer: number | null = null

function setMinutesClock(locale: string): void {
    const currentTime = new Date()
    baseEls.clock.date.innerText = currentTime.toLocaleDateString(locale)
    baseEls.clock.time.innerText = currentTime.toLocaleTimeString(locale, {
        "timeStyle": "short"
    })
    clockTimer = setTimeout(
        () => setMinutesClock(locale),
        // Time until next minute
        (60 - currentTime.getSeconds()) * 1000
    )
}

function setSecondsClock(locale: string): void {
    const currentTime = new Date()
    baseEls.clock.date.innerText = currentTime.toLocaleDateString(locale)
    baseEls.clock.time.innerText = currentTime.toLocaleTimeString(locale, {
        "timeStyle": "medium"
    })
    clockTimer = setTimeout(
        () => setSecondsClock(locale),
        1000
    )
}

export function setupClock(): void {
    const settings = getLocalStorage()

    if (clockTimer !== null) {
        clearTimeout(clockTimer)
        clockTimer = null
    }

    switch (settings['show_clock']) {
        case 'no':
            baseEls.clock.time.innerText = ''
            baseEls.clock.date.innerText = ''
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
