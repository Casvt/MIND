const NavButtons = {
	home: document.querySelector('#home-button'),
	notification_services: document.querySelector('#notification-services-button'),
	settings: document.querySelector('#settings-button'),
	log_out: document.querySelector('#logout-button')
};

const LibEls = {
	tab_selector: document.querySelector('.tab-selector'),
	tab_container: document.querySelector('.tab-container'),
	search_bar: {
		form: document.querySelector('#search-form'),
		input: document.querySelector('#search-input'),
		clear: document.querySelector('#clear-button'),
		sort: document.querySelector('#sort-input'),
		wide: document.querySelector('#wide-button')
	},
	wide_toggle: document.querySelector('#wide-toggle')
};

//
// Helpers
//
function getSorting(type, key=false) {
	let sorting_key;
	if (type === reminderTypes.reminder)
		sorting_key = 'sorting_reminders';
	else if (type === reminderTypes.static_reminder)
		sorting_key = 'sorting_static';
	else if (type === reminderTypes.template)
		sorting_key = 'sorting_templates';

	if (key)
		return sorting_key;
	else
		return getLocalStorage(sorting_key)[sorting_key];
};

function getActiveTab() {
	for (let t of Object.values(reminderTypes)) {
		if (getComputedStyle(t).display === 'flex')
			return t
	};
	return null;
};

// 
// Filling library
// 
function fillTable(table, results) {
	table.querySelectorAll('button.entry:not(.add-entry)').forEach(
		e => e.remove()
	);

	results.forEach(r => {
		const entry = document.createElement('button');
		entry.classList.add('entry');
		entry.dataset.id = r.id;
		entry.onclick = e => showEdit(r.id, table);
		if (r.color !== null)
			entry.style.setProperty('--color', r.color);

		const title = document.createElement('h2');
		title.innerText = r.title;
		entry.appendChild(title);

		if (table === reminderTypes.reminder) {
			const time = document.createElement('p');
			let offset = new Date(r.time * 1000).getTimezoneOffset() * -60;
			let d = new Date((r.time + offset) * 1000);
			let formatted_date = d.toLocaleString(getLocalStorage('locale')['locale']);

			if (r.repeat_interval !== null) {
				if (r.repeat_interval === 1) {
					let quantity = r.repeat_quantity.slice(0, -1)
					var interval_text = ` (each ${quantity})`;
				} else {
					var interval_text = ` (every ${r.repeat_interval} ${r.repeat_quantity})`;
				};
				formatted_date += interval_text;

			} else if (r.weekdays !== null)
				formatted_date += ` (each ${r.weekdays.map(d => week_days[d]).join(', ')})`;

			if (!r.enabled)
				formatted_date += ' (Disabled)';

			time.innerText = formatted_date;
			entry.appendChild(time);
		};

		table.appendChild(entry);
	});
	evaluateSizing();
};

function fillLibrary(type=null) {
	if (autoSearchTimer !== null)
		clearTimeout(autoSearchTimer)

	let tab_type = type || getActiveTab();

	let url;
	if (tab_type === reminderTypes.reminder)
		url = `${urlPrefix}/api/reminders`;
	else if (tab_type === reminderTypes.static_reminder)
		url = `${urlPrefix}/api/staticreminders`;
	else if (tab_type === reminderTypes.template)
		url = `${urlPrefix}/api/templates`;
	else
		return;

	const sorting = getSorting(tab_type);
	const query = LibEls.search_bar.input.value;
	if (query)
		url = `${url}/search?api_key=${apiKey}&sort_by=${sorting}&query=${query}`;
	else
		url = `${url}?api_key=${apiKey}&sort_by=${sorting}`;

	fetch(url)
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);
		return response.json();
	})
	.then(json => fillTable(tab_type, json.result))
	.catch(e => {
		if (e === 401)
			window.location.href = `${urlPrefix}/`;
		else
			console.log(e);
	});
};

function saveSorting() {
	const type = getActiveTab();
	const sorting_key = getSorting(type, key=true);
	const value = LibEls.search_bar.sort.value;
	setLocalStorage({[sorting_key]: value});
};

function evaluateSizing() {
	const tab = getActiveTab();
	const entries = [...tab.querySelectorAll('button:not(.add-entry)')];
	entries.forEach(e => e.classList.remove('fit'));
	entries.forEach(e => {
		const title = e.querySelector('h2');
		if (title.clientHeight < title.scrollHeight)
			e.classList.add('expand');
	});
	entries.forEach(e => e.classList.add('fit'));
};

// code run on load

var autoSearchTimer = null

Object.values(reminderTypes).forEach(t => fillLibrary(t));
setInterval(() => fillLibrary(reminderTypes.reminder), 60000);

const week_days = ["Mo", "Tu", "We", "Thu", "Fr", "Sa", "Su"];

NavButtons.home.onclick = e => showWindow("home");
NavButtons.notification_services.onclick = e => showWindow("notification");
NavButtons.settings.onclick = e => showWindow("settings");
NavButtons.log_out.onclick = e => logout();

LibEls.search_bar.form.action = 'javascript:fillLibrary();'

LibEls.search_bar.input.onkeydown = e => {
	if (autoSearchTimer !== null)
		clearTimeout(autoSearchTimer)

	autoSearchTimer = setTimeout(fillLibrary, constants.autoSearchTimeout)
}

LibEls.search_bar.sort.value = getSorting(getActiveTab());
LibEls.search_bar.sort.onchange = e => {
	saveSorting();
	fillLibrary();
};
LibEls.search_bar.clear.onclick = e => {
	LibEls.search_bar.input.value = '';
	fillLibrary();
};
LibEls.wide_toggle.onchange = e => {
	setLocalStorage({wide_library_view: LibEls.wide_toggle.checked});
};
LibEls.wide_toggle.checked = getLocalStorage('wide_library_view')['wide_library_view'];

LibEls.tab_selector.querySelectorAll('input').forEach(r => r.onchange = e => {
	evaluateSizing();
	LibEls.search_bar.input.value = '';
	LibEls.search_bar.sort.value = getSorting(getActiveTab());
});
