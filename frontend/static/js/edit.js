const edit_inputs = {
	'title': document.getElementById('title-edit-input'),
	'time': document.getElementById('time-edit-input'),
	'notification_service': document.getElementById('notification-service-edit-input'),
	'text': document.getElementById('text-edit-input')
};

function editReminder() {
	const id = document.getElementById('edit-form').dataset.id;
	const data = {
		'title': edit_inputs.title.value,
		'time': new Date(edit_inputs.time.value).getTime() / 1000,
		'notification_service': edit_inputs.notification_service.value,
		'text': edit_inputs.text.value
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

// code run on load

document.getElementById('edit-form').setAttribute('action', 'javascript:editReminder();');
document.getElementById('close-edit').addEventListener('click', e => hideWindow());
