export const baseEls = {
    logOut: document.getElementById("logout") as HTMLButtonElement,
    favIcon: document.querySelector("header img") as HTMLImageElement,

    navToggle: document.getElementById("toggle-nav") as HTMLButtonElement,
    navDivider: document.getElementById("nav-divider") as HTMLDivElement,
    navBackground: document.getElementById("nav-background") as HTMLDivElement,

    clock: {
        time: document.getElementById("clock-time") as HTMLDivElement,
        date: document.getElementById("clock-date") as HTMLDivElement
    }
}
