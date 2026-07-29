// ts/general.ts
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
async function deleteAccount() {
  await fetchAPI("/user", { method: "DELETE" });
  const storage = getLocalStorage();
  storage.api_key = null;
  setLocalStorage(storage);
  window.location.href = `${urlPrefix}`;
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

// ts/settings/elements.ts
var settingsEls = {
  settings: {
    showClock: document.getElementById("clock-input"),
    locale: document.getElementById("locale-input"),
    defaultService: document.getElementById("default-service-input")
  },
  editAcc: {
    open: document.getElementById("open-edit-account"),
    dialog: document.getElementById("edit-account-dialog"),
    form: document.getElementById("edit-account-form"),
    close: document.getElementById("close-edit-account"),
    usernameContainer: document.querySelector("#edit-account-form .checked-input-container:has(input[type='text'])"),
    inputs: {
      username: document.getElementById("edit-username"),
      password: document.getElementById("edit-password")
    },
    errors: {
      usernameInvalid: document.getElementById("invalid-username-error"),
      usernameTaken: document.getElementById("username-taken-error")
    }
  },
  delAcc: {
    open: document.getElementById("open-delete-account"),
    dialog: document.getElementById("delete-account-dialog"),
    close: document.getElementById("close-delete-account"),
    confirm: document.getElementById("confirm-delete-account")
  }
};

// ts/settings/actions.ts
async function loadSettings() {
  const values = getLocalStorage();
  settingsEls.settings.showClock.value = values.show_clock;
  settingsEls.settings.locale.value = values.locale;
  settingsEls.settings.defaultService.innerHTML = "";
  const json = await fetchAPI("/notificationservices");
  json.result.forEach((service) => {
    const entry = document.createElement("option");
    entry.value = service.id.toString();
    entry.innerText = service.title;
    if (values.default_service === service.id)
      entry.selected = true;
    settingsEls.settings.defaultService.appendChild(entry);
  });
  if (!json.result.map((s) => s.id).includes(values.default_service)) {
    values.default_service = json.result[0]?.id || null;
    setLocalStorage(values);
  }
}
function updateClockSetting() {
  const storage = getLocalStorage();
  storage.show_clock = settingsEls.settings.showClock.value;
  setLocalStorage(storage);
  setupClock();
}
function updateLocale() {
  const storage = getLocalStorage();
  storage.locale = settingsEls.settings.locale.value;
  setLocalStorage(storage);
  setupClock();
}
function updateDefaultService() {
  const storage = getLocalStorage();
  storage.default_service = parseInt(settingsEls.settings.defaultService.value);
  setLocalStorage(storage);
}
var EditAccountWindow = class {
  dialog = settingsEls.editAcc.dialog;
  prepare() {
  }
  show(args = {}) {
    settingsEls.editAcc.usernameContainer.classList.remove("error-input-container");
    hide({ to_hide: [
      settingsEls.editAcc.errors.usernameInvalid,
      settingsEls.editAcc.errors.usernameTaken
    ] });
    settingsEls.editAcc.inputs.username.value = "";
    settingsEls.editAcc.inputs.password.value = "";
    settingsEls.editAcc.dialog.showModal();
  }
  hide() {
    settingsEls.editAcc.dialog.close();
  }
  submit() {
    settingsEls.editAcc.usernameContainer.classList.remove("error-input-container");
    hide({ to_hide: [
      settingsEls.editAcc.errors.usernameInvalid,
      settingsEls.editAcc.errors.usernameTaken
    ] });
    const data = {};
    if (settingsEls.editAcc.inputs.username.value !== "")
      data.new_username = settingsEls.editAcc.inputs.username.value;
    if (settingsEls.editAcc.inputs.password.value !== "")
      data.new_password = settingsEls.editAcc.inputs.password.value;
    if (!Object.keys(data).length) {
      this.hide();
      return;
    }
    fetchAPI("/user", {
      method: "PUT",
      body: data
    }).then(() => this.hide()).catch((json) => {
      if (json.error === "UsernameInvalid") {
        settingsEls.editAcc.errors.usernameInvalid.innerText = json.result.reason;
        hide({ to_show: [settingsEls.editAcc.errors.usernameInvalid] });
        settingsEls.editAcc.usernameContainer.classList.add("error-input-container");
      } else if (json.error === "UsernameTaken") {
        hide({ to_show: [settingsEls.editAcc.errors.usernameTaken] });
        settingsEls.editAcc.usernameContainer.classList.add("error-input-container");
      } else
        console.log(json);
    });
  }
};

// ts/settings/settings.ts
settingsEls.settings.showClock.onchange = () => updateClockSetting();
settingsEls.settings.locale.onchange = () => updateLocale();
settingsEls.settings.defaultService.onchange = () => updateDefaultService();
var editWindow = new EditAccountWindow();
settingsEls.editAcc.open.onclick = () => editWindow.show();
settingsEls.editAcc.dialog.onclick = (e) => {
  if (e.target === e.currentTarget) {
    e.stopPropagation();
    editWindow.hide();
  }
};
settingsEls.editAcc.close.onclick = () => editWindow.hide();
settingsEls.editAcc.form.onsubmit = (e) => {
  e.preventDefault();
  editWindow.submit();
};
settingsEls.delAcc.open.onclick = () => settingsEls.delAcc.dialog.showModal();
settingsEls.delAcc.dialog.onclick = (e) => {
  if (e.target === e.currentTarget) {
    e.stopPropagation();
    settingsEls.delAcc.dialog.close();
  }
};
settingsEls.delAcc.close.onclick = () => settingsEls.delAcc.dialog.close();
settingsEls.delAcc.confirm.onclick = () => deleteAccount();
OnLoadRunner.add(loadSettings);
OnLoadRunner.runOnLoad();
