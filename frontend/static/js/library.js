const sorting_options = {};
sorting_options[types.reminder.id] = [
	['time', 'Time'],
	['time_reversed', 'Time Reversed'],
	['title', 'Title'],
	['title_reversed', 'Title Reversed'],
	['date_added', 'Date Added'],
	['date_added_reversed', 'Date Added Reversed']
];
sorting_options[types.static_reminder.id] = [
	['title', 'Title'],
	['title_reversed', 'Title Reversed'],
	['date_added', 'Date Added'],
	['date_added_reversed', 'Date Added Reversed']
];
sorting_options[types.template.id] = [
	['title', 'Title'],
	['title_reversed', 'Title Reversed'],
	['date_added', 'Date Added'],
	['date_added_reversed', 'Date Added Reversed']
];

function showTab(button) {
	// Apply styling to selected button
	document.querySelectorAll('.tab-selector > button').forEach(
		b => b.dataset.selected = b === button ? 'true' : 'false'
	);

	// Show desired tab and hide all others
	document.querySelectorAll('#home > div:not(.tab-selector):not(.search-container)').forEach(
		e => e.classList.add('hidden')
	);
	document.getElementById(button.dataset.target).classList.remove('hidden');
	
	fillSortOptions();
	document.querySelector('#search-input').value = '';
};

// 
// Filling library
// 
function fillTable(table, results) {
	table.querySelectorAll('button.entry:not(.add-entry)').forEach(e => e.remove());

	results.forEach(r => {
		const entry = document.createElement('button');
		entry.classList.add('entry');
		entry.dataset.id = r.id;
		entry.addEventListener('click', e => showEdit(r.id, table));
		if (r.color !== null)
			entry.style.setProperty('--color', r.color);
		
		const title = document.createElement('h2');
		title.innerText = r.title;
		entry.appendChild(title);

		if (table === types.reminder) {
			const time = document.createElement('p');
			var offset = new Date(r.time * 1000).getTimezoneOffset() * -60;
			var d = new Date((r.time + offset) * 1000);
			var formatted_date = d.toLocaleString('en-CA').slice(0,10) + ' ' + d.toTimeString().slice(0,5);
			if (r.repeat_interval !== null) {
				if (r.repeat_interval === 1) {
					var quantity = r.repeat_quantity.endsWith('s') ? r.repeat_quantity.slice(0, -1) : r.repeat_quantity;
					var interval_text = ` (each ${quantity})`;
				} else {
					var quantity = r.repeat_quantity.endsWith('s') ? r.repeat_quantity : r.repeat_quantity + 's';
					var interval_text = ` (every ${r.repeat_interval} ${quantity})`;
				};
				formatted_date += interval_text;
			};
			time.innerText = formatted_date;
			entry.appendChild(time);
		};
		
		table.appendChild(entry);
		
		if (title.clientHeight < title.scrollHeight)
			entry.classList.add('expand');
	});
	table.querySelectorAll('button.entry:not(.add-entry)').forEach(r => r.classList.add('fit'));
};

function fillLibrary(url, type) {
	fetch(url)
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);
		return response.json();
	})
	.then(json => fillTable(type, json.result))
	.catch(e => {
		if (e === 401)
			window.location.href = `${url_prefix}/`;
		else
			console.log(e);
	});
};

function fillReminders() {
	const sorting = document.querySelector('#sort-input').value;
	fillLibrary(`/api/reminders?api_key=${api_key}&sort_by=${sorting}`, types.reminder);
};

function fillStaticReminders(assume_sorting=false) {
	let sorting;
	if (assume_sorting)
		sorting = sorting_options[types.static_reminder.id][0][0];
	else
		sorting = document.querySelector('#sort-input').value;
	fillLibrary(`/api/staticreminders?api_key=${api_key}&sort_by=${sorting}`, types.static_reminder);
}

function fillTemplates(assume_sorting=false) {
	let sorting;
	if (assume_sorting)
		sorting = sorting_options[types.template.id][0][0];
	else
		sorting = document.querySelector('#sort-input').value;
	fillLibrary(`/api/templates?api_key=${api_key}&sort_by=${sorting}`, types.template);
};

// 
// Library search
// 
function searchLibrary() {
	const query = document.querySelector('#search-input').value,
		tab = document.getElementById(
			document.querySelector('.tab-selector > button[data-selected="true"]').dataset.target
		)
	const sorting = document.querySelector('#sort-input').value;
	let url;
	if (tab === types.reminder)
		url = `${url_prefix}/api/reminders/search?api_key=${api_key}&query=${query}&sort_by=${sorting}`;
	else if (tab === types.static_reminder)
		url = `${url_prefix}/api/staticreminders/search?api_key=${api_key}&query=${query}&sort_by=${sorting}`;
	else if (tab === types.template)
		url = `${url_prefix}/api/templates/search?api_key=${api_key}&query=${query}&sort_by=${sorting}`;
	else return;

	fillLibrary(url, tab);
};

function clearSearchLibrary() {
	document.querySelector('#search-input').value = '';
	const tab = document.getElementById(
		document.querySelector('.tab-selector > button[data-selected="true"]').dataset.target
	)
	if (tab === types.reminder)
		fillReminders();
	else if (tab === types.static_reminder)
		fillStaticReminders();
	else if (tab === types.template)
		fillTemplates();
	else return;
};

// 
// Library sort
// 
function fillSortOptions() {
	const tab = document.getElementById(
		document.querySelector('.tab-selector > button[data-selected="true"]').dataset.target
	)
	const sort_options = sorting_options[tab.id];
	
	const select = document.getElementById('sort-input');
	select.innerHTML = '';
	sort_options.forEach(o => {
		const entry = document.createElement('option');
		entry.value = o[0]
		entry.innerText = o[1]
		select.appendChild(entry);
	});
	select.querySelector(':first-child').setAttribute('selected', '');
};

function applySorting() {
	const query = document.querySelector('#search-input').value;
	if (query !== '') {
		searchLibrary();
		return;
	};

	const sorting = document.getElementById('sort-input').value,
		tab = document.getElementById(
			document.querySelector('.tab-selector > button[data-selected="true"]').dataset.target
		)

	let url;
	if (tab === types.reminder)
		url = `${url_prefix}/api/reminders?api_key=${api_key}&sort_by=${sorting}`;
	else if (tab === types.static_reminder)
		url = `${url_prefix}/api/staticreminders?api_key=${api_key}&sort_by=${sorting}`;
	else if (tab === types.template)
		url = `${url_prefix}/api/templates?api_key=${api_key}&sort_by=${sorting}`;
	else return;

	fetch(url)
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);
		return response.json();
	})
	.then(json => fillTable(tab, json.result))
	.catch(e => {
		if (e === 401)
			window.location.href = `${url_prefix}/`;
		else
			console.log(e);
	});
};

// code run on load

document.querySelectorAll('.tab-selector > button').forEach(b => {
	b.addEventListener('click', e => showTab(b));
});

fillSortOptions();
fillReminders();
fillStaticReminders(assume_sorting=true);
fillTemplates(assume_sorting=true);
setInterval(fillReminders, 60000);

document.querySelector('#search-form').setAttribute('action', 'javascript:searchLibrary();');
document.querySelector('#clear-button').addEventListener('click', e => clearSearchLibrary());
document.querySelector('#sort-input').addEventListener('change', e => applySorting());
