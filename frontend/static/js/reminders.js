// ts/general.ts
var Constants = class {
  static svgNamespace = "http://www.w3.org/2000/svg";
  static autoSearchTimeout = 500;
  // ms
  static libraryRefreshInterval = 6e4;
  // ms
  static unsavedChangesMessage = "You have unsaved changes. Are you sure you want to leave?";
  static restartMessage = "MIND has detected changes to the hosting settings. It is required to login into MIND within 1 minute in order to keep the new hosting settings. Otherwise, MIND will go back to the old hosting settings.";
};
function getPreferredLocale() {
  for (const lang of navigator.languages) {
    if (lang.includes("-"))
      return lang;
    const locale = new Intl.Locale(lang).maximize();
    if (!locale.region)
      continue;
    return `${locale.language}-${locale.region}`;
  }
  return "en-US";
}
var localStorageDefaultValues = {
  api_key: null,
  locale: getPreferredLocale(),
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
  navBackground: document.getElementById("nav-background"),
  clock: {
    time: document.getElementById("clock-time"),
    date: document.getElementById("clock-date")
  }
};

// ts/base/actions.ts
var clockTimer = null;
function setMinutesClock(locale) {
  const currentTime = /* @__PURE__ */ new Date();
  baseEls.clock.date.innerText = currentTime.toLocaleDateString(locale, {
    dateStyle: "short"
  });
  baseEls.clock.time.innerText = currentTime.toLocaleTimeString(locale, {
    timeStyle: "short"
  });
  clockTimer = setTimeout(
    () => setMinutesClock(locale),
    // Time until next minute
    (60 - currentTime.getSeconds()) * 1e3
  );
}
function setSecondsClock(locale) {
  const currentTime = /* @__PURE__ */ new Date();
  baseEls.clock.date.innerText = currentTime.toLocaleDateString(locale, {
    dateStyle: "short"
  });
  baseEls.clock.time.innerText = currentTime.toLocaleTimeString(locale, {
    timeStyle: "medium"
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
  switch (settings.show_clock) {
    case "no":
      baseEls.clock.time.innerText = "";
      baseEls.clock.date.innerText = "";
      break;
    case "without_seconds":
      setMinutesClock(settings.locale);
      break;
    case "with_seconds":
      setSecondsClock(settings.locale);
      break;
    default:
      break;
  }
}

// ts/base/base.ts
baseEls.logOut.onclick = () => logout();
baseEls.favIcon.onclick = () => window.location.href = "/reminders";
baseEls.navToggle.onclick = () => baseEls.navDivider.classList.toggle("show-nav");
baseEls.navBackground.onclick = () => baseEls.navDivider.classList.toggle("show-nav");
OnLoadRunner.add(setupClock);

// ts/reminders/elements.ts
var libEls = {
  tabSelectors: {
    "reminder-tab-selector": document.getElementById("reminder-tab-selector"),
    "static-tab-selector": document.getElementById("static-tab-selector"),
    "template-tab-selector": document.getElementById("template-tab-selector")
  },
  tabTypes: {
    "reminder-tab-selector": 0 /* REMINDER */,
    "static-tab-selector": 1 /* STATIC_REMINDER */,
    "template-tab-selector": 2 /* TEMPLATE */
  },
  search: {
    form: document.getElementById("search-form"),
    input: document.getElementById("search-input"),
    clear: document.getElementById("clear-button"),
    sort: document.getElementById("sort-input"),
    wide: document.getElementById("wide-toggle")
  },
  tabs: {
    [0 /* REMINDER */]: document.getElementById("reminder-tab"),
    [1 /* STATIC_REMINDER */]: document.getElementById("static-reminder-tab"),
    [2 /* TEMPLATE */]: document.getElementById("template-tab")
  }
};

// ts/reminders/actions.ts
var activeTab = 0 /* REMINDER */;
function showTab(selectedId) {
  Object.values(libEls.tabSelectors).forEach(
    (b) => delete b.dataset.selected
  );
  libEls.tabSelectors[selectedId].dataset.selected = "true";
  activeTab = libEls.tabTypes[selectedId];
}
function toggleWideView() {
  const storage = getLocalStorage();
  if (libEls.search.wide.dataset.selected) {
    storage.wide_library_view = false;
    delete libEls.search.wide.dataset.selected;
  } else {
    storage.wide_library_view = true;
    libEls.search.wide.dataset.selected = "true";
  }
  setLocalStorage(storage);
}
var weekDays = Array(7).fill(0).map(
  (_, idx) => new Date(Date.UTC(2017, 0, 2 + idx)).toLocaleDateString("en-US", { weekday: "short" })
);
function getSorting(reminderType) {
  const storage = getLocalStorage();
  switch (reminderType) {
    case 0 /* REMINDER */:
      return storage.sorting_reminders;
    case 1 /* STATIC_REMINDER */:
      return storage.sorting_static;
    case 2 /* TEMPLATE */:
      return storage.sorting_templates;
    default:
      const exhaustive = reminderType;
      throw new Error(`Handling of ${exhaustive} missing`);
  }
}
function setSorting(reminderType, value) {
  const storage = getLocalStorage();
  switch (reminderType) {
    case 0 /* REMINDER */:
      storage.sorting_reminders = value;
      break;
    case 1 /* STATIC_REMINDER */:
      storage.sorting_static = value;
      break;
    case 2 /* TEMPLATE */:
      storage.sorting_templates = value;
      break;
    default:
      const exhaustive = reminderType;
      throw new Error(`Handling of ${exhaustive} missing`);
  }
  setLocalStorage(storage);
}
function buildTimelessLibraryEntry(data) {
  const entry = document.createElement("button");
  entry.classList.add("entry");
  entry.dataset.id = data.id.toString();
  if (data.color !== null)
    entry.style.setProperty("--color", data.color);
  const title = document.createElement("h2");
  title.innerText = data.title;
  entry.appendChild(title);
  return entry;
}
function buildLibraryEntry(data) {
  const entry = buildTimelessLibraryEntry(data);
  const time = document.createElement("p");
  const offset = new Date(data.time * 1e3).getTimezoneOffset() * -60;
  const d = new Date((data.time + offset) * 1e3);
  let formattedDate = d.toLocaleString(getLocalStorage().locale);
  if (data.repeat_interval !== null && data.repeat_quantity !== null) {
    var intervalText;
    if (data.repeat_interval === 1) {
      const quantity = data.repeat_quantity.slice(0, -1);
      intervalText = ` (each ${quantity})`;
    } else {
      intervalText = ` (every ${data.repeat_interval} ${data.repeat_quantity})`;
    }
    formattedDate += intervalText;
  } else if (data.weekdays !== null)
    formattedDate += ` (each ${data.weekdays.map((d2) => weekDays[d2]).join(", ")})`;
  if (!data.enabled)
    formattedDate += " (Disabled)";
  time.innerText = formattedDate;
  entry.appendChild(time);
  return entry;
}
function evaluateSizing() {
  const entries = [...libEls.tabs[activeTab].querySelectorAll(
    "button:not(.add-entry)"
  )];
  entries.forEach((e) => e.classList.remove("fit"));
  entries.forEach((e) => {
    const title = e.querySelector("h2");
    if (title.clientHeight < title.scrollHeight)
      e.classList.add("expand");
  });
  entries.forEach((e) => e.classList.add("fit"));
}
async function fillLibrary(reminderType) {
  let url;
  switch (reminderType) {
    case 0 /* REMINDER */:
      url = "/reminders";
      break;
    case 1 /* STATIC_REMINDER */:
      url = "/staticreminders";
      break;
    case 2 /* TEMPLATE */:
      url = "/templates";
      break;
    default:
      const exhaustive = reminderType;
      throw new Error(`Handling of ${exhaustive} missing`);
  }
  const params = {
    sort_by: getSorting(reminderType)
  };
  if (libEls.search.input.value) {
    url += "/search";
    params.query = libEls.search.input.value;
  }
  const container = document.createDocumentFragment();
  const json = await fetchAPI(url, { params });
  if (reminderType === 0 /* REMINDER */)
    json.result.forEach(
      (entry) => container.appendChild(buildLibraryEntry(entry))
    );
  else
    json.result.forEach(
      (entry) => container.appendChild(
        buildTimelessLibraryEntry(entry)
      )
    );
  const table = libEls.tabs[reminderType];
  table.querySelectorAll("button.entry:not(.add-entry)").forEach(
    (e) => e.remove()
  );
  table.appendChild(container);
  evaluateSizing();
}

// ts/reminders/reminders.ts
Object.values(libEls.tabSelectors).forEach(
  (b) => b.onclick = () => {
    const oldTab = activeTab;
    showTab(b.id);
    if (libEls.search.input.value) {
      libEls.search.input.value = "";
      fillLibrary(oldTab);
    } else
      evaluateSizing();
    libEls.search.sort.value = getSorting(activeTab);
  }
);
libEls.search.form.onsubmit = (e) => {
  e.preventDefault();
  if (autoSearchTimer !== null)
    clearTimeout(autoSearchTimer);
  fillLibrary(activeTab);
};
var autoSearchTimer = null;
libEls.search.input.onkeydown = () => {
  if (autoSearchTimer !== null)
    clearTimeout(autoSearchTimer);
  autoSearchTimer = setTimeout(
    () => fillLibrary(activeTab),
    Constants.autoSearchTimeout
  );
};
document.body.addEventListener("keydown", (e) => {
  if (e.key === "/" && document.activeElement !== libEls.search.input) {
    e.preventDefault();
    libEls.search.input.focus();
  }
});
libEls.search.clear.onclick = () => {
  libEls.search.input.value = "";
  fillLibrary(activeTab);
};
libEls.search.sort.value = getSorting(activeTab);
libEls.search.sort.onchange = () => {
  setSorting(activeTab, libEls.search.sort.value);
  fillLibrary(activeTab);
};
libEls.search.wide.onclick = () => toggleWideView();
{
  const storage = getLocalStorage();
  if (storage.wide_library_view)
    toggleWideView();
}
setInterval(
  () => fillLibrary(0 /* REMINDER */),
  Constants.libraryRefreshInterval
);
OnLoadRunner.add(
  () => fillLibrary(0 /* REMINDER */),
  () => fillLibrary(1 /* STATIC_REMINDER */),
  () => fillLibrary(2 /* TEMPLATE */)
);
OnLoadRunner.runOnLoad();
