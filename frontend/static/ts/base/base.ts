import { logout, OnLoadRunner } from "../general";
import { setupClock } from "./actions";
import { baseEls } from "./elements";

baseEls.logOut.onclick = () => logout()
baseEls.favIcon.onclick = () => window.location.href = "/reminders"
baseEls.navToggle.onclick = () => baseEls.navDivider.classList.toggle("show-nav")
baseEls.navBackground.onclick = () => baseEls.navDivider.classList.toggle("show-nav")

OnLoadRunner.add(setupClock)
