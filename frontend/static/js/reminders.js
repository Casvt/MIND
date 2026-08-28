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
function hide({ to_hide = [], to_show = [] } = {}) {
  to_hide.forEach((el) => el.classList.add("hidden"));
  if (to_show !== null && to_show !== void 0)
    to_show.forEach((el) => el.classList.remove("hidden"));
}
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
  },
  addButtons: {
    [0 /* REMINDER */]: document.getElementById("add-reminder"),
    [1 /* STATIC_REMINDER */]: document.getElementById("add-static-reminder"),
    [2 /* TEMPLATE */]: document.getElementById("add-template")
  },
  editor: {
    dialog: document.getElementById("editor-dialog"),
    cancel: document.getElementById("close-editor"),
    activity: document.getElementById("editor-activity"),
    form: document.getElementById("editor-form"),
    testButton: document.getElementById("test-editor"),
    deleteButton: document.getElementById("delete-editor"),
    inputs: {
      template: document.getElementById("template-selection"),
      enabled: document.getElementById("enabled-toggle"),
      color: document.getElementById("color-selection"),
      repetition: document.getElementById("repetition-selection"),
      time: document.getElementById("time-input"),
      repeatInterval: document.getElementById("repeat-interval"),
      repeatQuantity: document.getElementById("repeat-quantity"),
      weekday: [...document.querySelectorAll("#weekday-container input")],
      cron: document.getElementById("cron-schedule"),
      ns: document.getElementById("ns-selection"),
      title: document.getElementById("title-input"),
      body: document.getElementById("body-input")
    },
    containers: {
      enabled: document.getElementById("enabled-container"),
      time: document.getElementById("time-container"),
      interval: document.getElementById("repeat-container"),
      weekday: document.getElementById("weekday-container"),
      cron: document.getElementById("cron-container"),
      ns: document.getElementById("ns-container")
    }
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
  entries.forEach((e) => {
    const title = e.querySelector("h2");
    e.classList.remove("expand");
    if (title.clientHeight < title.scrollHeight)
      e.classList.add("expand");
  });
}
function reminderTypeToUrl(reminderType) {
  switch (reminderType) {
    case 0 /* REMINDER */:
      return "/reminders";
    case 1 /* STATIC_REMINDER */:
      return "/staticreminders";
    case 2 /* TEMPLATE */:
      return "/templates";
    default:
      const exhaustive = reminderType;
      throw new Error(`Handling of ${exhaustive} missing`);
  }
}
var templates = {};
async function loadLibrary(reminderType) {
  let url = reminderTypeToUrl(reminderType);
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
    json.result.forEach((entry) => {
      const result = buildLibraryEntry(entry);
      result.onclick = () => windowInstances.editor.show({
        reminderType,
        entryId: entry.id
      });
      container.appendChild(result);
    });
  else
    json.result.forEach((entry) => {
      if (reminderType === 2 /* TEMPLATE */)
        templates[entry.id] = entry;
      const result = buildTimelessLibraryEntry(entry);
      result.onclick = () => windowInstances.editor.show({
        reminderType,
        entryId: entry.id
      });
      container.appendChild(result);
    });
  const table = libEls.tabs[reminderType];
  table.querySelectorAll("button.entry:not(.add-entry)").forEach(
    (e) => e.remove()
  );
  table.appendChild(container);
  evaluateSizing();
}
var reminderTypeToName = {
  [0 /* REMINDER */]: "reminder",
  [1 /* STATIC_REMINDER */]: "static reminder",
  [2 /* TEMPLATE */]: "template"
};
var colorOptions = {
  "#3c3c3c": "Gray",
  "#49191e": "Red",
  "#171a42": "Blue",
  "#083b06": "Green",
  "#3b3506": "Yellow",
  "#300e40": "Purple"
};
var nsExists = false;
var EditorWindow = class {
  state = {
    reminderType: null,
    entryId: null
  };
  isShown = false;
  dialog = libEls.editor.dialog;
  prepareTemplates() {
    libEls.editor.inputs.template.querySelectorAll("option:not([value='0'])").forEach((option) => option.remove());
    Object.values(templates).forEach((template) => {
      const option = document.createElement("option");
      option.value = template.id.toString();
      option.innerText = template.title;
      libEls.editor.inputs.template.appendChild(option);
    });
  }
  async prepare() {
    this.prepareTemplates();
    Object.entries(colorOptions).forEach(([color, desc]) => {
      const option = document.createElement("option");
      option.value = color;
      const container = document.createElement("div");
      container.setAttribute("style", `--color: ${color};`);
      container.innerText = desc;
      option.appendChild(container);
      libEls.editor.inputs.color.appendChild(option);
    });
    return fetchAPI("/notificationservices").then((json) => {
      if (json.result.length > 0)
        nsExists = true;
      json.result.forEach((ns) => {
        const option = document.createElement("option");
        option.value = ns.id.toString();
        option.innerText = ns.title;
        libEls.editor.inputs.ns.appendChild(option);
      });
    });
  }
  updateInputVisibility(hideAll) {
    const inputs = libEls.editor.inputs, containers = libEls.editor.containers;
    hide({ to_hide: [
      containers.time,
      containers.interval,
      containers.weekday,
      containers.cron
    ] });
    inputs.time.required = false;
    inputs.repeatInterval.required = false;
    inputs.cron.required = false;
    if (hideAll)
      return;
    switch (inputs.repetition.value) {
      case "normal":
        inputs.time.required = true;
        hide({ to_show: [containers.time] });
        break;
      case "repeated":
        inputs.time.required = true;
        inputs.repeatInterval.required = true;
        hide({ to_show: [containers.time, containers.interval] });
        break;
      case "week_days":
        inputs.time.required = true;
        hide({ to_show: [containers.time, containers.weekday] });
        break;
      case "cron":
        inputs.cron.required = true;
        hide({ to_show: [containers.cron] });
        break;
      default:
        break;
    }
  }
  resetForm(applyingTemplate) {
    if (!applyingTemplate)
      libEls.editor.inputs.template.value = "0";
    libEls.editor.inputs.enabled.checked = true;
    libEls.editor.inputs.color.value = Object.keys(colorOptions)[0];
    if (!applyingTemplate) {
      libEls.editor.inputs.repetition.value = "normal";
      this.updateInputVisibility(
        this.state.reminderType !== 0 /* REMINDER */
      );
    }
    libEls.editor.inputs.time.value = "";
    libEls.editor.containers.time.classList.remove("error-input-container");
    libEls.editor.inputs.repeatInterval.value = "";
    libEls.editor.inputs.repeatQuantity.value = "days";
    libEls.editor.inputs.weekday.forEach((w) => w.checked = false);
    libEls.editor.containers.weekday.classList.remove("error-input");
    libEls.editor.inputs.cron.value = "";
    libEls.editor.containers.cron.classList.remove("error-input-container");
    libEls.editor.inputs.ns.value = getLocalStorage().default_service?.toString() || "";
    libEls.editor.containers.ns.classList.remove("error-input");
    if (!applyingTemplate)
      libEls.editor.containers.ns.open = false;
    libEls.editor.inputs.title.value = "";
    libEls.editor.inputs.body.value = "";
  }
  fillTimelessForm(data) {
    libEls.editor.inputs.color.value = data.color || Object.keys(colorOptions)[0];
    libEls.editor.inputs.ns.querySelectorAll("option").forEach((option) => {
      option.selected = data.notification_services.includes(parseInt(option.value));
    });
    libEls.editor.inputs.title.value = data.title;
    libEls.editor.inputs.body.value = data.text || "";
    this.updateInputVisibility(true);
  }
  fillForm(data) {
    this.fillTimelessForm(data);
    libEls.editor.inputs.enabled.checked = data.enabled;
    const triggerDate = new Date(
      (data.time + new Date(data.time * 1e3).getTimezoneOffset() * -60) * 1e3
    );
    libEls.editor.inputs.time.value = triggerDate.toLocaleString("en-CA").slice(0, 10) + "T" + triggerDate.toTimeString().slice(0, 5);
    if (data.repeat_interval !== null && data.repeat_quantity !== null) {
      libEls.editor.inputs.repetition.value = "repeated";
      libEls.editor.inputs.repeatInterval.value = data.repeat_interval.toString();
      libEls.editor.inputs.repeatQuantity.value = data.repeat_quantity;
    } else if (data.weekdays !== null) {
      libEls.editor.inputs.repetition.value = "week_days";
      libEls.editor.inputs.weekday.forEach(
        (c, idx) => c.checked = data.weekdays.includes(idx)
      );
    } else if (data.cron_schedule !== null) {
      libEls.editor.inputs.repetition.value = "cron";
      libEls.editor.inputs.cron.value = data.cron_schedule;
    }
    this.updateInputVisibility(false);
  }
  async getEntryData(entryId, reminderType) {
    const response = await fetchAPI(`${reminderTypeToUrl(reminderType)}/${entryId}`);
    return response.result;
  }
  async show(args) {
    this.isShown = true;
    this.state.reminderType = args.reminderType;
    this.state.entryId = args.entryId;
    const actionTerm = args.entryId === null ? "Add" : "Edit";
    const typeTerm = reminderTypeToName[args.reminderType];
    libEls.editor.activity.innerText = `${actionTerm} a ${typeTerm}`;
    libEls.editor.dialog.removeAttribute("class");
    if (args.reminderType === 0 /* REMINDER */)
      libEls.editor.dialog.classList.add("reminder-type");
    else if (args.reminderType === 1 /* STATIC_REMINDER */)
      libEls.editor.dialog.classList.add("static-type");
    else if (args.reminderType === 2 /* TEMPLATE */)
      libEls.editor.dialog.classList.add("template-type");
    if (args.entryId === null)
      libEls.editor.dialog.classList.add("add-type");
    else
      libEls.editor.dialog.classList.add("edit-type");
    this.resetForm(false);
    libEls.editor.testButton.classList.remove("show-sent");
    if (args.entryId !== null) {
      if (args.reminderType === 0 /* REMINDER */) {
        const data = await this.getEntryData(
          args.entryId,
          args.reminderType
        );
        this.fillForm(data);
      } else {
        const data = await this.getEntryData(
          args.entryId,
          args.reminderType
        );
        this.fillTimelessForm(data);
      }
    }
    this.dialog.showModal();
  }
  applyTemplate(templateId) {
    const data = templates[templateId];
    this.resetForm(true);
    if (data !== void 0)
      this.fillTimelessForm(data);
    this.updateInputVisibility(
      this.state.reminderType !== 0 /* REMINDER */
    );
  }
  hide() {
    this.isShown = false;
    this.dialog.close();
  }
  test() {
    let url, args;
    libEls.editor.testButton.classList.remove("show-sent");
    libEls.editor.containers.ns.classList.remove("error-input");
    if (this.state.reminderType === 1 /* STATIC_REMINDER */ && this.state.entryId !== null) {
      url = `${reminderTypeToUrl(this.state.reminderType)}/${this.state.entryId}`;
      args = { method: "POST", body: "" };
    } else {
      const ns = [...libEls.editor.inputs.ns.selectedOptions].map(
        (option) => parseInt(option.value)
      );
      if (!ns.length) {
        libEls.editor.containers.ns.classList.add("error-input");
        libEls.editor.containers.ns.open = true;
        return;
      }
      url = "/reminders/test";
      args = {
        method: "POST",
        body: {
          title: libEls.editor.inputs.title.value,
          text: libEls.editor.inputs.body.value,
          notification_services: ns
        }
      };
    }
    libEls.editor.testButton.classList.add("show-sent");
    setTimeout(() => libEls.editor.testButton.classList.remove("show-sent"), 5e3);
    fetchAPI(url, args);
  }
  submit() {
    const reminderType = this.state.reminderType;
    const entryId = this.state.entryId;
    if (reminderType === null)
      throw new Error("Trying to submit reminder editor without having the dialog open");
    libEls.editor.containers.time.classList.remove("error-input-container");
    libEls.editor.containers.weekday.classList.remove("error-input");
    libEls.editor.containers.cron.classList.remove("error-input-container");
    libEls.editor.containers.ns.classList.remove("error-input");
    let url, method, data;
    if (entryId === null) {
      url = `${reminderTypeToUrl(reminderType)}`;
      method = "POST";
    } else {
      url = `${reminderTypeToUrl(reminderType)}/${entryId}`;
      method = "PUT";
    }
    const ns = [...libEls.editor.inputs.ns.selectedOptions].map(
      (option) => parseInt(option.value)
    );
    if (!ns.length) {
      libEls.editor.containers.ns.classList.add("error-input");
      libEls.editor.containers.ns.open = true;
      return;
    }
    if (reminderType === 0 /* REMINDER */) {
      let time, repeatQuantity = null, repeatInterval = null, weekDays2 = null, cronSchedule = null;
      if (libEls.editor.inputs.repetition.value === "cron")
        time = Date.now() / 1e3 + 5 + (/* @__PURE__ */ new Date()).getTimezoneOffset() * 60;
      else
        time = new Date(libEls.editor.inputs.time.value).getTime() / 1e3 + new Date(libEls.editor.inputs.time.value).getTimezoneOffset() * 60;
      switch (libEls.editor.inputs.repetition.value) {
        case "repeated":
          repeatQuantity = libEls.editor.inputs.repeatQuantity.value;
          repeatInterval = libEls.editor.inputs.repeatInterval.valueAsNumber;
          break;
        case "week_days":
          weekDays2 = [];
          libEls.editor.inputs.weekday.forEach((day, index) => {
            if (day.checked)
              weekDays2?.push(index);
          });
          if (weekDays2.length === 0) {
            libEls.editor.containers.weekday.classList.add("error-input");
            return;
          }
          break;
        case "cron":
          cronSchedule = libEls.editor.inputs.cron.value;
          break;
        default:
          break;
      }
      data = {
        enabled: libEls.editor.inputs.enabled.checked,
        color: libEls.editor.inputs.color.value,
        time,
        repeat_quantity: repeatQuantity,
        repeat_interval: repeatInterval,
        weekdays: weekDays2,
        cron_schedule: cronSchedule,
        notification_services: ns,
        title: libEls.editor.inputs.title.value,
        text: libEls.editor.inputs.body.value
      };
    } else {
      data = {
        color: libEls.editor.inputs.color.value,
        notification_services: ns,
        title: libEls.editor.inputs.title.value,
        text: libEls.editor.inputs.body.value
      };
    }
    fetchAPI(url, {
      method,
      body: data
    }).then(() => {
      loadLibrary(reminderType);
      if (reminderType === 2 /* TEMPLATE */)
        this.prepareTemplates();
      this.hide();
    }).catch((json) => {
      if (json.error === "InvalidTime")
        libEls.editor.containers.time.classList.add("error-input-container");
      else if (json.error === "InvalidKeyValue" && json.result.key === "cron_schedule")
        libEls.editor.containers.cron.classList.add("error-input-container");
      else
        console.log(json);
    });
  }
  async remove() {
    const reminderType = this.state.reminderType;
    const entryId = this.state.entryId;
    if (reminderType === null || entryId === null)
      throw new Error("Trying to delete reminder editor entry without having the dialog open");
    await fetchAPI(`${reminderTypeToUrl(reminderType)}/${entryId}`, {
      method: "DELETE"
    });
    loadLibrary(reminderType);
    if (reminderType === 2 /* TEMPLATE */)
      this.prepareTemplates();
    this.hide();
  }
};
var windowInstances = {
  editor: new EditorWindow()
};

// ts/reminders/reminders.ts
Object.values(libEls.tabSelectors).forEach(
  (b) => b.onclick = () => {
    const oldTab = activeTab;
    showTab(b.id);
    if (libEls.search.input.value) {
      libEls.search.input.value = "";
      loadLibrary(oldTab);
    } else
      evaluateSizing();
    libEls.search.sort.value = getSorting(activeTab);
  }
);
libEls.search.form.onsubmit = (e) => {
  e.preventDefault();
  if (autoSearchTimer !== null)
    clearTimeout(autoSearchTimer);
  loadLibrary(activeTab);
};
var autoSearchTimer = null;
libEls.search.input.onkeydown = () => {
  if (autoSearchTimer !== null)
    clearTimeout(autoSearchTimer);
  autoSearchTimer = setTimeout(
    () => loadLibrary(activeTab),
    Constants.autoSearchTimeout
  );
};
document.body.addEventListener("keydown", (e) => {
  if (e.key === "/" && document.activeElement !== libEls.search.input && !windowInstances.editor.isShown) {
    e.preventDefault();
    libEls.search.input.focus();
  }
});
libEls.search.clear.onclick = () => {
  libEls.search.input.value = "";
  loadLibrary(activeTab);
};
libEls.search.sort.value = getSorting(activeTab);
libEls.search.sort.onchange = () => {
  setSorting(activeTab, libEls.search.sort.value);
  loadLibrary(activeTab);
};
libEls.search.wide.onclick = () => toggleWideView();
function bindAddButtons() {
  Object.entries(libEls.addButtons).forEach(([type, button]) => {
    if (nsExists)
      button.onclick = () => windowInstances.editor.show({
        reminderType: parseInt(type),
        entryId: null
      });
    else {
      button.onclick = () => window.location.href = "/notificationservices";
      button.classList.add("error");
    }
  });
}
libEls.editor.cancel.onclick = () => windowInstances.editor.hide();
libEls.editor.dialog.onclick = (e) => {
  if (e.target === e.currentTarget) {
    e.stopPropagation();
    windowInstances.editor.hide();
  }
};
libEls.editor.form.onsubmit = (e) => {
  e.preventDefault();
  windowInstances.editor.submit();
};
libEls.editor.inputs.template.onchange = () => {
  windowInstances.editor.applyTemplate(
    parseInt(libEls.editor.inputs.template.value)
  );
};
libEls.editor.inputs.repetition.onchange = () => windowInstances.editor.updateInputVisibility(false);
libEls.editor.deleteButton.onclick = () => windowInstances.editor.remove();
libEls.editor.testButton.onclick = () => windowInstances.editor.test();
{
  const storage = getLocalStorage();
  if (storage.wide_library_view)
    toggleWideView();
}
setInterval(
  () => loadLibrary(0 /* REMINDER */),
  Constants.libraryRefreshInterval
);
OnLoadRunner.add(
  () => {
    loadLibrary(0 /* REMINDER */);
    loadLibrary(1 /* STATIC_REMINDER */);
    return loadLibrary(2 /* TEMPLATE */);
  },
  () => windowInstances.editor.prepare(),
  bindAddButtons
);
OnLoadRunner.runOnLoad();
