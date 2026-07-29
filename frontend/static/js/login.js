// ts/general.ts
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

// ts/login/elements.ts
var loginEls = {
  switchButtons: [...document.querySelectorAll(".switch-button")],
  formSwitch: document.getElementById("form-switch"),
  mfaSwitch: document.getElementById("mfa-switch"),
  login: {
    form: document.getElementById("login-form"),
    inputContainers: {
      username: document.querySelector("#login-form .checked-input-container:has(#login-username)"),
      password: document.querySelector("#login-form .checked-input-container:has(#login-password)")
    },
    inputs: {
      username: document.getElementById("login-username"),
      password: document.getElementById("login-password")
    }
  },
  mfa: {
    form: document.getElementById("mfa-form"),
    error: document.getElementById("invalid-mfa-code"),
    inputContainer: document.getElementById("mfa-container")
  },
  register: {
    form: document.getElementById("register-form"),
    inputContainers: {
      username: document.querySelector("#register-form .checked-input-container:has(#register-username)")
    },
    inputs: {
      username: document.getElementById("register-username"),
      password: document.getElementById("register-password")
    },
    errors: {
      usernameInvalid: document.getElementById("invalid-username"),
      usernameTaken: document.getElementById("taken-username")
    }
  }
};

// ts/login/actions.ts
function getMFACode() {
  return [
    ...loginEls.mfa.inputContainer.querySelectorAll('input[type="number"]')
  ].map((el) => el.value).join("");
}
function login(username, password) {
  loginEls.login.inputContainers.username.classList.remove("error-input-container");
  loginEls.login.inputContainers.password.classList.remove("error-input-container");
  if (!username)
    username = loginEls.login.inputs.username.value;
  if (!password)
    password = loginEls.login.inputs.password.value;
  let body = {
    username,
    password
  };
  if (loginEls.mfaSwitch.checked)
    body.mfa_code = getMFACode();
  fetchAPI("/auth/login", {
    redirectUnauth: false,
    method: "POST",
    body
  }).then((json) => {
    if (json.error === "MFACodeRequired") {
      loginEls.mfa.error.classList.add("hidden");
      loginEls.mfaSwitch.checked = true;
      loginEls.mfa.inputContainer.querySelector("input")?.focus();
      return;
    }
    const storage = getLocalStorage();
    storage.api_key = json.result.api_key;
    setLocalStorage(storage);
    if (json.result.admin)
      window.location.href = "./admin";
    else
      window.location.href = "./reminders";
  }).catch((json) => {
    if (json.error === "UserNotFound")
      loginEls.login.inputContainers.username.classList.add("error-input-container");
    else if (json.error === "AccessUnauthorized") {
      loginEls.login.inputContainers.password.classList.add("error-input-container");
      loginEls.mfa.error.classList.remove("hidden");
    } else
      console.log(json);
  });
}
function register() {
  loginEls.register.inputContainers.username.classList.remove("error-input-container");
  hide({ to_hide: [
    loginEls.register.errors.usernameInvalid,
    loginEls.register.errors.usernameTaken
  ] });
  const body = {
    username: loginEls.register.inputs.username.value,
    password: loginEls.register.inputs.password.value
  };
  fetchAPI("/user/add", {
    method: "POST",
    body
  }).then((_) => login(body.username, body.password)).catch((json) => {
    if (json.error === "UsernameInvalid") {
      loginEls.register.errors.usernameInvalid.innerText = invalidUsernameReasonMap[json.result.reason];
      hide({ to_show: [loginEls.register.errors.usernameInvalid] });
      loginEls.register.inputContainers.username.classList.add("error-input-container");
    } else if (json.error === "UsernameTaken") {
      hide({ to_show: [loginEls.register.errors.usernameTaken] });
      loginEls.register.inputContainers.username.classList.add("error-input-container");
    } else
      console.log(json);
  });
}
function checkNewAccountsAllowed() {
  const storage = getLocalStorage();
  if (!storage.allow_new_accounts_cache)
    hide({ to_hide: [loginEls.switchButtons[0]] });
  fetchAPI("/settings").then((json) => {
    if (!json.result.allow_new_accounts)
      hide({ to_hide: [loginEls.switchButtons[0]] });
    else
      hide({ to_show: [loginEls.switchButtons[0]] });
    if (storage.allow_new_accounts_cache !== json.result.allow_new_accounts) {
      storage.allow_new_accounts_cache = json.result.allow_new_accounts;
      setLocalStorage(storage);
    }
  });
}

// ts/login/login.ts
loginEls.switchButtons.forEach(
  (el) => el.onclick = (e) => loginEls.formSwitch.checked = !loginEls.formSwitch.checked
);
loginEls.mfa.inputContainer.querySelectorAll("input:not(:last-of-type)").forEach(
  (el) => el.oninput = (e) => {
    if (["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"].includes(el.value)) {
      const nextInput = el.nextElementSibling;
      nextInput.focus();
    }
  }
);
loginEls.login.form.onsubmit = (e) => {
  e.preventDefault();
  login();
};
loginEls.mfa.form.onsubmit = (e) => {
  e.preventDefault();
  login();
};
loginEls.register.form.onsubmit = (e) => {
  e.preventDefault();
  register();
};
OnLoadRunner.add(checkNewAccountsAllowed);
OnLoadRunner.runOnLoad();
