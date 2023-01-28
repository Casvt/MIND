const colors = ["#3c3c3c", "#49191e", "#171a42", "#083b06", "#3b3506", "#300e40"];
const inputs = {
	'title': document.getElementById('title-input'),
	'time': document.getElementById('time-input'),
	'notification_service': document.getElementById('notification-service-input'),
	'text': document.getElementById('text-input'),
	'color': document.querySelector('#add .color-list')
};

const type_buttons = {
	'normal-button': document.getElementById('normal-button'),
	'repeat-button': document.getElementById('repeat-button'),
	
	'repeat-bar': document.querySelector('.repeat-bar'),
	'repeat-interval': document.getElementById('repeat-interval'),
	'repeat-quantity': document.getElementById('repeat-quantity')
};

function addReminder() {
	inputs.time.classList.remove('error-input');
	inputs.time.removeAttribute('title');
	
	const data = {
		'title': inputs.title.value,
		'time': (new Date(inputs.time.value) / 1000) + (new Date(inputs.time.value).getTimezoneOffset() * 60),
		'notification_service': inputs.notification_service.value,
		'text': inputs.text.value,
		'color': null
	};
	if (!inputs.color.classList.contains('hidden')) {
		data['color'] = inputs.color.querySelector('button[data-selected="true"]').dataset.color;
	};
	if (type_buttons['repeat-button'].dataset.selected === 'true') {
		data['repeat_quantity'] = type_buttons['repeat-quantity'].value;
		data['repeat_interval'] = type_buttons['repeat-interval'].value
	};

	fetch(`/api/reminders?api_key=${api_key}`, {
		'method': 'POST',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};

		fillList();
		closeAdd();
		return
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		} else if (e === 400) {
			inputs.time.classList.add('error-input');
			inputs.time.title = 'Time is in the past';
		} else {
			console.log(e);
		};
	});
};

function showAdd() {
	if (!document.getElementById('add-entry').classList.contains('error')) {
		loadTemplates(force=false);
		showWindow('add');
	} else {
		showWindow('notification');
	};
};

function closeAdd() {
	hideWindow();
	setTimeout(() => {
		document.getElementById('template-selection').value = document.querySelector('#template-selection option[selected]').value;
		if (!inputs.color.classList.contains('hidden')) {
			toggleColor(inputs.color);
		};
		inputs.title.value = '';
		inputs.time.value = '';
		inputs.notification_service.value = document.querySelector('#notification-service-input option[selected]').value;
		toggleNormal();
		inputs.text.value = '';
		document.getElementById('test-reminder').classList.remove('show-sent');
	}, 500);
};

function loadColor() {
	document.querySelectorAll('.color-list').forEach(list => {
		colors.forEach(color => {
			const entry = document.createElement('button');
			entry.dataset.color = color;
			entry.title = color;
			entry.type = 'button';
			entry.style.setProperty('--color', color);
			entry.addEventListener('click', e => selectColor(list, color))
			list.appendChild(entry);
		});
	});
};

function selectColor(list, color_code) {
	list.querySelector(`button[data-color="${color_code}"]`).dataset.selected = 'true';
	list.querySelectorAll(`button:not([data-color="${color_code}"])`).forEach(b => b.dataset.selected = 'false');
	return;
}

function toggleColor(list) {
	selectColor(list, colors[0]);
	list.classList.toggle('hidden');
}

function toggleNormal() {
	type_buttons['normal-button'].dataset.selected = 'true';
	type_buttons['repeat-button'].dataset.selected = 'false';

	type_buttons['repeat-bar'].classList.add('hidden');
	type_buttons['repeat-interval'].removeAttribute('required');
	type_buttons['repeat-interval'].value = '';
};

function toggleRepeated() {
	type_buttons['normal-button'].dataset.selected = 'false';
	type_buttons['repeat-button'].dataset.selected = 'true';

	type_buttons['repeat-bar'].classList.remove('hidden');
	type_buttons['repeat-interval'].setAttribute('required', '');
};

function testReminder() {
	const input = document.getElementById('test-reminder');
	if (inputs.title.value === '') {
		input.classList.add('error-input');
		input.title = 'No title set';
		return
	} else {
		input.classList.remove('error-input');
		input.removeAttribute('title');
	};
	const data = {
		'title': inputs.title.value,
		'notification_service': inputs.notification_service.value,
		'text': inputs.text.value
	};
	fetch(`/api/reminders/test?api_key=${api_key}`, {
		'method': 'POST',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		input.classList.add('show-sent');		
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		};
	});
};

// code run on load

document.getElementById('add-form').setAttribute('action', 'javascript:addReminder();');
document.getElementById('template-selection').addEventListener('change', e => loadTemplate());
document.getElementById('color-toggle').addEventListener('click', e => toggleColor(inputs.color));
document.getElementById('normal-button').addEventListener('click', e => toggleNormal());
document.getElementById('repeat-button').addEventListener('click', e => toggleRepeated());
document.getElementById('close-add').addEventListener('click', e => closeAdd());
document.getElementById('test-reminder').addEventListener('click', e => testReminder());

loadColor();
