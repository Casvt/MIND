const inputs = {
	'title': document.getElementById('title-input'),
	'time': document.getElementById('time-input'),
	'notification_service': document.getElementById('notification-service-input'),
	'text': document.getElementById('text-input')
};

function addReminder() {
	const data = {
		'title': inputs.title.value,
		'time': new Date(inputs.time.value).getTime() / 1000,
		'notification_service': inputs.notification_service.value,
		'text': inputs.text.value
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
		} else {
			console.log(e);
		};
	});
};

function showAdd() {
	if (document.getElementById('no-service-error').classList.contains('hidden')) {
		showWindow('add');
	};
};

function closeAdd() {
	hideWindow();
	setTimeout(() => {
		inputs.title.value = '';
		inputs.time.value = '';
		inputs.notification_service.value = document.querySelector('#notification-service-input option[selected]').value;
		inputs.text.value = '';
	}, 500);
};

// code run on load

document.getElementById('add-form').setAttribute('action', 'javascript:addReminder();');
document.getElementById('close-add').addEventListener('click', e => closeAdd());
