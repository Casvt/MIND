// region Helpers

/**
 * Hide and show elements.
 * 
 * @param {Array<HTMLElement>} to_hide The elements to hide,
 * by adding the `hidden` class.
 * 
 * @param {Array<HTMLElement>?} to_show The elements to show,
 * by removing the `hidden` class.
 */
export function hide(
    { to_hide = [], to_show = [] }: { to_hide?: HTMLElement[], to_show?: HTMLElement[] } = {}
): void {
	to_hide.forEach(el => el.classList.add('hidden'))
	if (to_show !== null && to_show !== undefined)
		to_show.forEach(el => el.classList.remove('hidden'))
}

// region LocalStorage
interface localStorageFields {
    api_key: string | null
    locale: string
    default_service: number | null
    sorting_reminders: string
    sorting_static: string
    sorting_templates: string
    wide_library_view: boolean
    allow_new_accounts_cache: boolean
    show_clock: string
}

const localStorageDefaultValues: localStorageFields = {
	api_key: null,
	locale: 'en-GB',
	default_service: null,
	sorting_reminders: 'time',
	sorting_static: 'title',
	sorting_templates: 'title',
	wide_library_view: false,
	allow_new_accounts_cache: true,
	show_clock: 'no'
}

/**
 * Get the configuration stored in the local storage of the client (browser).
 * @returns {localStorageFields} The keys and their values.
 */
export function getLocalStorage(): localStorageFields {
    return JSON.parse(localStorage.getItem("MIND") || "{}")
}

/**
 * Update the configuration stored in the local storage of the client (browser).
 * @param {localStorageFields} new_values The new values for the keys.
 */
export function setLocalStorage(new_values: localStorageFields): void {
	localStorage.setItem("MIND", JSON.stringify(new_values))
}

/**
 * Setup the configuration stored in the local storage of the client (browser)
 * with default values.
 */
export function setupLocalStorage(): void {
	if (!localStorage.getItem("MIND"))
        setLocalStorage(localStorageDefaultValues)

	const currentValues: {[key: string]: any} = getLocalStorage()
	const cleanedVersion: {[key: string]: any} = {}

    Object.keys(localStorageDefaultValues).forEach(k => {
		if (currentValues[k] === undefined)
            //@ts-expect-error
			cleanedVersion[k] = localStorageDefaultValues[k] 
		else
			cleanedVersion[k] = currentValues[k]
	})

    /// @ts-expect-error
    setLocalStorage(cleanedVersion)
}

// region Requests
interface APIRequestOptions {
    /**
     * The REST method to use when making the request.
     */
    method: string,
    
    /**
     * Any URL parameters to include in the request. The API key is already
     * supplied.
     */
    params: Record<string, any>,
    
    /**
     * The body of the request when it's a POST request. Will automatically
     * be stringified.
     */
    body: Record<string, any>,
    
    /**
     * If the server responds that the user is not authenticated, automatically
     * redirect to the login page.
     */
    redirectUnauth: boolean
}

const defaultAPIRequestOptions: APIRequestOptions = {
    method: "GET",
    params: {},
    body: {},
    redirectUnauth: true
}

interface APIResponse {
    error: string | null
    result: any
}

/**
 * Make a request to the MIND API. Automatically takes care of supplying the
 * API key, any headers and handling not being authenticated.
 * @param endpoint The API endpoint to make the request to, without API prefix.
 * @param options Extra options that influence the request.
 * @returns The JSON response. Raises an exception with the JSON response if
 *          the HTTP return code is bad.
 */
export async function fetchAPI(
    endpoint: string,
    options: Partial<APIRequestOptions> = {}
): Promise<APIResponse> {
    const finalOptions: APIRequestOptions = {
        ...defaultAPIRequestOptions,
        ...options
    }

    if (apiKey)
        finalOptions.params.api_key = apiKey

    let formattedParams = new URLSearchParams(finalOptions.params).toString()
    if (formattedParams)
        formattedParams = "?" + formattedParams

    let fetchOptions: RequestInit = {
        method: finalOptions.method
    }
    
    if (finalOptions.method === "POST") {
        fetchOptions.headers = {"Content-Type": "application/json"},
        fetchOptions.body = JSON.stringify(finalOptions.body)
    }

    const response = await fetch(
        `${urlPrefix}/api${endpoint}${formattedParams}`,
        fetchOptions
    )
    if (!response.ok) {
        if (finalOptions.redirectUnauth && response.status === 401) {
            const storage = getLocalStorage()
            storage.api_key = null
            setLocalStorage(storage)
            if (window.location.pathname !== `${urlPrefix}/`)
                window.location.href = `${urlPrefix}/`
        }
        throw await response.json()
    }
    return await response.json()
}

// region Auth
/**
 * Check whether the API key stored in local storage is valid (might be expired)
 * and whether they're on the correct page (might be user loading admin page). 
 * If not, redirect the user to the proper page. Await the call if this check
 * needs to be completed before anything else happens.
 */
async function checkLogin(): Promise<void> {
    if (!apiKey) {
        // API key not set so can't be logged in
        // Redirect to login page if not already there
        if (window.location.pathname !== `${urlPrefix}/`)
            window.location.href = `${urlPrefix}/`
        return
    }

    // Calling this function will already make the user redirect to the
    // login page if API key is invalid and they're not already there
    await fetchAPI("/auth/status")
    .then(json => {
        if (
            json.result.admin
            && window.location.pathname !== `${urlPrefix}/admin`
        )
            window.location.href = `${urlPrefix}/admin`
        
        else if (
            !json.result.admin
            && window.location.pathname !== `${urlPrefix}/reminders`
        )
            window.location.href = `${urlPrefix}/reminders`
    })
}

// region Globals
/**
 * The URL prefix that the UI is running at.
 */
const urlPrefix = document.getElementById("url_prefix")?.dataset.value || ""

/**
 * The API key as stored in local storage.
 */
const apiKey = getLocalStorage().api_key

// region On Load
/**
 * This class handles running code when the page loads. Use this mostly for
 * code that makes API requests that must happen after other requests.
 */
export class OnLoadRunner {
    private static onLoadFunctions: CallableFunction[] = []

    /**
     * Register one or more functions to run on load. They are run after the
     * functions that are already registered. If multiple are added, they are
     * run in the order that they are supplied.
     * @param {CallableFunction[]} functions The functions to register.
     */
    public static add(...functions: CallableFunction[]): void {
        this.onLoadFunctions.push(...functions)
    }

    /**
     * Run all registered functions sequentially.
     */
    public static async runOnLoad(): Promise<void> {
        for (const f of this.onLoadFunctions) {
            await f()
        }
    }
}

OnLoadRunner.add(setupLocalStorage, checkLogin)
