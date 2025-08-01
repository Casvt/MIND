//
// region Definitions
//
const constants = {
    /**
     * The duration of the animation set for the window translation
     */
    windowAnimationDuration: 500,

	/**
	 * The amount of time to wait after the user stops typing to automatically
	 * trigger the search
	 */
	autoSearchTimeout: 500,

	/**
	 * The amount of time to wait after the user stops typing to automatically
	 * trigger the search for notification services
	 */
	autoSearchTimeoutNs: 250
}

const icons = {
	save: '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:svgjs="http://svgjs.com/svgjs" width="256" height="256" x="0" y="0" viewBox="0 0 24 24" xml:space="preserve"><g><path d="M12,10a4,4,0,1,0,4,4A4,4,0,0,0,12,10Zm0,6a2,2,0,1,1,2-2A2,2,0,0,1,12,16Z"></path><path d="M22.536,4.122,19.878,1.464A4.966,4.966,0,0,0,16.343,0H5A5.006,5.006,0,0,0,0,5V19a5.006,5.006,0,0,0,5,5H19a5.006,5.006,0,0,0,5-5V7.657A4.966,4.966,0,0,0,22.536,4.122ZM17,2.08V3a3,3,0,0,1-3,3H10A3,3,0,0,1,7,3V2h9.343A2.953,2.953,0,0,1,17,2.08ZM22,19a3,3,0,0,1-3,3H5a3,3,0,0,1-3-3V5A3,3,0,0,1,5,2V3a5.006,5.006,0,0,0,5,5h4a4.991,4.991,0,0,0,4.962-4.624l2.16,2.16A3.02,3.02,0,0,1,22,7.657Z"></path></g></svg>',
	edit: '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:svgjs="http://svgjs.com/svgjs" width="256" height="256" x="0" y="0" viewBox="0 0 24 24" xml:space="preserve"><g><g id="_01_align_center" data-name="01 align center"><path d="M22.94,1.06a3.626,3.626,0,0,0-5.124,0L0,18.876V24H5.124L22.94,6.184A3.627,3.627,0,0,0,22.94,1.06ZM4.3,22H2V19.7L15.31,6.4l2.3,2.3ZM21.526,4.77,19.019,7.277l-2.295-2.3L19.23,2.474a1.624,1.624,0,0,1,2.3,2.3Z"></path></g></g></svg>',
	delete: '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:svgjs="http://svgjs.com/svgjs" width="256" height="256" x="0" y="0" viewBox="0 0 24 24" xml:space="preserve"><g><g id="_01_align_center" data-name="01 align center"><path d="M22,4H17V2a2,2,0,0,0-2-2H9A2,2,0,0,0,7,2V4H2V6H4V21a3,3,0,0,0,3,3H17a3,3,0,0,0,3-3V6h2ZM9,2h6V4H9Zm9,19a1,1,0,0,1-1,1H7a1,1,0,0,1-1-1V6H18Z"></path><rect x="9" y="10" width="2" height="8"></rect><rect x="13" y="10" width="2" height="8"></rect></g></g></svg>',
	add: '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:svgjs="http://svgjs.com/svgjs" width="256" height="256" x="0" y="0" viewBox="0 0 512 512" xml:space="preserve"><g><g><path d="M480,224H288V32c0-17.673-14.327-32-32-32s-32,14.327-32,32v192H32c-17.673,0-32,14.327-32,32s14.327,32,32,32h192v192   c0,17.673,14.327,32,32,32s32-14.327,32-32V288h192c17.673,0,32-14.327,32-32S497.673,224,480,224z"></path></g></g></svg>',
	download: '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" id="Capa_1" x="0px" y="0px" viewBox="0 0 512 512" xml:space="preserve" width="512" height="512"><g><path d="M210.731,386.603c24.986,25.002,65.508,25.015,90.51,0.029c0.01-0.01,0.019-0.019,0.029-0.029l68.501-68.501   c7.902-8.739,7.223-22.23-1.516-30.132c-8.137-7.357-20.527-7.344-28.649,0.03l-62.421,62.443l0.149-329.109   C277.333,9.551,267.782,0,256,0l0,0c-11.782,0-21.333,9.551-21.333,21.333l-0.192,328.704L172.395,288   c-8.336-8.33-21.846-8.325-30.176,0.011c-8.33,8.336-8.325,21.846,0.011,30.176L210.731,386.603z"/><path d="M490.667,341.333L490.667,341.333c-11.782,0-21.333,9.551-21.333,21.333V448c0,11.782-9.551,21.333-21.333,21.333H64   c-11.782,0-21.333-9.551-21.333-21.333v-85.333c0-11.782-9.551-21.333-21.333-21.333l0,0C9.551,341.333,0,350.885,0,362.667V448   c0,35.346,28.654,64,64,64h384c35.346,0,64-28.654,64-64v-85.333C512,350.885,502.449,341.333,490.667,341.333z"/></g></svg>',
	upload: '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" id="Capa_1" x="0px" y="0px" viewBox="0 0 512.008 512.008" xml:space="preserve" width="512" height="512"><g><path d="M172.399,117.448l62.421-62.443l-0.149,329.344c0,11.782,9.551,21.333,21.333,21.333l0,0   c11.782,0,21.333-9.551,21.333-21.333l0.149-328.981l62.123,62.144c8.475,8.185,21.98,7.951,30.165-0.524   c7.985-8.267,7.985-21.374,0-29.641L301.273,18.76c-24.986-25.002-65.508-25.015-90.51-0.029c-0.01,0.01-0.019,0.019-0.029,0.029   l-68.501,68.523c-8.185,8.475-7.951,21.98,0.524,30.165C151.024,125.433,164.131,125.433,172.399,117.448z"/><path d="M490.671,341.341L490.671,341.341c-11.782,0-21.333,9.551-21.333,21.333v85.333c0,11.782-9.551,21.333-21.333,21.333h-384   c-11.782,0-21.333-9.551-21.333-21.333v-85.333c0-11.782-9.551-21.333-21.333-21.333l0,0c-11.782,0-21.333,9.551-21.333,21.333   v85.333c0,35.346,28.654,64,64,64h384c35.346,0,64-28.654,64-64v-85.333C512.004,350.892,502.453,341.341,490.671,341.341z"/></g></svg>',
	loading: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="m10.5 1.5c0-.828.672-1.5 1.5-1.5s1.5.672 1.5 1.5-.672 1.5-1.5 1.5-1.5-.672-1.5-1.5zm1.5 22.5c.828 0 1.5-.672 1.5-1.5s-.672-1.5-1.5-1.5-1.5.672-1.5 1.5.672 1.5 1.5 1.5zm9-12c0 .828.672 1.5 1.5 1.5s1.5-.672 1.5-1.5-.672-1.5-1.5-1.5-1.5.672-1.5 1.5zm-21 0c0 .828.672 1.5 1.5 1.5s1.5-.672 1.5-1.5-.672-1.5-1.5-1.5-1.5.672-1.5 1.5zm17.293-7.577c.828 0 1.5-.672 1.5-1.5s-.672-1.5-1.5-1.5-1.5.672-1.5 1.5.672 1.5 1.5 1.5zm3.779 3.798c.828 0 1.5-.672 1.5-1.5s-.672-1.5-1.5-1.5-1.5.672-1.5 1.5.672 1.5 1.5 1.5zm-.01 10.567c.828 0 1.5-.672 1.5-1.5s-.672-1.5-1.5-1.5-1.5.672-1.5 1.5.672 1.5 1.5 1.5zm-3.788 3.788c.828 0 1.5-.672 1.5-1.5s-.672-1.5-1.5-1.5-1.5.672-1.5 1.5.672 1.5 1.5 1.5zm-10.577-.01c.828 0 1.5-.672 1.5-1.5s-.672-1.5-1.5-1.5-1.5.672-1.5 1.5.672 1.5 1.5 1.5zm-3.75-3.779c.828 0 1.5-.672 1.5-1.5s-.672-1.5-1.5-1.5-1.5.672-1.5 1.5.672 1.5 1.5 1.5zm-.01-10.596c.828 0 1.5-.672 1.5-1.5s-.672-1.5-1.5-1.5-1.5.672-1.5 1.5.672 1.5 1.5 1.5zm3.779-3.769c.828 0 1.5-.672 1.5-1.5s-.672-1.5-1.5-1.5-1.5.672-1.5 1.5.672 1.5 1.5 1.5z"/></svg>'
}


//
// region Helpers
//

/**
 * Hide and show elements.
 * 
 * @param {Array<HTMLElement>} to_hide The elements to hide,
 * by adding the `hidden` class.
 * 
 * @param {Array<HTMLElement>?} to_show The elements to show,
 * by removing the `hidden` class.
 */
function hide(to_hide, to_show) {
	to_hide.forEach(el => el.classList.add('hidden'))
	if (to_show !== null && to_show !== undefined)
		to_show.forEach(el => el.classList.remove('hidden'))
}


//
// region LocalStorage
//
const defaultValues = {
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
 * 
 * @param {string | string[] | null | undefined} keys The keys to fetch, or all
 * if null or undefined.
 * 
 * @returns {Object} The keys and their values.
 */
function getLocalStorage(keys) {
	const storage = JSON.parse(localStorage.getItem('MIND'))
	
	if (keys === undefined || keys === null)
		return storage
	
	const result = {}
	if (typeof keys === 'string')
		result[keys] = storage[keys]

	else if (typeof keys === 'object')
		for (const key in keys)
			result[key] = storage[key]

	return result
}

/**
 * Update the configuration stored in the local storage of the client (browser).
 * @param {Object} keys_values The new values for the given keys.
 */
function setLocalStorage(keys_values) {
	const storage = JSON.parse(localStorage.getItem('MIND'))

	for (const [key, value] of Object.entries(keys_values))
		storage[key] = value

	localStorage.setItem('MIND', JSON.stringify(storage))
}

/**
 * Setup the configuration stored in the local storage of the client (browser)
 * with default values.
 */
function setupLocalStorage() {
	if (!localStorage.getItem('MIND'))
		localStorage.setItem('MIND', JSON.stringify(defaultValues))

	const currentValues = getLocalStorage()
	const cleanedVersion = {}
	Object.keys(defaultValues).forEach(k => {
		if (currentValues[k] === undefined)
			cleanedVersion[k] = defaultValues[k]
		else
			cleanedVersion[k] = currentValues[k]
	})

	localStorage.setItem('MIND', JSON.stringify(cleanedVersion))
}


//
// region Fetching
//

/**
 * Make a GET request to the API.
 * 
 * @param {string} endpoint The endpoint to make the request to, without API URL
 * prefix.
 * 
 * @param {Object} params The URL parameters to use in the request.
 * API key doesn't need to be supplied.
 * 
 * @param {bool} jsonReturn Whether to return the json response, or the raw
 * response.
 * 
 * @param {bool} checkAuth Check whether authentication failed and if so
 * automatically redirect to login page.
 * 
 * @returns The response.
 */
async function fetchAPI(endpoint, params={}, jsonReturn=true, checkAuth=true) {
	let formattedParams = ''
	if (apiKey !== null)
		params.api_key = apiKey
	if (Object.keys(params).length) {
		formattedParams = '?' + Object.entries(params).map(p => p.join('=')).join('&')
	}

	return fetch(`${urlPrefix}/api${endpoint}${formattedParams}`)
	.then(response => {
		if (!response.ok)
			return Promise.reject(response)
		if (jsonReturn)
			return response.json()
		else
			return response
	})
	.catch(response => {
		if (checkAuth && response.status === 401) {
			setLocalStorage({api_key: null})
			window.location.href = `${urlPrefix}/`
		} else {
			return Promise.reject(response)
		}
	})
}

/**
 * Make a POST, PUT or DELETE request to the API.
 * 
 * @param {string} method The HTTP method to use.
 * 
 * @param {string} endpoint The endpoint to make the request to, without API URL
 * prefix.
 * 
 * @param {Object} params The URL parameters to use in the request.
 * API key doesn't need to be supplied.
 * 
 * @param {any} body The JSON to supply in the body of the request.
 * 
 * @param {bool} jsonReturn Whether to return the json response, or the raw
 * response.
 * 
 * @param {bool} checkAuth Check whether authentication failed and if so
 * automatically redirect to login page.
 * 
 * @returns The response.
 */
async function sendAPI(
	method,
	endpoint,
	params={},
	body={},
	jsonReturn=true,
	checkAuth=true
) {
	let formattedParams = ''
	if (apiKey !== null)
		params.api_key = apiKey
	if (Object.keys(params).length) {
		formattedParams = '?' + Object.entries(params).map(p => p.join('=')).join('&')
	}

	return fetch(`${urlPrefix}/api${endpoint}${formattedParams}`, {
		'method': method,
		'headers': {'Content-Type': 'application/json'},
		'body': Object.entries(body).length !== 0 ? JSON.stringify(body) : ''
	})
	.then(response => {
		if (!response.ok)
			return Promise.reject(response)
		if (jsonReturn)
			return response.json()
		else
			return response
	})
	.catch(response => {
		if (checkAuth && response.status === 401) {
			setLocalStorage({api_key: null})
			window.location.href = `${urlPrefix}/`
		} else {
			return Promise.reject(response)
		}
	})
}

/**
 * Check the login status, and redirect to proper place if not already there.
 */
function checkLogin() {
	if (apiKey === null)
		window.location.href = `${urlPrefix}/`

	fetchAPI("/auth/status")
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
	.catch(e => console.log(e))
}

/**
 * Log out and redirect to login page.
 */
function logout() {
	sendAPI("POST", "/auth/logout")
	.then(response => {
		setLocalStorage({'api_key': null})
		window.location.href = `${urlPrefix}/`
	})
}

// 
// region On load
// 
setupLocalStorage()

/**
 * The URL prefix that the application is running on.
 */
const urlPrefix = document.getElementById('url_prefix').dataset.value

/**
 * The API key that can be used to authenticate API requests. Not guaranteed to
 * be valid.
 */
const apiKey = getLocalStorage('api_key')['api_key']
