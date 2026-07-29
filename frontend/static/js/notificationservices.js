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
var nsTestFailReasonMap = {
  connection_error: "There was a connection error",
  syntax_invalid_url: "The syntax of the URL is invalid",
  rejected_url: "Value(s) rejected by service"
};
function hide({ to_hide = [], to_show = [] } = {}) {
  to_hide.forEach((el) => el.classList.add("hidden"));
  if (to_show !== null && to_show !== void 0)
    to_show.forEach((el) => el.classList.remove("hidden"));
}
function createIcon(iconId) {
  const svg = document.createElementNS(Constants.svgNamespace, "svg");
  const use = document.createElementNS(Constants.svgNamespace, "use");
  use.setAttribute("href", `#${iconId}`);
  svg.appendChild(use);
  return svg;
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
async function fetchAPI(endpoint, options2 = {}) {
  const finalOptions = {
    ...defaultAPIRequestOptions,
    ...options2
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

// ts/notificationservices/elements.ts
var nsEls = {
  servicesList: document.getElementById("services-list"),
  options: {
    open: document.getElementById("open-service-options"),
    dialog: document.getElementById("ns-options-dialog"),
    close: document.getElementById("close-ns-options"),
    list: document.getElementById("options-list"),
    search: document.getElementById("ns-search-input")
  },
  add: {
    dialog: document.getElementById("add-ns-dialog"),
    back: document.getElementById("close-add-ns"),
    test: document.getElementById("test-service"),
    submit: document.getElementById("submit-add-ns"),
    typeTitle: document.getElementById("add-type"),
    form: document.getElementById("builder-form")
  },
  edit: {
    dialog: document.getElementById("edit-ns-dialog"),
    form: document.getElementById("edit-ns-form"),
    close: document.getElementById("close-edit-ns"),
    urlContainer: document.querySelector("#edit-ns-form .checked-input-container:has(#edit-url)"),
    inputs: {
      title: document.getElementById("edit-title"),
      url: document.getElementById("edit-url")
    },
    error: document.getElementById("edit-invalid-url")
  },
  delete: {
    dialog: document.getElementById("delete-ns-dialog"),
    close: document.getElementById("close-delete-ns"),
    confirm: document.getElementById("confirm-delete-ns"),
    error: document.getElementById("delete-ns-error")
  }
};

// ts/notificationservices/urlbuilder.ts
function createTitleInput() {
  const title = document.createElement("input");
  title.classList.add("input-style");
  title.type = "text";
  title.id = "service-title";
  title.placeholder = "Service Title";
  title.required = true;
  return title;
}
function createStringInput(param) {
  const input = document.createElement("input");
  input.classList.add("input-style");
  input.type = "text";
  input.required = param.required;
  input.placeholder = `${param.name}${!param.required ? " (Optional)" : ""}`;
  return input;
}
function createIntInput(param) {
  const input = document.createElement("input");
  input.classList.add("input-style");
  input.type = "number";
  input.required = param.required;
  input.placeholder = `${param.name}${!param.required ? " (Optional)" : ""}`;
  if (param.min !== null)
    input.min = param.min.toString();
  if (param.max !== null)
    input.max = param.max.toString();
  return input;
}
function createFloatInput(param) {
  const input = document.createElement("input");
  input.classList.add("input-style");
  input.type = "number";
  input.step = "0.1";
  input.required = param.required;
  input.placeholder = `${param.name}${!param.required ? " (Optional)" : ""}`;
  if (param.min !== null)
    input.min = param.min.toString();
  if (param.max !== null)
    input.max = param.max.toString();
  return input;
}
function createBoolInput(param) {
  const input = document.createElement("select");
  input.classList.add("input-style");
  input.required = param.required;
  const yesEntry = document.createElement("option");
  yesEntry.value = "true";
  yesEntry.innerText = "Yes";
  if (param.default === true)
    yesEntry.selected = true;
  input.appendChild(yesEntry);
  const noEntry = document.createElement("option");
  noEntry.value = "false";
  noEntry.innerText = "No";
  if (param.default === false)
    noEntry.selected = true;
  input.appendChild(noEntry);
  return input;
}
function createChoiceInput(param) {
  const choice = document.createElement("select");
  choice.classList.add("input-style");
  choice.required = param.required;
  param.options.forEach((option) => {
    const entry = document.createElement("option");
    entry.value = option;
    entry.innerText = option;
    if (option === param.default)
      entry.selected = true;
    choice.appendChild(entry);
  });
  return choice;
}
function createEntriesList(param) {
  const list = document.createElement("div");
  list.classList.add("entries-list");
  const desc = document.createElement("p");
  desc.innerText = param.name;
  list.appendChild(desc);
  const entries = document.createElement("div");
  entries.classList.add("input-entries");
  list.appendChild(entries);
  const addRow = document.createElement("div");
  addRow.classList.add("add-row", "hidden");
  const addInput = document.createElement("input");
  addInput.classList.add("input-style");
  addInput.type = "text";
  addInput.onkeydown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      e.stopImmediatePropagation();
      addEntry(entries, addInput.value, addRow);
    }
  };
  addRow.appendChild(addInput);
  const addRowButton = document.createElement("button");
  addRowButton.classList.add("input-style");
  addRowButton.type = "button";
  addRowButton.innerText = "Add";
  addRowButton.onclick = () => addEntry(entries, addInput.value, addRow);
  addRow.appendChild(addRowButton);
  list.appendChild(addRow);
  const toggleAddButton = document.createElement("button");
  toggleAddButton.classList.add("input-style");
  toggleAddButton.type = "button";
  toggleAddButton.appendChild(createIcon("icon-plus"));
  toggleAddButton.onclick = () => toggleAddRow(addRow);
  list.appendChild(toggleAddButton);
  return list;
}
function toggleAddRow(row) {
  if (row.classList.contains("hidden")) {
    const addInput = row.querySelector("input");
    addInput.value = "";
    hide({ to_show: [row] });
    addInput.focus();
  } else {
    hide({ to_hide: [row] });
  }
}
function addEntry(entriesList, value, addRow) {
  const entry = document.createElement("div");
  entry.innerText = value;
  entriesList.appendChild(entry);
  toggleAddRow(addRow);
}
function createAdvancedToggle() {
  const button = document.createElement("button");
  button.classList.add("input-style");
  button.type = "button";
  button.innerText = "Show Advanced Settings";
  button.onclick = () => {
    nsEls.add.form.querySelectorAll('[data-is_arg="true"]').forEach(
      (el) => el.classList.toggle("hidden")
    );
    button.innerText = button.innerText === "Show Advanced Settings" ? "Hide Advanced Settings" : "Show Advanced Settings";
  };
  return button;
}
function insertParameter(param, index, isArg) {
  let result = null;
  switch (param.type) {
    case "string":
      result = createStringInput(param);
      break;
    case "int":
      result = createIntInput(param);
      break;
    case "float":
      result = createFloatInput(param);
      break;
    case "bool":
      const boolDesc = document.createElement("p");
      boolDesc.innerText = `${param.name}${!param.required ? " (Optional)" : ""}`;
      boolDesc.dataset.is_arg = isArg.toString();
      nsEls.add.form.appendChild(boolDesc);
      result = createBoolInput(param);
      break;
    case "choice":
      const choiceDesc = document.createElement("p");
      choiceDesc.innerText = `${param.name}${!param.required ? " (Optional)" : ""}`;
      choiceDesc.dataset.is_arg = isArg.toString();
      nsEls.add.form.appendChild(choiceDesc);
      result = createChoiceInput(param);
      break;
    case "list":
      result = document.createElement("div");
      const listDesc = document.createElement("p");
      listDesc.innerText = `${param.name}${!param.required ? " (Optional)" : ""}`;
      result.appendChild(listDesc);
      if (param.content.length === 0)
        result.appendChild(createEntriesList(param));
      else
        param.content.forEach((c, i) => {
          const list = createEntriesList(c);
          list.dataset.content_index = i.toString();
          result.appendChild(list);
        });
      break;
    default:
      return;
  }
  result.dataset.index = index.toString();
  result.dataset.is_arg = isArg.toString();
  nsEls.add.form.appendChild(result);
}
function createURLBuilder(data) {
  nsEls.add.form.innerHTML = "";
  const title = document.createElement("h3");
  title.innerText = data.name;
  nsEls.add.form.appendChild(title);
  if (data.doc_url) {
    const docs = document.createElement("a");
    docs.href = data.doc_url;
    docs.target = "_blank";
    docs.innerText = "Documentation";
    nsEls.add.form.appendChild(docs);
  }
  nsEls.add.form.appendChild(createTitleInput());
  data.details.tokens.forEach((param, idx) => insertParameter(param, idx, false));
  if (data.details.args.length > 0) {
    nsEls.add.form.appendChild(createAdvancedToggle());
    data.details.args.forEach((param, idx) => insertParameter(param, idx, true));
    hide({ to_hide: [
      ...nsEls.add.form.querySelectorAll("[data-is_arg='true']")
    ] });
  }
}
function buildURL(data) {
  console.debug(data);
  const tokens = {};
  const args = {};
  nsEls.add.form.querySelectorAll(":where(input, select, div)[data-index]").forEach((el) => {
    const index = parseInt(el.dataset.index || "");
    if (el.dataset.is_arg === "false")
      tokens[index] = el;
    else
      args[index] = el;
  });
  const values = {};
  Object.entries(tokens).forEach(([idx, el]) => {
    const inputData = data.details.tokens[parseInt(idx)];
    if (inputData.type !== "list") {
      let value = `${inputData.prefix || ""}${el.value}`;
      if (value)
        values[inputData.map_to] = value;
    } else {
      let value = [...el.querySelectorAll(".entries-list")].map((l) => {
        let prefix = null;
        if (l.dataset.content_index)
          prefix = inputData.content[parseInt(l.dataset.content_index)].prefix;
        return [...l.querySelectorAll(".input-entries > div")].map((e) => `${prefix || ""}${e.innerText}`);
      }).flat().join(inputData.delim);
      if (value)
        values[inputData.map_to] = value;
    }
  });
  const inputKeys = Object.keys(values).sort().join();
  const matchingTemplates = data.details.templates.filter(
    (template2) => inputKeys === template2.replaceAll("}", "{").split("{").filter((e, i) => i % 2).sort().join()
  );
  if (!matchingTemplates.length)
    return null;
  let template = matchingTemplates[0];
  for (const [key, value] of Object.entries(values))
    template = template.replace(`{${key}}`, value);
  const inputArgs = new URLSearchParams();
  Object.entries(args).forEach(([idx, el]) => {
    const inputData = data.details.args[parseInt(idx)];
    if (inputData.type !== "list") {
      const elValue = el.value;
      if (elValue && ([void 0, null, ""].includes(inputData.default) || elValue !== inputData.default.toString()))
        inputArgs.append(
          inputData.map_to,
          `${inputData.prefix || ""}${elValue}`
        );
    } else {
      let value = [...el.querySelectorAll(".entries-list")].map((l) => {
        let prefix = null;
        if (l.dataset.content_index)
          prefix = inputData.content[parseInt(l.dataset.content_index)].prefix;
        return [...l.querySelectorAll(".input-entries > div")].map((e) => `${prefix || ""}${e.innerText}`);
      }).flat().join(inputData.delim);
      if (value)
        inputArgs.append(inputData.map_to, value);
    }
  });
  if (inputArgs.size > 0)
    template += (template.includes("?") ? "&" : "?") + inputArgs.toString();
  template.replace(" ", "%20");
  console.debug(matchingTemplates);
  console.debug(template);
  return template;
}
function validateInputRegexes(data) {
  const faultyInputs = [];
  nsEls.add.form.querySelectorAll(":where(input, select)[data-index]").forEach((el) => {
    el.classList.remove("error-input");
    const index = parseInt(el.dataset.index || "");
    let tokenData;
    if (el.dataset.is_arg === "false")
      tokenData = data.details.tokens[index];
    else
      tokenData = data.details.args[index];
    const regex = tokenData.regex;
    if (!regex)
      return;
    if (!tokenData.required && el.value === "")
      return;
    if (new RegExp(regex[0], regex[1]).test(el.value))
      return;
    faultyInputs.push(el);
  });
  faultyInputs.forEach((el) => el.classList.add("error-input"));
  return faultyInputs.length === 0;
}

// ts/notificationservices/actions.ts
var services = {};
var options = [];
var NSOptionsWindow = class {
  dialog = nsEls.options.dialog;
  isShown = false;
  autoSearchTimer = null;
  prepare() {
    fetchAPI("/notificationservices/available").then((json) => {
      json.result.forEach((result, index) => {
        options.push(result);
        const entry = document.createElement("button");
        entry.innerText = result.name;
        entry.onclick = () => windowInstances.add.show({ index });
        entry.style.viewTransitionName = `ns-${index}`;
        nsEls.options.list.appendChild(entry);
      });
    });
  }
  show() {
    this.isShown = true;
    nsEls.options.search.value = "";
    this.searchOptions();
    this.dialog.showModal();
  }
  hide() {
    this.isShown = false;
    this.dialog.close();
  }
  submit() {
  }
  searchOptions() {
    if (this.autoSearchTimer !== null)
      clearTimeout(this.autoSearchTimer);
    const f = () => {
      const query = nsEls.options.search.value.toLowerCase().replace("-", "").replace("_", "").replace(" ", "");
      if (query === "")
        hide({ to_show: [...nsEls.options.list.querySelectorAll("button")] });
      else
        nsEls.options.list.querySelectorAll("button").forEach(
          (e) => e.classList.toggle(
            "hidden",
            !e.innerText.toLowerCase().replace("-", "").replace("_", "").replace(" ", "").includes(query)
          )
        );
    };
    f();
  }
};
var AddNSWindow = class {
  dialog = nsEls.add.dialog;
  serviceIndex = null;
  prepare() {
  }
  show(args) {
    this.serviceIndex = args.index;
    nsEls.add.typeTitle.innerText = options[args.index].name;
    createURLBuilder(options[args.index]);
    nsEls.add.test.classList.remove("error-input");
    nsEls.add.test.title = "";
    nsEls.add.submit.classList.remove("error-input");
    nsEls.add.submit.title = "";
    windowInstances.options.hide();
    this.dialog.showModal();
  }
  hide() {
    this.dialog.close();
    windowInstances.options.show();
  }
  test() {
    const testButton = nsEls.add.test;
    if (this.serviceIndex === null)
      throw new Error("Testing service before builder is opened");
    if (!validateInputRegexes(options[this.serviceIndex]))
      return;
    const data = {
      url: buildURL(options[this.serviceIndex])
    };
    if (!data.url) {
      testButton.classList.add("error-input");
      testButton.title = "Required field missing";
      return;
    }
    fetchAPI("/notificationservices/test", {
      method: "POST",
      body: data
    }).then((json) => {
      if (json.result.success) {
        testButton.classList.remove("error-input");
        testButton.title = "";
        testButton.classList.add("show-sent");
      } else {
        testButton.classList.add("error-input");
        testButton.title = nsTestFailReasonMap[json.result.description];
      }
    });
  }
  submit() {
    const addButton = nsEls.add.submit;
    if (this.serviceIndex === null)
      throw new Error("Adding service before builder is opened");
    if (!validateInputRegexes(options[this.serviceIndex]))
      return;
    const titleEl = document.getElementById("service-title");
    if (!titleEl)
      throw new Error("Service Title element not found");
    const data = {
      title: titleEl.value,
      url: buildURL(options[this.serviceIndex])
    };
    if (!data.url) {
      addButton.classList.add("error-input");
      addButton.title = "Required field missing";
      return;
    }
    fetchAPI("/notificationservices", {
      method: "POST",
      body: data
    }).then(() => {
      addButton.classList.remove("error-input");
      addButton.title = "";
      loadServices();
      this.hide();
      windowInstances.options.hide();
    }).catch((json) => {
      if (json.error === "URLInvalid") {
        addButton.classList.add("error-input");
        addButton.title = nsTestFailReasonMap[json.result.reason];
      } else
        console.log(json);
    });
  }
};
var EditNSWindow = class {
  serviceId = null;
  dialog = nsEls.edit.dialog;
  prepare() {
  }
  show(args) {
    this.serviceId = args.id;
    nsEls.edit.inputs.title.value = services[args.id].title;
    nsEls.edit.inputs.url.value = services[args.id].url;
    nsEls.edit.urlContainer.classList.remove("error-input-container");
    this.dialog.showModal();
  }
  hide() {
    this.dialog.close();
  }
  submit() {
    nsEls.edit.urlContainer.classList.remove("error-input-container");
    const data = {
      title: nsEls.edit.inputs.title.value,
      url: nsEls.edit.inputs.url.value
    };
    fetchAPI(`/notificationservices/${this.serviceId}`, {
      method: "PUT",
      body: data
    }).then(() => {
      loadServices();
      this.hide();
    }).catch((json) => {
      if (json.error === "URLInvalid" || json.error === "InvalidKeyValue") {
        nsEls.edit.error.innerText = nsTestFailReasonMap[json.result.reason] || "Syntax of URL invalid";
        hide({ to_show: [nsEls.edit.error] });
        nsEls.edit.urlContainer.classList.add("error-input-container");
      } else
        console.log(json);
    });
  }
};
var DeleteNSWindow = class {
  serviceId = null;
  deleteRemindersUsing = false;
  dialog = nsEls.delete.dialog;
  prepare() {
  }
  show(args) {
    this.serviceId = args.id;
    nsEls.delete.confirm.innerText = "Delete";
    hide({ to_hide: [nsEls.delete.error] });
    this.dialog.showModal();
  }
  hide() {
    this.deleteRemindersUsing = false;
    this.dialog.close();
  }
  submit() {
    fetchAPI(`/notificationservices/${this.serviceId}`, {
      method: "DELETE",
      params: { delete_reminders_using: this.deleteRemindersUsing }
    }).then(() => {
      hide({ to_hide: [nsEls.delete.error] });
      loadServices();
      this.hide();
    }).catch((json) => {
      if (json.error === "NotificationServiceInUse") {
        nsEls.delete.error.innerText = `The notification service is still in use by a ${json.result.reminder_type.toLowerCase()}. Do you want to delete all ${json.result.reminder_type.toLowerCase()}s that are using the notification service?`;
        hide({ to_show: [nsEls.delete.error] });
        nsEls.delete.confirm.innerText = "Delete Anyway";
        this.deleteRemindersUsing = true;
      } else
        console.log(json);
    });
  }
};
var windowInstances = {
  options: new NSOptionsWindow(),
  add: new AddNSWindow(),
  edit: new EditNSWindow(),
  delete: new DeleteNSWindow()
};
async function loadServices() {
  const json = await fetchAPI("/notificationservices");
  nsEls.servicesList.querySelectorAll("tr:not(.empty-row)").forEach(
    (e) => e.remove()
  );
  json.result.forEach((service) => {
    services[service.id] = service;
    const entry = document.createElement("tr");
    entry.dataset.id = service.id.toString();
    const title = document.createElement("td");
    title.classList.add("title-column");
    title.innerText = service.title;
    entry.appendChild(title);
    const url = document.createElement("td");
    url.classList.add("url-column");
    url.innerText = service.url;
    entry.appendChild(url);
    const actions = document.createElement("td");
    actions.classList.add("action-column");
    entry.appendChild(actions);
    const editEntry = document.createElement("button");
    editEntry.title = "Edit service";
    editEntry.appendChild(createIcon("icon-edit"));
    editEntry.onclick = () => windowInstances.edit.show({ id: service.id });
    actions.appendChild(editEntry);
    const deleteEntry = document.createElement("button");
    deleteEntry.title = "Delete service";
    deleteEntry.appendChild(createIcon("icon-delete"));
    deleteEntry.onclick = () => windowInstances.delete.show({ id: service.id });
    actions.appendChild(deleteEntry);
    nsEls.servicesList.appendChild(entry);
  });
}

// ts/notificationservices/notificationservices.ts
nsEls.options.open.onclick = () => windowInstances.options.show();
nsEls.options.dialog.onclick = (e) => {
  if (e.target === e.currentTarget) {
    e.stopPropagation();
    windowInstances.options.hide();
  }
};
nsEls.options.close.onclick = () => windowInstances.options.hide();
nsEls.options.search.oninput = () => {
  if (windowInstances.options.autoSearchTimer !== null)
    clearTimeout(windowInstances.options.autoSearchTimer);
  windowInstances.options.autoSearchTimer = setTimeout(
    windowInstances.options.searchOptions,
    Constants.autoSearchTimeout
  );
};
document.body.addEventListener("keydown", (e) => {
  if (e.key === "/" && windowInstances.options.isShown && document.activeElement !== nsEls.options.search) {
    e.preventDefault();
    nsEls.options.search.focus();
  }
});
nsEls.add.dialog.onclick = (e) => {
  if (e.target === e.currentTarget) {
    e.stopPropagation();
    windowInstances.add.hide();
  }
};
nsEls.add.back.onclick = () => windowInstances.add.hide();
nsEls.add.test.onclick = () => windowInstances.add.test();
nsEls.add.form.onsubmit = (e) => {
  e.preventDefault();
  windowInstances.add.submit();
};
nsEls.edit.dialog.onclick = (e) => {
  if (e.target === e.currentTarget) {
    e.stopPropagation();
    windowInstances.edit.hide();
  }
};
nsEls.edit.close.onclick = () => windowInstances.edit.hide();
nsEls.edit.form.onsubmit = (e) => {
  e.preventDefault();
  windowInstances.edit.submit();
};
nsEls.delete.dialog.onclick = (e) => {
  if (e.target === e.currentTarget) {
    e.stopPropagation();
    windowInstances.delete.hide();
  }
};
nsEls.delete.close.onclick = () => windowInstances.delete.hide();
nsEls.delete.confirm.onclick = () => windowInstances.delete.submit();
OnLoadRunner.add(loadServices, windowInstances.options.prepare);
OnLoadRunner.runOnLoad();
