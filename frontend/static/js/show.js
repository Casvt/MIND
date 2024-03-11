function showAdd(type) {
	const default_service = getLocalStorage('default_service')['default_service'];
	inputs.template.value = '0';
	inputs.title.value = '';
	inputs.text.value = '';
	inputs.time.value = '';
	inputs.notification_service.querySelectorAll('input[type="checkbox"]')
		.forEach(c => c.checked = false);
	inputs.notification_service.querySelector(
		`input[type="checkbox"][data-id="${default_service}"]`
	).checked = true;
	document.querySelectorAll('.weekday-bar > input[type="checkbox"]')
		.forEach(el => el.checked = false);
	toggleNormal();
	selectColor(colors[0]);
	inputs.color_toggle.checked = false;
	document.getElementById('test-reminder').classList.remove('show-sent');

	const cl = document.getElementById('info').classList;
	cl.forEach(c => {
		if (InfoClasses.includes(c)) cl.remove(c)
	});
	document.querySelector('.options > button[type="submit"]').innerText = 'Add';
	
	document.querySelector('#test-reminder > div:first-child').innerText = 'Test';
	const title = document.querySelector('#info h2');
	if (type === Types.reminder) {
		cl.add('show-add-reminder');
		title.innerText = 'Add a reminder';
		inputs.time.setAttribute('required', '');
	} else if (type === Types.template) {
		cl.add('show-add-template');
		title.innerText = 'Add a template';
		inputs.time.removeAttribute('required');
	} else if (type === Types.static_reminder) {
		cl.add('show-add-static-reminder');
		title.innerText = 'Add a static reminder';
		inputs.time.removeAttribute('required');
	} else
		return;
	showWindow('info');
};

function showEdit(id, type) {
	let url;
	if (type === Types.reminder) {
		url = `${url_prefix}/api/reminders/${id}?api_key=${api_key}`;
		inputs.time.setAttribute('required', '');
	} else if (type === Types.template) {
		url = `${url_prefix}/api/templates/${id}?api_key=${api_key}`;
		inputs.time.removeAttribute('required');
		type_buttons.repeat_interval.removeAttribute('required');
	} else if (type === Types.static_reminder) {
		url = `${url_prefix}/api/staticreminders/${id}?api_key=${api_key}`;
		document.getElementById('test-reminder').classList.remove('show-sent');
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
		inputs.color_toggle.checked = false;
		selectColor(json.result.color || colors[0]);
		inputs.title.value = json.result.title;

		if (type === Types.reminder) {
			var trigger_date = new Date(
				(json.result.time
					+ new Date(json.result.time * 1000).getTimezoneOffset()
					* -60
				) * 1000
			);
			inputs.time.value = 
				trigger_date.toLocaleString('en-CA').slice(0,10)
				+ 'T'
				+ trigger_date.toTimeString().slice(0,5);
		};
		inputs.notification_service.querySelectorAll('input[type="checkbox"]').forEach(
			c => c.checked = json.result.notification_services.includes(parseInt(c.dataset.id))
		);

		if (type == Types.reminder) {
			if (json.result.repeat_interval !== null) {
				toggleRepeated();
				type_buttons.repeat_interval.value = json.result.repeat_interval;
				type_buttons.repeat_quantity.value = json.result.repeat_quantity;
			}
			else if (json.result.weekdays !== null) {
				toggleWeekDay();
				[...document.querySelectorAll('.weekday-bar > input[type="checkbox"]')]
					.map((el, index) => [el, index])
					.forEach(el => el[0].checked = json.result.weekdays.includes(el[1]))
			} else
				toggleNormal();
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
		if (InfoClasses.includes(c)) cl.remove(c)
	});
	document.querySelector('.options > button[type="submit"]').innerText = 'Save';
	const title = document.querySelector('#info h2');
	const test_text = document.querySelector('#test-reminder > div:first-child');
	if (type === Types.reminder) {
		cl.add('show-edit-reminder');
		title.innerText = 'Edit a reminder';
		test_text.innerText = 'Test';
	} else if (type === Types.template) {
		cl.add('show-edit-template');
		title.innerText = 'Edit a template';
		test_text.innerText = 'Test';
	} else if (type === Types.static_reminder) {
		cl.add('show-edit-static-reminder');
		title.innerText = 'Edit a static reminder';
		test_text.innerText = 'Trigger';
	} else
		return;
};