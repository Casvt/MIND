const colors = ["#3c3c3c", "#49191e", "#171a42", "#083b06", "#3b3506", "#300e40"];

const inputs = {
	'template': document.querySelector('#template-selection'),
	'color_toggle': document.querySelector('#color-toggle'),
	'color_button': document.querySelector('#color-button'),
	'color': document.querySelector('.color-list'),
	'title': document.querySelector('#title-input'),
	'time': document.querySelector('#time-input'),
	'notification_service': document.querySelector('.notification-service-selection'),
	'text': document.querySelector('#text-input'),
};

const type_buttons = {
	'normal_button': document.querySelector('#normal-button'),
	'repeat_button': document.querySelector('#repeat-button'),
	'weekday_button': document.querySelector('#weekday-button'),
	
	'repeat_bar': document.querySelector('.repeat-bar'),
	'repeat_interval': document.querySelector('#repeat-interval'),
	'repeat_quantity': document.querySelector('#repeat-quantity'),
	
	'weekday_bar': document.querySelector('.weekday-bar')
};

function fillColors() {
	colors.forEach((color, idx) => {
		const entry_toggle = document.createElement('label');
		entry_toggle.title = color;
		entry_toggle.style.setProperty('--color', color);
		inputs.color.appendChild(entry_toggle);

		const entry = document.createElement('input');
		entry.type = 'radio';
		entry.name = 'color_selection';
		entry.value = color;
		entry.checked = idx === 0;
		entry.classList.add('hidden');
		entry.onchange = e => {
			if (e.target === entry)
				inputs.color_button.style.setProperty('--color', color);
		};
		entry_toggle.appendChild(entry);
		
		if (idx === 0)
			inputs.color_button.style.setProperty('--color', color);
	});
};

function selectColor(color_code) {
	inputs.color.querySelector(`label[title="${color_code}"]`).click();
};

function toggleNormal() {
	type_buttons.normal_button.dataset.selected = 'true';
	type_buttons.repeat_button.dataset.selected = 'false';
	type_buttons.weekday_button.dataset.selected = 'false';

	type_buttons.repeat_bar.classList.add('hidden');
	type_buttons.repeat_interval.removeAttribute('required');
	type_buttons.repeat_interval.value = '';
	
	type_buttons.weekday_bar.classList.add('hidden');
	type_buttons.weekday_bar.querySelectorAll('input[type="checkbox"]')
		.forEach(el => el.checked = false);
};

function toggleRepeated() {
	type_buttons.normal_button.dataset.selected = 'false';
	type_buttons.repeat_button.dataset.selected = 'true';
	type_buttons.weekday_button.dataset.selected = 'false';

	type_buttons.repeat_bar.classList.remove('hidden');
	type_buttons.repeat_interval.setAttribute('required', '');
	
	type_buttons.weekday_bar.classList.add('hidden');
	type_buttons.weekday_bar.querySelectorAll('input[type="checkbox"]')
		.forEach(el => el.checked = false);
};

function toggleWeekDay() {
	type_buttons.normal_button.dataset.selected = 'false';
	type_buttons.repeat_button.dataset.selected = 'false';
	type_buttons.weekday_button.dataset.selected = 'true';

	type_buttons.repeat_bar.classList.add('hidden');
	type_buttons.repeat_interval.removeAttribute('required');
	type_buttons.repeat_interval.value = '';
	
	type_buttons.weekday_bar.classList.remove('hidden');
};

function testReminder() {
	const input = document.getElementById('test-reminder');
	const cl = document.getElementById('info').classList;
	const r_id = document.getElementById('info').dataset.id;
	const headers = {
		'method': 'POST',
		'headers': {'Content-Type': 'application/json'}
	};
	let url;
	if (cl.contains('show-edit-static-reminder')) {
		// Trigger static reminder
		url = `${url_prefix}/api/staticreminders/${r_id}?api_key=${api_key}`;
	} else {
		// Test reminder draft
		if (inputs.title.value === '') {
			input.classList.add('error-input');
			input.title = 'No title set';
			return
		} else {
			input.classList.remove('error-input');
			input.removeAttribute('title');
		};

		const ns = [...
			document.querySelectorAll('.notification-service-selection input[type="checkbox"]:checked')
		].map(c => parseInt(c.dataset.id))
		if (!ns.length) {
			input.classList.add('error-input');
			input.title = 'No notification service set';
			return
		} else {
			input.classList.remove('error-input');
			input.removeAttribute('title');
		};

		const data = {
			'title': inputs.title.value,
			'notification_services': ns,
			'text': inputs.text.value
		};
		headers.body = JSON.stringify(data);
		url = `${url_prefix}/api/reminders/test?api_key=${api_key}`;
	};
	fetch(url, headers)
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);
		input.classList.add('show-sent');		
	})
	.catch(e => {
		if (e === 401)
			window.location.href = `${url_prefix}/`;
		else
			console.log(e);
	});
};

function deleteInfo() {
	let url;
	const e_id = document.getElementById('info').dataset.id;
	const cl = document.getElementById('info').classList;
	if (cl.contains('show-edit-reminder')) {
		// Delete reminder
		url = `${url_prefix}/api/reminders/${e_id}?api_key=${api_key}`;
	} else if (cl.contains('show-edit-template')) {
		// Delete template
		url = `${url_prefix}/api/templates/${e_id}?api_key=${api_key}`;
	} else if (cl.contains('show-edit-static-reminder')) {
		// Delete static reminder
		url = `${url_prefix}/api/staticreminders/${e_id}?api_key=${api_key}`;
	} else return;
	
	fetch(url, {'method': 'DELETE'})
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);

		if (cl.contains('show-edit-reminder')) {
			// Delete reminder
			fillLibrary(Types.reminder);
		} else if (cl.contains('show-edit-template')) {
			// Delete template
			fillLibrary(Types.template);
			loadTemplateSelection();
		} else if (cl.contains('show-edit-static-reminder')) {
			// Delete static reminder
			fillLibrary(Types.static_reminder);
		};
		showWindow("home");
	})
	.catch(e => {
		if (e === 401)
			window.location.href = `${url_prefix}/`;
		else
			console.log(e);
	});
};

function submitInfo() {
	inputs.time.classList.remove('error-input');
	inputs.time.removeAttribute('title');
	inputs.notification_service.classList.remove('error-input');
	inputs.notification_service.removeAttribute('title');
	type_buttons.weekday_bar.classList.remove('error-input');
	type_buttons.weekday_bar.removeAttribute('title');
	let fetch_data = {
		url: null,
		method: null,
		call_back: null
	};
	const data = {
		'title': inputs.title.value,
		'notification_services': [...
				document.querySelectorAll('.notification-service-selection input[type="checkbox"]:checked')
			].map(c => parseInt(c.dataset.id)),
		'text': inputs.text.value,
		'color': inputs.color.querySelector('input:checked').value
	};
	if (data.color === colors[0])
		data.color = null;
	
	if (data.notification_services.length === 0) {
		inputs.notification_service.classList.add('error-input');
		inputs.notification_service.title = 'No notification service set';
		return;
	};

	const e_id = document.getElementById('info').dataset.id;
	const cl = document.getElementById('info').classList;
	if (cl.contains('show-add-reminder')) {
		// Add reminder
		data['time'] =
			(new Date(inputs.time.value) / 1000)
			+ (new Date(inputs.time.value).getTimezoneOffset() * 60);

		if (type_buttons.repeat_button.dataset.selected === 'true') {
			data['repeat_quantity'] = type_buttons.repeat_quantity.value;
			data['repeat_interval'] = parseInt(type_buttons.repeat_interval.value)

		} else if (type_buttons.weekday_button.dataset.selected === 'true') {
			data['weekdays'] = 
				[...document.querySelectorAll('.weekday-bar > input[type="checkbox"]')]
					.map((el, index) => [el, index])
					.filter(el => el[0].checked)
					.map(el => el[1]);

			if (data['weekdays'].length === 0) {
				type_buttons.weekday_bar.classList.add('error-input');
				type_buttons.weekday_bar.title = 'No day of the week is selected';
				return;
			};
		};

		fetch_data.url = `${url_prefix}/api/reminders?api_key=${api_key}`;
		fetch_data.method = 'POST';
		fetch_data.call_back = () => fillLibrary(Types.reminder);

	} else if (cl.contains('show-add-template')) {
		// Add template
		fetch_data.url = `${url_prefix}/api/templates?api_key=${api_key}`;
		fetch_data.method = 'POST';
		fetch_data.call_back = () => {
			loadTemplateSelection();
			fillLibrary(Types.template);
		};

	} else if (cl.contains('show-add-static-reminder')) {
		// Add static reminder
		fetch_data.url = `${url_prefix}/api/staticreminders?api_key=${api_key}`;
		fetch_data.method = 'POST';
		fetch_data.call_back = () => fillLibrary(Types.static_reminder);
		
	} else if (cl.contains('show-edit-reminder')) {
		// Edit reminder
		data['time'] =
			(new Date(inputs.time.value) / 1000)
			+ (new Date(inputs.time.value).getTimezoneOffset() * 60);

		if (type_buttons.repeat_button.dataset.selected === 'true') {
			data['repeat_quantity'] = type_buttons.repeat_quantity.value;
			data['repeat_interval'] = parseInt(type_buttons.repeat_interval.value)

		} else if (type_buttons.weekday_button.dataset.selected === 'true') {
			data['weekdays'] = 
				[...document.querySelectorAll('.weekday-bar > input[type="checkbox"]')]
					.map((el, index) => [el, index])
					.filter(el => el[0].checked)
					.map(el => el[1]);

			if (data['weekdays'].length === 0) {
				type_buttons.weekday_bar.classList.add('error-input');
				type_buttons.weekday_bar.title = 'No day of the week is selected';
				return;
			};
		};

		fetch_data.url = `${url_prefix}/api/reminders/${e_id}?api_key=${api_key}`;
		fetch_data.method = 'PUT';
		fetch_data.call_back = () => fillLibrary(Types.reminder);

	} else if (cl.contains('show-edit-template')) {
		// Edit template
		fetch_data.url = `${url_prefix}/api/templates/${e_id}?api_key=${api_key}`;
		fetch_data.method = 'PUT';
		fetch_data.call_back = () => {
			loadTemplateSelection();
			fillLibrary(Types.template);
		};

	} else if (cl.contains('show-edit-static-reminder')) {
		// Edit a static reminder
		fetch_data.url = `${url_prefix}/api/staticreminders/${e_id}?api_key=${api_key}`;
		fetch_data.method = 'PUT';
		fetch_data.call_back = () => fillLibrary(Types.static_reminder);
		
	} else return;
	
	fetch(fetch_data.url, {
		'method': fetch_data.method,
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);

		fetch_data.call_back()
		showWindow("home");
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = `${url_prefix}/`;
		} else if (e === 400) {
			inputs.time.classList.add('error-input');
			inputs.time.title = 'Time is in the past';
		} else
			console.log(e);
	});
};

// code run on load

fillColors();

document.querySelector('#template-selection').onchange = e => applyTemplate();
document.querySelector('#normal-button').onclick = e => toggleNormal();
document.querySelector('#repeat-button').onclick = e => toggleRepeated();
document.querySelector('#weekday-button').onclick = e => toggleWeekDay();
document.querySelector('#close-info').onclick = e => showWindow("home");
document.querySelector('#delete-info').onclick = e => deleteInfo();
document.querySelector('#test-reminder').onclick = e => testReminder();
document.querySelector('#info-form').action = 'javascript:submitInfo();';