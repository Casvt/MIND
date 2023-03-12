const edit_inputs = {
	'title': document.getElementById('title-edit-input'),
	'time': document.getElementById('time-edit-input'),
	'notification_service': document.getElementById('notification-service-edit-input'),
	'text': document.getElementById('text-edit-input'),
	'color': document.querySelector('#edit .color-list')
};

const edit_type_buttons = {
	'normal-edit-button': document.getElementById('normal-edit-button'),
	'repeat-edit-button': document.getElementById('repeat-edit-button'),
	
	'repeat-edit-bar': document.querySelector('.repeat-edit-bar'),
	'repeat-edit-interval': document.getElementById('repeat-edit-interval'),
	'repeat-edit-quantity': document.getElementById('repeat-edit-quantity')
};

function editReminder() {
	const id = document.getElementById('edit-form').dataset.id;
	const data = {
		'title': edit_inputs.title.value,
		'time': (new Date(edit_inputs.time.value) / 1000) + (new Date(edit_inputs.time.value).getTimezoneOffset() * 60),
		'notification_service': edit_inputs.notification_service.value,
		'text': edit_inputs.text.value,
		'repeat_quantity': null,
		'repeat_interval': null,
		'color': null
	};
	if (!edit_inputs.color.classList.contains('hidden')) {
		data['color'] = edit_inputs.color.querySelector('button[data-selected="true"]').dataset.color;
	};
	if (edit_type_buttons['repeat-edit-button'].dataset.selected === 'true') {
		data['repeat_quantity'] = edit_type_buttons['repeat-edit-quantity'].value;
		data['repeat_interval'] = edit_type_buttons['repeat-edit-interval'].value;
	};

	fetch(`${url_prefix}/api/reminders/${id}?api_key=${api_key}`, {
		'method': 'PUT',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};

		fillList();
		hideWindow();
		return
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = url_prefix;
		} else {
			console.log(e);
		};
	});
};

function showEdit(id) {
	document.getElementById('edit-form').dataset.id = id;
	fetch(`${url_prefix}/api/reminders/${id}?api_key=${api_key}`)
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};

		return response.json();
	})
	.then(json => {
		if (json.result['color'] !== null) {
			if (edit_inputs.color.classList.contains('hidden')) {
				toggleColor(edit_inputs.color);
			};
			selectColor(edit_inputs.color, json.result['color']);
		};

		edit_inputs.title.value = json.result.title;

		var trigger_date = new Date(
			(json.result.time + new Date(json.result.time * 1000).getTimezoneOffset() * -60) * 1000
		);
		edit_inputs.time.value = trigger_date.toLocaleString('en-CA').slice(0,10) + 'T' + trigger_date.toTimeString().slice(0,5);
		edit_inputs.notification_service.value = json.result.notification_service;

		if (json.result['repeat_interval'] === null) {
			toggleEditNormal();
		} else {
			toggleEditRepeated();
			edit_type_buttons['repeat-edit-interval'].value = json.result['repeat_interval'];
			edit_type_buttons['repeat-edit-quantity'].value = json.result['repeat_quantity'];
		};

		edit_inputs.text.value = json.result.text !== null ? json.result.text : '';

		showWindow('edit');
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = url_prefix;
		} else if (e === 404) {
			fillList();
		} else {
			console.log(e);
		};
	});
};

function toggleEditNormal() {
	edit_type_buttons['normal-edit-button'].dataset.selected = 'true';
	edit_type_buttons['repeat-edit-button'].dataset.selected = 'false';

	edit_type_buttons['repeat-edit-bar'].classList.add('hidden');
	edit_type_buttons['repeat-edit-interval'].removeAttribute('required');
	edit_type_buttons['repeat-edit-interval'].value = '';
};

function toggleEditRepeated() {
	edit_type_buttons['normal-edit-button'].dataset.selected = 'false';
	edit_type_buttons['repeat-edit-button'].dataset.selected = 'true';
	
	edit_type_buttons['repeat-edit-bar'].classList.remove('hidden');
	edit_type_buttons['repeat-edit-interval'].setAttribute('required', '');
};

function deleteReminder() {
	const id = document.getElementById('edit-form').dataset.id;
	fetch(`${url_prefix}/api/reminders/${id}?api_key=${api_key}`, {
		'method': 'DELETE'
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};

		fillList();
		hideWindow();
		return;
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = url_prefix;
		} else if (e === 404) {
			fillList();
		} else {
			console.log(e);
		};
	});
};

// code run on load

document.getElementById('edit-form').setAttribute('action', 'javascript:editReminder();');
document.getElementById('color-edit-toggle').addEventListener('click', e => toggleColor(edit_inputs.color));
document.getElementById('normal-edit-button').addEventListener('click', e => toggleEditNormal());
document.getElementById('repeat-edit-button').addEventListener('click', e => toggleEditRepeated());
document.getElementById('close-edit').addEventListener('click', e => hideWindow());
document.getElementById('delete-reminder').addEventListener('click', e => deleteReminder());
