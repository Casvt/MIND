const colors = ["#3c3c3c", "#49191e", "#171a42", "#083b06", "#3b3506", "#300e40"];

const inputs = {
	'template': document.getElementById('template-selection'),
	'title': document.getElementById('title-input'),
	'time': document.getElementById('time-input'),
	'notification_service': document.querySelector('.notification-service-list'),
	'text': document.getElementById('text-input'),
	'color': document.querySelector('.color-list')
};

const type_buttons = {
	'normal_button': document.getElementById('normal-button'),
	'repeat_button': document.getElementById('repeat-button'),
	
	'repeat_bar': document.querySelector('.repeat-bar'),
	'repeat_interval': document.getElementById('repeat-interval'),
	'repeat_quantity': document.getElementById('repeat-quantity')
};

function loadColor() {
	colors.forEach(color => {
		const entry = document.createElement('button');
		entry.dataset.color = color;
		entry.title = color;
		entry.type = 'button';
		entry.style.setProperty('--color', color);
		entry.addEventListener('click', e => selectColor(color))
		inputs.color.appendChild(entry);
	});
};

function selectColor(color_code) {
	inputs.color.querySelector(`button[data-color="${color_code}"]`).dataset.selected = 'true';
	inputs.color.querySelectorAll(`button:not([data-color="${color_code}"])`).forEach(b => b.dataset.selected = 'false');
	return;
};

function toggleColor(hide=false) {
	selectColor(colors[0])
	if (!hide) 
		inputs.color.classList.toggle('hidden');
	else
		inputs.color.classList.add('hidden');
};

function toggleNotificationService(hide=false) {
	if (!hide)
		inputs.notification_service.classList.toggle('hidden');
	else
		inputs.notification_service.classList.add('hidden');
};

function toggleNormal() {
	type_buttons.normal_button.dataset.selected = 'true';
	type_buttons.repeat_button.dataset.selected = 'false';

	type_buttons.repeat_bar.classList.add('hidden');
	type_buttons.repeat_interval.removeAttribute('required');
	type_buttons.repeat_interval.value = '';
};

function toggleRepeated() {
	type_buttons.normal_button.dataset.selected = 'false';
	type_buttons.repeat_button.dataset.selected = 'true';

	type_buttons.repeat_bar.classList.remove('hidden');
	type_buttons.repeat_interval.setAttribute('required', '');
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
			document.querySelectorAll('.notification-service-list input[type="checkbox"]:checked')
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
			fillReminders();
		} else if (cl.contains('show-edit-template')) {
			// Delete template
			fillTemplates();
			loadTemplateSelection();
		} else if (cl.contains('show-edit-static-reminder')) {
			// Delete static reminder
			fillStaticReminders();
		};
		hideWindow();
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
	let fetch_data = {
		url: null,
		method: null,
		call_back: null
	};
	const data = {
		'title': inputs.title.value,
		'notification_services': [...
				document.querySelectorAll('.notification-service-list input[type="checkbox"]:checked')
			].map(c => parseInt(c.dataset.id)),
		'text': inputs.text.value,
		'color': null
	};
	if (!inputs.color.classList.contains('hidden')) {
		data['color'] = inputs.color.querySelector('button[data-selected="true"]').dataset.color;
	};
	
	if (data.notification_services.length === 0) {
		inputs.notification_service.classList.add('error-input');
		inputs.notification_service.title = 'No notification service set';
		return
	};

	const e_id = document.getElementById('info').dataset.id;
	const cl = document.getElementById('info').classList;
	if (cl.contains('show-add-reminder')) {
		// Add reminder
		data['time'] = (new Date(inputs.time.value) / 1000) + (new Date(inputs.time.value).getTimezoneOffset() * 60)
		if (type_buttons.repeat_button.dataset.selected === 'true') {
			data['repeat_quantity'] = type_buttons.repeat_quantity.value;
			data['repeat_interval'] = type_buttons.repeat_interval.value
		};
		fetch_data.url = `${url_prefix}/api/reminders?api_key=${api_key}`;
		fetch_data.method = 'POST';
		fetch_data.call_back = fillReminders;

	} else if (cl.contains('show-add-template')) {
		// Add template
		fetch_data.url = `${url_prefix}/api/templates?api_key=${api_key}`;
		fetch_data.method = 'POST';
		fetch_data.call_back = () => {
			loadTemplateSelection();
			fillTemplates();	
		};

	} else if (cl.contains('show-add-static-reminder')) {
		// Add static reminder
		fetch_data.url = `${url_prefix}/api/staticreminders?api_key=${api_key}`;
		fetch_data.method = 'POST';
		fetch_data.call_back = fillStaticReminders;
		
	} else if (cl.contains('show-edit-reminder')) {
		// Edit reminder
		data['time'] = (new Date(inputs.time.value) / 1000) + (new Date(inputs.time.value).getTimezoneOffset() * 60)
		if (type_buttons.repeat_button.dataset.selected === 'true') {
			data['repeat_quantity'] = type_buttons.repeat_quantity.value;
			data['repeat_interval'] = type_buttons.repeat_interval.value
		};
		fetch_data.url = `${url_prefix}/api/reminders/${e_id}?api_key=${api_key}`;
		fetch_data.method = 'PUT';
		fetch_data.call_back = fillReminders;

	} else if (cl.contains('show-edit-template')) {
		// Edit template
		fetch_data.url = `${url_prefix}/api/templates/${e_id}?api_key=${api_key}`;
		fetch_data.method = 'PUT';
		fetch_data.call_back = () => {
			loadTemplateSelection();
			fillTemplates();
		};

	} else if (cl.contains('show-edit-static-reminder')) {
		// Edit a static reminder
		fetch_data.url = `${url_prefix}/api/staticreminders/${e_id}?api_key=${api_key}`;
		fetch_data.method = 'PUT';
		fetch_data.call_back = fillStaticReminders;
		
	} else return;
	
	fetch(fetch_data.url, {
		'method': fetch_data.method,
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);

		fetch_data.call_back()
		hideWindow();
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

loadColor();

document.getElementById('template-selection').addEventListener('change', e => applyTemplate());
document.getElementById('color-toggle').addEventListener('click', e => toggleColor());
document.getElementById('toggle-notification-service-list').addEventListener('click', e => toggleNotificationService());
document.getElementById('normal-button').addEventListener('click', e => toggleNormal());
document.getElementById('repeat-button').addEventListener('click', e => toggleRepeated());
document.getElementById('close-info').addEventListener('click', e => hideWindow());
document.getElementById('delete-info').addEventListener('click', e => deleteInfo());
document.getElementById('test-reminder').addEventListener('click', e => testReminder());
document.getElementById('info-form').setAttribute('action', 'javascript:submitInfo();');
