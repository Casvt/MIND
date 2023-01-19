const edit_inputs = {
	'title': document.getElementById('title-edit-input'),
	'time': document.getElementById('time-edit-input'),
	'notification_service': document.getElementById('notification-service-edit-input'),
	'text': document.getElementById('text-edit-input')
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
		'time': new Date(edit_inputs.time.value).getTime() / 1000,
		'notification_service': edit_inputs.notification_service.value,
		'text': edit_inputs.text.value,
		'repeat_quantity': null,
		'repeat_interval': null
	};
	if (edit_type_buttons['repeat-edit-button'].dataset.selected === 'true') {
		data['repeat_quantity'] = edit_type_buttons['repeat-edit-quantity'].value;
		data['repeat_interval'] = edit_type_buttons['repeat-edit-interval'].value;
	};

	fetch(`/api/reminders/${id}?api_key=${api_key}`, {
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
			window.location.href = '/';
		} else {
			console.log(e);
		};
	});
};

function showEdit(id) {
	document.getElementById('edit-form').dataset.id = id;
	fetch(`/api/reminders/${id}?api_key=${api_key}`)
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};

		return response.json();
	})
	.then(json => {
		edit_inputs.title.value = json.result.title;

		edit_inputs.time.value = new Date(
			(json.result.time + new Date(json.result.time * 1000).getTimezoneOffset() * -60) * 1000
		).toISOString().slice(0, 16);
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
			window.location.href = '/';
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

// code run on load

document.getElementById('edit-form').setAttribute('action', 'javascript:editReminder();');
document.getElementById('normal-edit-button').addEventListener('click', e => toggleEditNormal());
document.getElementById('repeat-edit-button').addEventListener('click', e => toggleEditRepeated());
document.getElementById('close-edit').addEventListener('click', e => hideWindow());
