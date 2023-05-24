function showAdd(type) {
	inputs.template.value = '0';
	inputs.title.value = '';
	inputs.text.value = '';
	inputs.time.value = '';
	inputs.notification_service.value = document.querySelector('#notification-service-input option[selected]').value;
	toggleNormal();
	toggleColor(true);

	const cl = document.getElementById('info').classList;
	cl.forEach(c => {
		if (info_classes.includes(c)) cl.remove(c)
	});
	document.querySelector('.options > button[type="submit"]').innerText = 'Add';
	if (type === types.reminder) {
		cl.add('show-add-reminder');
		document.querySelector('#info h2').innerText = 'Add a reminder';
		inputs.time.setAttribute('required', '');
	} else if (type === types.template) {
		cl.add('show-add-template');
		document.querySelector('#info h2').innerText = 'Add a template';
		inputs.time.removeAttribute('required');
	} else
		return;
	showWindow('info');
};

function showEdit(id, type) {
	let url;
	if (type === types.reminder) {
		url = `${url_prefix}/api/reminders/${id}?api_key=${api_key}`;
		inputs.time.setAttribute('required', '');
	} else if (type === types.template) {
		url = `${url_prefix}/api/templates/${id}?api_key=${api_key}`;
		inputs.time.removeAttribute('required');
		type_buttons.repeat_interval.removeAttribute('required');
	} else return;
	
	fetch(url)
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);
		return response.json();
	})
	.then(json => {
		document.getElementById('info').dataset.id = id;
		if (json.result.color !== null) {
			if (inputs.color.classList.contains('hidden')) {
				toggleColor();
			};
			selectColor(json.result['color']);
		};

		inputs.title.value = json.result.title;

		if (type === types.reminder) {
			var trigger_date = new Date(
				(json.result.time + new Date(json.result.time * 1000).getTimezoneOffset() * -60) * 1000
			);
			inputs.time.value = trigger_date.toLocaleString('en-CA').slice(0,10) + 'T' + trigger_date.toTimeString().slice(0,5);
		};
		inputs.notification_service.value = json.result.notification_service;

		if (type == types.reminder) {
			if (json.result.repeat_interval === null) {
				toggleNormal();
			} else {
				toggleRepeated();
				type_buttons.repeat_interval.value = json.result.repeat_interval;
				type_buttons.repeat_quantity.value = json.result.repeat_quantity;
			};
		};

		inputs.text.value = json.result.text;
		
		showWindow('info');
	})
	.catch(e => {
		if (e === 401) 
			window.location.href = `${url_prefix}/`;
		else 
			console.log(e);
	});
	
	const cl = document.getElementById('info').classList;
	cl.forEach(c => {
		if (info_classes.includes(c)) cl.remove(c)
	});
	document.querySelector('.options > button[type="submit"]').innerText = 'Save';
	if (type === types.reminder) {
		cl.add('show-edit-reminder');
		document.querySelector('#info h2').innerText = 'Edit a reminder';
	} else if (type === types.template) {
		cl.add('show-edit-template');
		document.querySelector('#info h2').innerText = 'Edit a template';
	} else
		return;
};

// code run on load

document.getElementById('add-reminder').addEventListener('click', e => showAdd(types.reminder));
document.getElementById('add-template').addEventListener('click', e => showAdd(types.template));
