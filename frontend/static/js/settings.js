// ts/general.ts
var localStorageDefaultValues = {
  api_key: null,
  locale: "en-GB",
  default_service: null,
  sorting_reminders: "time",
  sorting_static: "title",
  sorting_templates: "title",
  wide_library_view: false,
  allow_new_accounts_cache: true,
  show_clock: "no"
};
function getLocalStorage() {
  return JSON.parse(localStorage.getItem("MIND") || "{}");
}
function setLocalStorage(new_values) {
  localStorage.setItem("MIND", JSON.stringify(new_values));
}
function setupLocalStorage() {
  if (!localStorage.getItem("MIND"))
    setLocalStorage(localStorageDefaultValues);
  const currentValues = getLocalStorage();
  const cleanedVersion = {};
  Object.keys(localStorageDefaultValues).forEach((k) => {
    if (currentValues[k] === void 0)
      cleanedVersion[k] = localStorageDefaultValues[k];
    else
      cleanedVersion[k] = currentValues[k];
  });
  setLocalStorage(cleanedVersion);
}
var defaultAPIRequestOptions = {
  method: "GET",
  params: {},
  body: {},
  redirectUnauth: true
};
async function fetchAPI(endpoint, options = {}) {
  const finalOptions = {
    ...defaultAPIRequestOptions,
    ...options
  };
  if (apiKey)
    finalOptions.params.api_key = apiKey;
  let formattedParams = new URLSearchParams(finalOptions.params).toString();
  if (formattedParams)
    formattedParams = "?" + formattedParams;
  let fetchOptions = {
    method: finalOptions.method
  };
  if (["POST", "PUT", "DELETE"].includes(finalOptions.method)) {
    if (finalOptions.body instanceof FormData) {
      fetchOptions.body = finalOptions.body;
    } else {
      fetchOptions.headers = { "Content-Type": "application/json" }, fetchOptions.body = JSON.stringify(finalOptions.body);
    }
  }
  const response = await fetch(
    `${urlPrefix}/api${endpoint}${formattedParams}`,
    fetchOptions
  );
  if (!response.ok) {
    if (finalOptions.redirectUnauth && response.status === 401) {
      const storage = getLocalStorage();
      storage.api_key = null;
      setLocalStorage(storage);
      if (window.location.pathname !== `${urlPrefix}/`)
        window.location.href = `${urlPrefix}/`;
    }
    throw await response.json();
  }
  return await response.json();
}
async function checkLogin() {
  if (!apiKey) {
    if (window.location.pathname !== `${urlPrefix}/`)
      window.location.href = `${urlPrefix}/`;
    return;
  }
  await fetchAPI("/auth/status").then((json) => {
    if (json.result.admin && window.location.pathname !== `${urlPrefix}/admin`)
      window.location.href = `${urlPrefix}/admin`;
    else if (!json.result.admin && (window.location.pathname !== `${urlPrefix}/reminders` && window.location.pathname !== `${urlPrefix}/notificationservices` && window.location.pathname !== `${urlPrefix}/settings`))
      window.location.href = `${urlPrefix}/reminders`;
  });
}
function logout() {
  fetchAPI("/auth/logout", { method: "POST" }).then((_) => {
    const storage = getLocalStorage();
    storage.api_key = null;
    setLocalStorage(storage);
    window.location.href = `${urlPrefix}/`;
  });
}
var urlPrefix = document.getElementById("url_prefix")?.dataset.value || "";
var apiKey = getLocalStorage().api_key;
var OnLoadRunner = class {
  static onLoadFunctions = [];
  /**
   * Register one or more functions to run on load. They are run after the
   * functions that are already registered. If multiple are added, they are
   * run in the order that they are supplied.
   * @param {CallableFunction[]} functions The functions to register.
   */
  static add(...functions) {
    this.onLoadFunctions.push(...functions);
  }
  /**
   * Run all registered functions sequentially.
   */
  static async runOnLoad() {
    for (const f of this.onLoadFunctions) {
      await f();
    }
  }
};
OnLoadRunner.add(setupLocalStorage, checkLogin);

// ts/base/elements.ts
var baseEls = {
  logOut: document.getElementById("logout"),
  favIcon: document.querySelector("header img"),
  navToggle: document.getElementById("toggle-nav"),
  navDivider: document.getElementById("nav-divider"),
  clock: {
    time: document.getElementById("clock-time"),
    date: document.getElementById("clock-date")
  }
};

// ts/base/actions.ts
var clockTimer = null;
function setMinutesClock(locale) {
  const currentTime = /* @__PURE__ */ new Date();
  baseEls.clock.date.innerText = currentTime.toLocaleDateString(locale);
  baseEls.clock.time.innerText = currentTime.toLocaleTimeString(locale, {
    "timeStyle": "short"
  });
  clockTimer = setTimeout(
    () => setMinutesClock(locale),
    // Time until next minute
    (60 - currentTime.getSeconds()) * 1e3
  );
}
function setSecondsClock(locale) {
  const currentTime = /* @__PURE__ */ new Date();
  baseEls.clock.date.innerText = currentTime.toLocaleDateString(locale);
  baseEls.clock.time.innerText = currentTime.toLocaleTimeString(locale, {
    "timeStyle": "medium"
  });
  clockTimer = setTimeout(
    () => setSecondsClock(locale),
    1e3
  );
}
function setupClock() {
  const settings = getLocalStorage();
  if (clockTimer !== null) {
    clearTimeout(clockTimer);
    clockTimer = null;
  }
  switch (settings["show_clock"]) {
    case "no":
      baseEls.clock.time.innerText = "";
      baseEls.clock.date.innerText = "";
      break;
    case "without_seconds":
      setMinutesClock(settings["locale"]);
      break;
    case "with_seconds":
      setSecondsClock(settings["locale"]);
      break;
    default:
      break;
  }
}

// ts/base/base.ts
baseEls.logOut.onclick = () => logout();
baseEls.favIcon.onclick = () => window.location.href = "/reminders";
baseEls.navToggle.onclick = () => baseEls.navDivider.classList.toggle("show-nav");
OnLoadRunner.add(setupClock);

// ts/settings/settings.ts
OnLoadRunner.runOnLoad();
