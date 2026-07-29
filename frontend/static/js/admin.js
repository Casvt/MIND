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
var invalidUsernameReasonMap = {
  only_numbers: "A username can't exist of just digits",
  not_allowed: "The username is not allowed",
  invalid_character: "The username contains an invalid character"
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
function downloadLogs() {
  window.location.href = `${urlPrefix}/api/admin/logs?api_key=${apiKey}`;
}
function downloadCurrentDatabase() {
  window.location.href = `${urlPrefix}/api/admin/database?api_key=${apiKey}`;
}
function downloadBackupDatabase(index) {
  window.location.href = `${urlPrefix}/api/admin/database/backups/${index}?api_key=${apiKey}`;
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

// ts/admin/elements.ts
var adminEls = {
  logout: document.getElementById("logout"),
  about: {
    mindVersion: document.getElementById("mind-version"),
    pythonVersion: document.getElementById("python-version"),
    dbVersion: document.getElementById("db-version"),
    dbLocation: document.getElementById("db-location"),
    dataFolder: document.getElementById("data-folder")
  },
  settingsSubmit: document.getElementById("save-settings"),
  changesCount: document.getElementById("changes-count"),
  settingsForm: document.getElementById("settings-form"),
  dbBackupFolderInputContainer: document.querySelector("div.checked-input-container:has(#db-backup-folder)"),
  settings: {
    allowNewAccounts: document.getElementById("allow-new-accounts"),
    loginTime: document.getElementById("login-time"),
    loginTimeReset: document.getElementById("login-time-reset"),
    host: document.getElementById("host"),
    port: document.getElementById("port"),
    urlPrefix: document.getElementById("url-prefix"),
    logLevel: document.getElementById("log-level"),
    dbBackupInterval: document.getElementById("db-backup-interval"),
    dbBackupAmount: document.getElementById("db-backup-amount"),
    dbBackupFolder: document.getElementById("db-backup-folder")
  },
  power: {
    restart: document.getElementById("restart-button"),
    shutdown: document.getElementById("shutdown-button")
  },
  downloadLogs: document.getElementById("download-logs"),
  downloadCurrentDatabase: document.getElementById("download-db"),
  resetSettings: {
    dialog: document.getElementById("reset-settings-dialog"),
    open: document.getElementById("open-reset-settings"),
    cancel: document.getElementById("close-reset-settings"),
    submit: document.getElementById("submit-reset-settings"),
    list: document.getElementById("reset-list"),
    form: document.getElementById("reset-settings-form")
  },
  plugins: {
    dialog: document.getElementById("plugins-dialog"),
    open: document.getElementById("open-plugins"),
    cancel: document.getElementById("close-plugins"),
    add: document.getElementById("add-plugin"),
    addRow: document.getElementById("add-plugin-row"),
    addInput: document.getElementById("plugin-path"),
    form: document.getElementById("add-plugin-form"),
    list: document.getElementById("plugins-list"),
    error: document.getElementById("plugin-not-found")
  },
  userList: document.getElementById("user-list"),
  addUser: {
    dialog: document.getElementById("add-user-dialog"),
    open: document.getElementById("open-add-user"),
    cancel: document.getElementById("close-add-user"),
    form: document.getElementById("add-user-form"),
    inputContainers: {
      username: document.querySelector("#add-user-form .checked-input-container:has(input[type='text'])")
    },
    inputs: {
      username: document.getElementById("add-user-username"),
      password: document.getElementById("add-user-password")
    },
    errors: {
      usernameInvalid: document.getElementById("add-invalid-username"),
      usernameTaken: document.getElementById("add-taken-username")
    }
  },
  editUser: {
    dialog: document.getElementById("edit-user-dialog"),
    username: document.getElementById("edit-target-username"),
    cancel: document.getElementById("close-edit-user"),
    form: document.getElementById("edit-user-form"),
    inputContainers: {
      username: document.querySelector("#edit-user-form .checked-input-container:has(input[type='text'])")
    },
    inputs: {
      username: document.getElementById("edit-user-username"),
      password: document.getElementById("edit-user-password")
    },
    errors: {
      usernameInvalid: document.getElementById("edit-invalid-username"),
      usernameTaken: document.getElementById("edit-taken-username")
    }
  },
  deleteUser: {
    dialog: document.getElementById("delete-user-dialog"),
    username: document.getElementById("delete-target-username"),
    cancel: document.getElementById("close-delete-user"),
    confirm: document.getElementById("confirm-delete-user")
  },
  backupList: document.getElementById("backup-list"),
  downloadDb: document.getElementById("download-db-button"),
  uploadDb: {
    dialog: document.getElementById("upload-db-dialog"),
    open: document.getElementById("open-upload-db"),
    cancel: document.getElementById("close-upload-db"),
    submit: document.getElementById("submit-upload-db"),
    form: document.getElementById("upload-db-form"),
    inputContainers: {
      file: document.querySelector("#upload-db-form .checked-input-container:has(input[type='file'])")
    },
    inputs: {
      file: document.getElementById("database-file"),
      keepHostingSettings: document.getElementById("copy-hosting-upload")
    }
  },
  importDb: {
    dialog: document.getElementById("import-db-dialog"),
    backupName: document.getElementById("db-backup-name"),
    backupCreation: document.getElementById("db-creation-date"),
    cancel: document.getElementById("close-import-db"),
    submit: document.getElementById("submit-import-db"),
    form: document.getElementById("import-db-form"),
    inputs: {
      keepHostingSettings: document.getElementById("copy-hosting-import")
    }
  }
};

// ts/admin/actions.ts
function loadAbout() {
  fetchAPI("/about").then((json) => {
    adminEls.about.mindVersion.innerText = json.result.version;
    adminEls.about.pythonVersion.innerText = json.result.python_version;
    adminEls.about.dbVersion.innerText = json.result.database_version;
    adminEls.about.dbLocation.innerText = json.result.database_location;
    adminEls.about.dataFolder.innerText = json.result.data_folder;
  });
}
function restart() {
  adminEls.power.restart.replaceChildren(createIcon("icon-loading"));
  adminEls.power.restart.classList.add("spinning");
  fetchAPI("/admin/restart", { method: "POST" }).then(() => {
    setTimeout(
      () => window.location.reload(),
      1e3
    );
  });
}
function shutdown() {
  adminEls.power.shutdown.replaceChildren(createIcon("icon-loading"));
  adminEls.power.shutdown.classList.add("spinning");
  fetchAPI("/admin/shutdown", { method: "POST" }).then(() => {
    setTimeout(
      () => window.location.reload(),
      1e3
    );
  });
}
var SettingsChanges = class {
  static changesCount = 0;
  static setChangeCount(count) {
    this.changesCount = count;
    if (count === 1)
      adminEls.changesCount.innerText = `${count} change`;
    else
      adminEls.changesCount.innerText = `${count} changes`;
  }
  static initInputChangeDetection() {
    this.setChangeCount(0);
    Object.values(adminEls.settings).forEach((s) => {
      const settingValue = s.type === "checkbox" ? s.checked : s.value;
      s.dataset.currentValue = encodeURI(settingValue.toString());
      s.classList.remove("changed");
      s.oninput = (e) => {
        const newValue = encodeURI((s.type === "checkbox" ? s.checked : s.value).toString());
        if (newValue !== s.dataset.currentValue && !s.classList.contains("changed")) {
          this.setChangeCount(this.changesCount + 1);
          s.classList.add("changed");
        } else if (newValue === s.dataset.currentValue && s.classList.contains("changed")) {
          this.setChangeCount(this.changesCount - 1);
          s.classList.remove("changed");
        }
      };
    });
  }
};
function loadSettings() {
  fetchAPI("/settings").then((json) => {
    let el = adminEls.settings.allowNewAccounts;
    el.checked = json.result[el.name];
    el = adminEls.settings.loginTime;
    el.value = Math.round(json.result[el.name] / 60).toString();
    el = adminEls.settings.loginTimeReset;
    el.value = json.result[el.name].toString();
    el = adminEls.settings.host;
    el.value = json.result[el.name];
    el = adminEls.settings.port;
    el.value = json.result[el.name];
    el = adminEls.settings.urlPrefix;
    el.value = json.result[el.name];
    el = adminEls.settings.logLevel;
    el.value = json.result[el.name];
    el = adminEls.settings.dbBackupInterval;
    el.value = (json.result[el.name] / 3600).toString();
    el = adminEls.settings.dbBackupAmount;
    el.value = json.result[el.name];
    el = adminEls.settings.dbBackupFolder;
    el.value = json.result[el.name];
    loadPlugins(json.result["apprise_plugin_paths"]);
    SettingsChanges.initInputChangeDetection();
  });
}
function submitSettings() {
  adminEls.dbBackupFolderInputContainer.classList.remove("error-input-container");
  adminEls.settingsSubmit.classList.remove("submit-error");
  if (SettingsChanges.changesCount === 0)
    return;
  const data = {};
  let hostChanged = false, portChanged = false, urlPrefixChanged = false;
  if (adminEls.settings.allowNewAccounts.classList.contains("changed")) {
    const el = adminEls.settings.allowNewAccounts;
    data[el.name] = el.checked;
  }
  if (adminEls.settings.loginTime.classList.contains("changed")) {
    const el = adminEls.settings.loginTime;
    data[el.name] = parseInt(el.value) * 60;
  }
  if (adminEls.settings.loginTimeReset.classList.contains("changed")) {
    const el = adminEls.settings.loginTimeReset;
    data[el.name] = el.value === "true";
  }
  if (adminEls.settings.host.classList.contains("changed")) {
    const el = adminEls.settings.host;
    data[el.name] = el.value;
    hostChanged = true;
  }
  if (adminEls.settings.port.classList.contains("changed")) {
    const el = adminEls.settings.port;
    data[el.name] = parseInt(el.value);
    portChanged = true;
  }
  if (adminEls.settings.urlPrefix.classList.contains("changed")) {
    const el = adminEls.settings.urlPrefix;
    data[el.name] = el.value;
    urlPrefixChanged = true;
  }
  if (adminEls.settings.logLevel.classList.contains("changed")) {
    const el = adminEls.settings.logLevel;
    data[el.name] = parseInt(el.value);
  }
  if (adminEls.settings.dbBackupInterval.classList.contains("changed")) {
    const el = adminEls.settings.dbBackupInterval;
    data[el.name] = parseInt(el.value) * 3600;
  }
  if (adminEls.settings.dbBackupAmount.classList.contains("changed")) {
    const el = adminEls.settings.dbBackupAmount;
    data[el.name] = parseInt(el.value);
  }
  if (adminEls.settings.dbBackupFolder.classList.contains("changed")) {
    const el = adminEls.settings.dbBackupFolder;
    data[el.name] = el.value;
  }
  if (hostChanged || portChanged || urlPrefixChanged) {
    if (!confirm(Constants.restartMessage))
      return;
  }
  fetchAPI("/admin/settings", { method: "PUT", body: data }).then(() => {
    if (hostChanged) {
      setTimeout(
        () => window.location.reload(),
        1e3
      );
    } else if (portChanged || urlPrefixChanged) {
      const newUrl = new URL(window.location.href);
      if (portChanged)
        newUrl.port = adminEls.settings.port.value;
      if (urlPrefixChanged)
        newUrl.pathname = adminEls.settings.urlPrefix.value + newUrl.pathname.slice(
          adminEls.settings.urlPrefix.dataset.currentValue?.length || 0
        );
      setTimeout(
        () => window.location.href = newUrl.toString(),
        1e3
      );
    }
    SettingsChanges.initInputChangeDetection();
  }).catch((json) => {
    if (json.error === "InvalidKeyValue" && json.result.key === adminEls.settings.dbBackupFolder.name) {
      adminEls.dbBackupFolderInputContainer.classList.add("error-input-container");
      adminEls.settingsSubmit.classList.add("submit-error");
    }
  });
}
var ResetWindow = class {
  dialog = adminEls.resetSettings.dialog;
  prepare() {
    Object.values(adminEls.settings).forEach((el, idx) => {
      let parent = el.parentElement;
      if (parent.nodeName === "DIV")
        parent = parent.parentElement;
      parent = parent.parentElement;
      const title = parent.firstElementChild.firstElementChild.innerText;
      const tr = document.createElement("tr");
      const checkboxContainer = document.createElement("td");
      const checkbox = document.createElement("input");
      checkbox.id = `reset-${idx}`;
      checkbox.type = "checkbox";
      checkbox.dataset.setting = el.name;
      checkboxContainer.appendChild(checkbox);
      const titleContainer = document.createElement("td");
      const titleLabel = document.createElement("label");
      titleLabel.setAttribute("for", `reset-${idx}`);
      titleLabel.innerText = title;
      titleContainer.appendChild(titleLabel);
      tr.appendChild(checkboxContainer);
      tr.appendChild(titleContainer);
      adminEls.resetSettings.list.appendChild(tr);
    });
  }
  show(args = {}) {
    adminEls.resetSettings.list.querySelectorAll("input").forEach(
      (el) => el.checked = false
    );
    this.dialog.showModal();
  }
  hide() {
    this.dialog.close();
  }
  submit() {
    const resetSettings = [...adminEls.resetSettings.list.querySelectorAll("input")].filter((i) => i.checked).map((i) => i.dataset.setting);
    if (!resetSettings.length)
      return;
    adminEls.resetSettings.submit.replaceChildren(createIcon("icon-loading"));
    adminEls.resetSettings.submit.classList.add("spinning");
    const hostChanged = resetSettings.includes(
      adminEls.settings.host.name
    ), portChanged = resetSettings.includes(
      adminEls.settings.port.name
    ), urlPrefixChanged = resetSettings.includes(
      adminEls.settings.urlPrefix.name
    );
    if (hostChanged || portChanged || urlPrefixChanged) {
      if (!confirm(Constants.restartMessage)) {
        adminEls.resetSettings.submit.innerText = "Reset";
        adminEls.resetSettings.submit.classList.remove("spinning");
        return;
      }
    }
    fetchAPI("/admin/settings", {
      method: "DELETE",
      body: { setting_keys: resetSettings }
    }).then((_) => {
      if (portChanged || urlPrefixChanged) {
        const newUrl = new URL(window.location.href);
        if (portChanged)
          newUrl.port = 8080 .toString();
        if (urlPrefixChanged)
          newUrl.pathname = "/";
        setTimeout(
          () => window.location.href = newUrl.toString(),
          1e3
        );
      } else {
        setTimeout(
          () => window.location.reload(),
          1e3
        );
      }
    });
  }
};
var plugins = [];
function loadPlugins(plugins2) {
  adminEls.plugins.list.innerHTML = "";
  plugins2.forEach((plugin) => {
    const tr = document.createElement("tr");
    const path = document.createElement("td");
    path.innerText = plugin;
    tr.appendChild(path);
    const action = document.createElement("td");
    const deletePlugin = document.createElement("button");
    deletePlugin.appendChild(createIcon("icon-delete"));
    deletePlugin.title = "Remove the plugin path";
    deletePlugin.onclick = (e) => {
      plugins2.shift();
      loadPlugins(plugins2);
      fetchAPI("/admin/settings", { method: "PUT", body: {
        apprise_plugin_paths: plugins2
      } });
    };
    action.appendChild(deletePlugin);
    tr.appendChild(action);
    adminEls.plugins.list.appendChild(tr);
  });
}
var PluginsWindow = class {
  dialog = adminEls.plugins.dialog;
  prepare() {
  }
  show(args = {}) {
    hide({ to_hide: [adminEls.plugins.addRow, adminEls.plugins.error] });
    this.dialog.showModal();
  }
  hide() {
    this.dialog.close();
  }
  submit() {
    hide({ to_hide: [adminEls.plugins.error] });
    plugins.unshift(adminEls.plugins.addInput.value);
    fetchAPI("/admin/settings", { method: "PUT", body: {
      apprise_plugin_paths: plugins
    } }).then((_) => {
      loadPlugins(plugins);
      hide({ to_hide: [adminEls.plugins.addRow] });
    }).catch((json) => {
      if (json.error === "InvalidKeyValue") {
        plugins.shift();
        hide({ to_show: [adminEls.plugins.error] });
      } else
        console.log(json);
    });
  }
};
var users = {};
function loadUsers() {
  adminEls.userList.innerHTML = "";
  fetchAPI("/admin/users").then((json) => {
    json.result.forEach((user) => {
      users[user.id] = { username: user.username, admin: user.admin };
      const entry = document.createElement("tr");
      entry.dataset.id = user.id.toString();
      const username = document.createElement("td");
      username.innerText = user.username;
      entry.appendChild(username);
      const actions = document.createElement("td");
      entry.appendChild(actions);
      const editUser = document.createElement("button");
      editUser.appendChild(createIcon("icon-edit"));
      editUser.title = "Edit the user";
      editUser.onclick = (e) => windowInstances.editUser.show({
        userId: user.id
      });
      actions.appendChild(editUser);
      const deleteUser = document.createElement("button");
      deleteUser.appendChild(createIcon("icon-delete"));
      deleteUser.title = "Delete the user";
      deleteUser.onclick = (e) => windowInstances.deleteUser.show({
        userId: user.id
      });
      actions.appendChild(deleteUser);
      if (user.username === "admin") {
        deleteUser.classList.add("hidden");
      }
      adminEls.userList.appendChild(entry);
    });
  });
}
var AddUserWindow = class {
  dialog = adminEls.addUser.dialog;
  prepare() {
  }
  show(args = {}) {
    adminEls.addUser.inputContainers.username.classList.remove("error-input-container");
    hide({ to_hide: [
      adminEls.addUser.errors.usernameInvalid,
      adminEls.addUser.errors.usernameTaken
    ] });
    adminEls.addUser.inputs.username.value = "";
    adminEls.addUser.inputs.password.value = "";
    this.dialog.showModal();
  }
  hide() {
    this.dialog.close();
  }
  submit() {
    adminEls.addUser.inputContainers.username.classList.remove("error-input-container");
    hide({ to_hide: [
      adminEls.addUser.errors.usernameInvalid,
      adminEls.addUser.errors.usernameTaken
    ] });
    const data = {
      username: adminEls.addUser.inputs.username.value,
      password: adminEls.addUser.inputs.password.value
    };
    fetchAPI("/admin/users", {
      method: "POST",
      body: data
    }).then((_) => {
      loadUsers();
      this.hide();
    }).catch((json) => {
      if (json.error === "UsernameInvalid") {
        adminEls.addUser.errors.usernameInvalid.innerText = invalidUsernameReasonMap[json.result.reason];
        hide({ to_show: [adminEls.addUser.errors.usernameInvalid] });
        adminEls.addUser.inputContainers.username.classList.add("error-input-container");
      } else if (json.error === "UsernameTaken") {
        hide({ to_show: [adminEls.addUser.errors.usernameTaken] });
        adminEls.addUser.inputContainers.username.classList.add("error-input-container");
      } else {
        console.log(json);
      }
    });
  }
};
var EditUserWindow = class {
  state = {
    userId: null
  };
  dialog = adminEls.editUser.dialog;
  prepare() {
  }
  show(args) {
    this.state.userId = args.userId;
    const { username, admin } = users[args.userId];
    adminEls.editUser.username.innerText = username;
    adminEls.editUser.inputContainers.username.classList.remove("error-input-container");
    hide({ to_hide: [
      adminEls.editUser.errors.usernameInvalid,
      adminEls.editUser.errors.usernameTaken
    ] });
    adminEls.editUser.inputs.username.value = "";
    adminEls.editUser.inputs.password.value = "";
    if (admin)
      hide({ to_hide: [adminEls.editUser.inputContainers.username] });
    else
      hide({ to_show: [adminEls.editUser.inputContainers.username] });
    this.dialog.showModal();
  }
  hide() {
    this.dialog.close();
  }
  submit() {
    adminEls.editUser.inputContainers.username.classList.remove("error-input-container");
    hide({ to_hide: [
      adminEls.editUser.errors.usernameInvalid,
      adminEls.editUser.errors.usernameTaken
    ] });
    const data = {}, usernameValue = adminEls.editUser.inputs.username.value, passwordValue = adminEls.editUser.inputs.password.value;
    if (usernameValue)
      data.new_username = usernameValue;
    if (passwordValue)
      data.new_password = passwordValue;
    if (!Object.keys(data).length) {
      this.hide();
      return;
    }
    const userId = this.state.userId;
    if (!userId)
      throw new Error("Trying to submit editing a user without having the dialog open");
    fetchAPI(`/admin/users/${userId}`, {
      method: "PUT",
      body: data
    }).then((_) => {
      loadUsers();
      this.hide();
    }).catch((json) => {
      if (json.error === "UsernameInvalid") {
        adminEls.editUser.errors.usernameInvalid.innerText = invalidUsernameReasonMap[json.result.reason];
        hide({ to_show: [adminEls.editUser.errors.usernameInvalid] });
        adminEls.editUser.inputContainers.username.classList.add("error-input-container");
      } else if (json.error === "UsernameTaken") {
        hide({ to_show: [adminEls.editUser.errors.usernameTaken] });
        adminEls.editUser.inputContainers.username.classList.add("error-input-container");
      } else {
        console.log(json);
      }
    });
  }
};
var DeleteUserWindow = class {
  state = {
    userId: null
  };
  dialog = adminEls.deleteUser.dialog;
  prepare() {
  }
  show(args) {
    this.state.userId = args.userId;
    const username = users[args.userId].username;
    adminEls.deleteUser.username.innerText = username;
    adminEls.deleteUser.dialog.showModal();
  }
  hide() {
    adminEls.deleteUser.dialog.close();
  }
  submit() {
    const userId = this.state.userId;
    if (!userId)
      throw new Error("Trying to submit deleting a user without having the dialog open");
    fetchAPI(`/admin/users/${userId}`, { method: "DELETE" }).then((_) => {
      adminEls.userList.querySelector(`tr[data-id="${userId}"]`)?.remove();
      this.hide();
    });
  }
};
var backups = {};
function loadBackups() {
  adminEls.backupList.innerHTML = "";
  fetchAPI("/admin/database/backups").then((json) => {
    json.result.forEach((backup) => {
      backups[backup.index] = {
        filename: backup.filename,
        creationDate: backup.creation_date
      };
      const entry = document.createElement("tr");
      entry.dataset.index = backup.index.toString();
      const filename = document.createElement("td");
      filename.innerText = backup.filename;
      entry.appendChild(filename);
      const creation = document.createElement("td");
      let formattedDate = new Date(backup.creation_date * 1e3).toLocaleString(getLocalStorage().locale);
      creation.innerText = formattedDate;
      entry.appendChild(creation);
      const actions = document.createElement("td");
      entry.appendChild(actions);
      const downloadBackup = document.createElement("button");
      downloadBackup.appendChild(createIcon("icon-download"));
      downloadBackup.title = "Download database backup";
      downloadBackup.onclick = (e) => downloadBackupDatabase(backup.index);
      actions.appendChild(downloadBackup);
      const importBackup = document.createElement("button");
      importBackup.appendChild(createIcon("icon-upload"));
      importBackup.title = "Import database backup";
      importBackup.onclick = (e) => windowInstances.importDatabase.show({
        backupIndex: backup.index
      });
      actions.appendChild(importBackup);
      adminEls.backupList.appendChild(entry);
    });
  });
}
var UploadDatabaseWindow = class {
  dialog = adminEls.uploadDb.dialog;
  prepare() {
  }
  show(args = {}) {
    adminEls.uploadDb.inputs.file.value = "";
    adminEls.uploadDb.inputContainers.file.classList.remove("error-input-container");
    adminEls.uploadDb.inputs.keepHostingSettings.checked = false;
    this.dialog.showModal();
  }
  hide() {
    this.dialog.close();
  }
  submit() {
    const formData = new FormData();
    if (!adminEls.uploadDb.inputs.file.files)
      return;
    formData.append("file", adminEls.uploadDb.inputs.file.files[0]);
    adminEls.uploadDb.submit.replaceChildren(createIcon("icon-loading"));
    adminEls.uploadDb.submit.classList.add("spinning");
    adminEls.uploadDb.inputContainers.file.classList.remove("error-input-container");
    fetchAPI("/admin/database", {
      method: "POST",
      params: {
        copy_hosting_settings: adminEls.uploadDb.inputs.keepHostingSettings
      },
      body: formData
    }).then((_) => setTimeout(
      () => window.location.reload(),
      1e3
    )).catch((json) => {
      if (json.error === "InvalidDatabaseFile") {
        adminEls.uploadDb.inputs.file.value = "";
        adminEls.uploadDb.submit.innerText = "Import";
        adminEls.uploadDb.submit.classList.remove("spinning");
        adminEls.uploadDb.inputContainers.file.classList.add("error-input-container");
      } else
        console.log(json);
    });
  }
};
var ImportDatabaseWindow = class {
  state = {
    backupIndex: null
  };
  dialog = adminEls.importDb.dialog;
  prepare() {
  }
  show(args) {
    this.state.backupIndex = args.backupIndex;
    const { filename, creationDate } = backups[args.backupIndex];
    adminEls.importDb.backupName.innerText = filename;
    adminEls.importDb.backupCreation.innerText = new Date(creationDate * 1e3).toLocaleString(getLocalStorage().locale);
    adminEls.importDb.inputs.keepHostingSettings.checked = false;
    adminEls.importDb.dialog.showModal();
  }
  hide() {
    this.dialog.close();
  }
  submit() {
    const backupIndex = this.state.backupIndex;
    if (!backupIndex)
      throw new Error("Trying to submit importing a db without having the dialog open");
    adminEls.importDb.submit.replaceChildren(createIcon("icon-loading"));
    adminEls.importDb.submit.classList.add("spinning");
    fetchAPI(`/admin/database/backups/${backupIndex}`, {
      method: "POST",
      params: {
        copy_hosting_settings: adminEls.importDb.inputs.keepHostingSettings.checked
      }
    }).then((_) => setTimeout(
      () => window.location.reload(),
      1e3
    ));
  }
};
var windowInstances = {
  reset: new ResetWindow(),
  plugins: new PluginsWindow(),
  addUser: new AddUserWindow(),
  editUser: new EditUserWindow(),
  deleteUser: new DeleteUserWindow(),
  uploadDatabase: new UploadDatabaseWindow(),
  importDatabase: new ImportDatabaseWindow()
};

// ts/admin/admin.ts
adminEls.settingsForm.onsubmit = (e) => {
  e.preventDefault();
  submitSettings();
};
adminEls.logout.onclick = (e) => {
  if (SettingsChanges.changesCount > 0) {
    if (!confirm(Constants.unsavedChangesMessage))
      return;
    window.onbeforeunload = null;
  }
  logout();
};
window.onbeforeunload = (e) => {
  if (SettingsChanges.changesCount === 0)
    return void 0;
  e.preventDefault();
};
adminEls.power.restart.onclick = (e) => restart();
adminEls.power.shutdown.onclick = (e) => shutdown();
adminEls.downloadLogs.onclick = (e) => downloadLogs();
adminEls.resetSettings.open.onclick = (e) => windowInstances.reset.show();
adminEls.resetSettings.cancel.onclick = (e) => windowInstances.reset.hide();
adminEls.resetSettings.dialog.onclick = (e) => {
  if (e.target === e.currentTarget) {
    e.stopPropagation();
    windowInstances.reset.hide();
  }
};
adminEls.resetSettings.form.onsubmit = (e) => {
  e.preventDefault();
  windowInstances.reset.submit();
};
adminEls.plugins.open.onclick = (e) => windowInstances.plugins.show();
adminEls.plugins.cancel.onclick = (e) => windowInstances.plugins.hide();
adminEls.plugins.dialog.onclick = (e) => {
  if (e.target === e.currentTarget) {
    e.stopPropagation();
    windowInstances.plugins.hide();
  }
};
adminEls.plugins.add.onclick = (e) => {
  if (adminEls.plugins.addRow.classList.contains("hidden")) {
    adminEls.plugins.addInput.value = "";
    hide({
      to_show: [adminEls.plugins.addRow],
      to_hide: [adminEls.plugins.error]
    });
    adminEls.plugins.addInput.focus();
  } else {
    hide({
      to_hide: [adminEls.plugins.addRow, adminEls.plugins.error]
    });
  }
};
adminEls.plugins.form.onsubmit = (e) => {
  e.preventDefault();
  windowInstances.plugins.submit();
};
adminEls.addUser.open.onclick = (e) => windowInstances.addUser.show();
adminEls.addUser.cancel.onclick = (e) => windowInstances.addUser.hide();
adminEls.addUser.dialog.onclick = (e) => {
  if (e.target === e.currentTarget) {
    e.stopPropagation();
    windowInstances.addUser.hide();
  }
};
adminEls.addUser.form.onsubmit = (e) => {
  e.preventDefault();
  windowInstances.addUser.submit();
};
adminEls.editUser.cancel.onclick = (e) => windowInstances.editUser.hide();
adminEls.editUser.dialog.onclick = (e) => {
  if (e.target === e.currentTarget) {
    e.stopPropagation();
    windowInstances.editUser.hide();
  }
};
adminEls.editUser.form.onsubmit = (e) => {
  e.preventDefault();
  windowInstances.editUser.submit();
};
adminEls.deleteUser.cancel.onclick = (e) => windowInstances.deleteUser.hide();
adminEls.deleteUser.dialog.onclick = (e) => {
  if (e.target === e.currentTarget) {
    e.stopPropagation();
    windowInstances.deleteUser.hide();
  }
};
adminEls.deleteUser.confirm.onclick = (e) => windowInstances.deleteUser.submit();
adminEls.uploadDb.open.onclick = (e) => windowInstances.uploadDatabase.show();
adminEls.uploadDb.cancel.onclick = (e) => windowInstances.uploadDatabase.hide();
adminEls.uploadDb.dialog.onclick = (e) => {
  if (e.target === e.currentTarget) {
    e.stopPropagation();
    windowInstances.uploadDatabase.hide();
  }
};
adminEls.uploadDb.form.onsubmit = (e) => {
  e.preventDefault();
  windowInstances.uploadDatabase.submit();
};
adminEls.downloadCurrentDatabase.onclick = (e) => downloadCurrentDatabase();
adminEls.importDb.cancel.onclick = (e) => windowInstances.importDatabase.hide();
adminEls.importDb.dialog.onclick = (e) => {
  if (e.target === e.currentTarget) {
    e.stopPropagation();
    windowInstances.importDatabase.hide();
  }
};
adminEls.importDb.form.onclick = (e) => {
  e.preventDefault();
  windowInstances.importDatabase.submit();
};
OnLoadRunner.add(
  loadAbout,
  loadSettings,
  loadUsers,
  loadBackups,
  windowInstances.reset.prepare
);
OnLoadRunner.runOnLoad();
