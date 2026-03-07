const NotiEls = {
	services_list: document.querySelector('#services-list'),
	search_input: document.querySelector('#ns-search-input'),
	service_list: document.querySelector('#service-list'),
	default_service_input: document.querySelector('#default-service-input'),
	service_selection: document.querySelector('.notification-service-selection'),
	notification_service_row: document.querySelector('.element-storage .notification-service-row'),
	add_service_window: document.querySelector('#add-service-window'),
	triggers: {
		add_service: document.querySelector('#add-service-toggle'),
		service_list: document.querySelector('#service-list-toggle')
	},
	windows: {
		editService: {
			dialog: document.querySelector("#edit-ns-dialog"),
			form: document.querySelector("#edit-ns-form"),
			close: document.querySelector("#close-edit-ns"),
			inputContainers: {
				url: document.querySelector("#edit-ns-form .checked-input-container:has(#edit-ns-url-input)")
			},
			inputs: {
				title: document.querySelector("#edit-ns-title-input"),
				url: document.querySelector("#edit-ns-url-input")
			},
			error: document.querySelector("#edit-ns-url-error")
		},
		deleteService: {
			dialog: document.querySelector("#delete-ns-dialog"),
			error: document.querySelector("#delete-ns-error"),
			close: document.querySelector("#close-delete-ns"),
			confirm: document.querySelector("#confirm-delete-ns")
		}
	}
};

//
// Fill lists and tables
//
function fillNotificationTable(json) {
	NotiEls.services_list.querySelectorAll("tr[data-id]").forEach(
		e => e.remove()
	)
	json.result.forEach(service => {
		const entry = NotiEls.notification_service_row.cloneNode(true)
		entry.dataset.id = service.id

		entry.querySelector('.title-column').innerText = service.title
		entry.querySelector('.url-column').innerText = service.url

		entry.querySelector('button[data-type="edit"]').onclick =
			e => openEditNotificationService(service.id)

		entry.querySelector('button[data-type="delete"]').onclick =
			e => openDeleteNotificationService(service.id)

		NotiEls.services_list.appendChild(entry)
	})
};

function fillNotificationSelection(json) {
	// Default service setting
	NotiEls.default_service_input.innerHTML = '';
	const default_service = getLocalStorage('default_service')['default_service'];
	json.result.forEach(service => {
		const entry = document.createElement('option');
		entry.value = service.id;
		entry.innerText = service.title;
		if (default_service === service.id)
			entry.setAttribute('selected', '');
		NotiEls.default_service_input.appendChild(entry);
	});

	if (!NotiEls.default_service_input.querySelector(`option[value="${default_service}"]`))
		setLocalStorage({'default_service':
			parseInt(NotiEls.default_service_input.querySelector('option')?.value)
			|| null
		});

	// Selection when managing (static)reminders/templates
	NotiEls.service_selection.innerHTML = '';
	json.result.forEach(service => {
		const entry = document.createElement('div');

		const select = document.createElement('input');
		select.dataset.id = service.id;
		select.type = 'checkbox';
		entry.appendChild(select);

		const title = document.createElement('p');
		title.innerText = service.title;
		entry.appendChild(title);

		NotiEls.service_selection.appendChild(entry);
	});
	if (json.result.length > 0)
		NotiEls.service_selection.querySelector(':first-child input').checked = true;
};

function setNoNotificationServiceMsg(json) {
	if (json.result.length > 0) {
		LibEls.tab_container.querySelectorAll('.add-entry').forEach(ae => {
			ae.classList.remove('error', 'error-icon');
			if (ae.id === 'add-reminder')
				ae.onclick = e => showAdd(reminderTypes.reminder);
			else if (ae.id === 'add-static-reminder')
				ae.onclick = e => showAdd(reminderTypes.static_reminder);
			else if (ae.id === 'add-template')
				ae.onclick = e => showAdd(reminderTypes.template);
		});

	} else {
		LibEls.tab_container.querySelectorAll('.add-entry').forEach(ae => {
			ae.classList.add('error', 'error-icon');
			ae.onclick = e => showWindow('notification');
		});
	};
};

function fillNotificationServices() {
	fetch(`${urlPrefix}/api/notificationservices?api_key=${apiKey}`)
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);
		return response.json();
	})
	.then(json => {
		fillNotificationTable(json);
		fillNotificationSelection(json);
		setNoNotificationServiceMsg(json);
	})
	.catch(e => {
		if (e === 401)
			window.location.href = `${urlPrefix}/`;
		else
			console.log(e);
	});
};

//
// Actions for table
//
function openEditNotificationService(serviceId) {
	NotiEls.windows.editService.dialog.dataset.id = serviceId;
	const row = NotiEls.services_list.querySelector(`tr[data-id="${serviceId}"]`);
	NotiEls.windows.editService.inputs.title.value = row.querySelector('.title-column').innerText;
	NotiEls.windows.editService.inputs.url.value = row.querySelector('.url-column').innerText;
	NotiEls.windows.editService.inputContainers.url.classList.remove('error-input-container');
	NotiEls.windows.editService.dialog.showModal();
};

function editNotificationService() {
	NotiEls.windows.editService.inputContainers.url.classList.remove('error-input-container')
	const data = {
		title: NotiEls.windows.editService.inputs.title.value,
		url: NotiEls.windows.editService.inputs.url.value
	}

	const id = parseInt(NotiEls.windows.editService.dialog.dataset.id)
	sendAPI("PUT", `/notificationservices/${id}`, {}, data)
	.then(json => {
		fillNotificationServices()
		NotiEls.windows.editService.dialog.close()
	})
	.catch(e => {
		e.json().then(json => {
			if (json.error === "URLInvalid" || json.error === "InvalidKeyValue") {
				NotiEls.windows.editService.error.innerText = json.result.reason || "Syntax of URL invalid"
				hide([], [NotiEls.windows.editService.error])
				NotiEls.windows.editService.inputContainers.url.classList.add('error-input-container')
			}
			else
				console.log(json)
		})
	})
}

function openDeleteNotificationService(serviceId) {
	NotiEls.windows.deleteService.dialog.dataset.id = serviceId
	NotiEls.windows.deleteService.error.classList.add("hidden")
	NotiEls.windows.deleteService.confirm.innerText = "Delete"
	NotiEls.windows.deleteService.confirm.onclick = e => deleteService()
	NotiEls.windows.deleteService.dialog.showModal()
}

function deleteService(delete_reminders_using=false) {
	const id = parseInt(NotiEls.windows.deleteService.dialog.dataset.id)
	sendAPI("DELETE", `/notificationservices/${id}`, {delete_reminders_using: delete_reminders_using})
	.then(json => {
		NotiEls.windows.deleteService.error.classList.add('hidden')
		fillNotificationServices()
		if (delete_reminders_using) {
			fillLibrary(reminderTypes.reminder)
			fillLibrary(reminderTypes.static_reminder)
			fillLibrary(reminderTypes.template)
		}
		NotiEls.windows.deleteService.dialog.close()
	})
	.catch(e => {
		e.json().then(json => {
			if (json.error === 'NotificationServiceInUse') {
				NotiEls.windows.deleteService.error.innerText =
					`The notification service is still in use by a ${json.result.reminder_type.toLowerCase()}. Do you want to delete all ${json.result.reminder_type.toLowerCase()}s that are using the notification service?`
				NotiEls.windows.deleteService.error.classList.remove('hidden')
				NotiEls.windows.deleteService.confirm.innerText = "Delete Anyway"
				NotiEls.windows.deleteService.confirm.onclick = e => deleteService(delete_reminders_using=true)
			}
			else
				console.log(json)
		})
	})
}

//
// Adding a service
//
function showServiceList(e) {
	if (!e.target.checked)
		return;

	NotiEls.triggers.add_service.checked = false;

	if (notification_services !== null)
		return;

	fetch(`${urlPrefix}/api/notificationservices/available?api_key=${apiKey}`)
	.then(response => response.json())
	.then(json => {
		notification_services = json.result;
		json.result.forEach((result, index) => {
			const entry = document.createElement('button');
			entry.innerText = result.name;
			entry.onclick = e => showAddServiceWindow(index);
			entry.style.viewTransitionName = `ns-${index}`;
			NotiEls.service_list.appendChild(entry);
		});
	});
};

function searchServiceList() {
	if (autoSearchTimerNs !== null)
		clearTimeout(autoSearchTimerNs)

	const f = () => {
		const query = NotiEls.search_input.value
			.toLowerCase()
			.replace('-', '')
			.replace('_', '')
			.replace(' ', '');
	
		if (query === '')
			NotiEls.service_list.querySelectorAll('button').forEach(
				e => e.classList.remove('hidden')
			);
	
		else
			NotiEls.service_list.querySelectorAll('button').forEach(
				e => e.classList.toggle(
					'hidden',
					!e.innerText
						.toLowerCase()
						.replace('-', '')
						.replace('_', '')
						.replace(' ', '')
						.includes(query)
				)
			);
	};
	
	if (!document.startViewTransition)
		f();
	else
		document.startViewTransition(f);
};

function createTitle() {
	const service_title = document.createElement('input');
	service_title.classList.add('input-style');
	service_title.id = 'service-title';
	service_title.type = 'text';
	service_title.placeholder = 'Service Title';
	service_title.required = true;
	return service_title;
};

function createChoice(token) {
	const choice = document.createElement('select');
	choice.classList.add('input-style');
	choice.dataset.map = token.map_to || '';
	choice.dataset.prefix = '';
	if (![null, undefined, ''].includes(token.default))
		choice.dataset.default = token.default
	else
		choice.dataset.default = ''
	choice.placeholder = token.name;
	choice.required = token.required;
	token.options.forEach(option => {
		const entry = document.createElement('option');
		entry.value = option;
		entry.innerText = option;
		choice.appendChild(entry);
	});
	if (![null, undefined, ''].includes(token.default))
		choice.querySelector(`option[value="${token.default}"]`).setAttribute('selected', '');

	return choice;
};

function createString(token) {
	const str_input = document.createElement('input');
	str_input.classList.add('input-style');
	str_input.dataset.map = token.map_to || '';
	str_input.dataset.prefix = token.prefix || '';
	str_input.dataset.regex = token.regex || '';
	str_input.dataset.default = token.default || '';
	str_input.type = 'text';
	str_input.placeholder = `${token.name}${!token.required ? ' (Optional)' : ''}`;
	str_input.required = token.required;
	return str_input;
};

function createInt(token) {
	const int_input = document.createElement('input');
	int_input.classList.add('input-style');
	int_input.dataset.map = token.map_to || '';
	int_input.dataset.prefix = token.prefix || '';
	if (![null, undefined, ''].includes(token.default))
		int_input.dataset.default = token.default
	else
		int_input.dataset.default = ''	
	int_input.type = 'number';
	int_input.placeholder = `${token.name}${!token.required ? ' (Optional)' : ''}`;
	int_input.required = token.required;
	if (token.min !== null)
		int_input.min = token.min;
	if (token.max !== null)
		int_input.max = token.max;
	return int_input;
};

function createFloat(token) {
	const float_input = document.createElement('input');
	float_input.classList.add('input-style');
	float_input.dataset.map = token.map_to || '';
	float_input.dataset.prefix = token.prefix || '';
	if (![null, undefined, ''].includes(token.default))
		float_input.dataset.default = token.default
	else
		float_input.dataset.default = ''
	float_input.type = 'number';
	float_input.step = 0.1;
	float_input.placeholder = `${token.name}${!token.required ? ' (Optional)' : ''}`;
	float_input.required = token.required;
	if (token.min !== null)
		float_input.min = token.min;
	if (token.max !== null)
		float_input.max = token.max;
	return float_input;
};

function createBool(token) {
	const bool_input = document.createElement('select');
	bool_input.classList.add('input-style');
	bool_input.dataset.map = token.map_to || '';
	bool_input.dataset.prefix = '';
	if (![null, undefined, ''].includes(token.default))
		bool_input.dataset.default = token.default
	else
		bool_input.dataset.default = ''
	bool_input.placeholder = token.name;
	bool_input.required = token.required;
	[['Yes', 'true'], ['No', 'false']].forEach(option => {
		const entry = document.createElement('option');
		entry.value = option[1];
		entry.innerText = option[0];
		bool_input.appendChild(entry);
	});
	bool_input.querySelector(`option[value="${token.default}"]`).setAttribute('selected', '');

	return bool_input;
};

function createEntriesList(token) {
	const entries_list = document.createElement('div');
	entries_list.classList.add('entries-list');
	entries_list.dataset.map = token.map_to || '';
	entries_list.dataset.delim = token.delim || '';
	entries_list.dataset.prefix = token.prefix || '';

	const entries_desc = document.createElement('p');
	entries_desc.innerText = token.name;
	entries_list.appendChild(entries_desc);

	const entries = document.createElement('div');
	entries.classList.add('input-entries');
	entries_list.appendChild(entries);

	const add_row = document.createElement('div');
	add_row.classList.add('add-row', 'hidden');
	const add_input = document.createElement('input');
	add_input.classList.add('input-style');
	add_input.type = 'text';
	add_input.onkeydown = e => {
		if (e.key === "Enter") {
			e.preventDefault();
			e.stopImmediatePropagation();
			addEntry(entries_list);
		};
	};
	add_row.appendChild(add_input);
	const add_entry_button = document.createElement('button');
	add_entry_button.classList.add('input-style');
	add_entry_button.type = 'button';
	add_entry_button.innerText = 'Add';
	add_entry_button.onclick = e => addEntry(entries_list);
	add_row.appendChild(add_entry_button);
	entries_list.appendChild(add_row);

	const add_button = document.createElement('button');
	add_button.classList.add('input-style');
	add_button.type = 'button';
	add_button.innerHTML = icons.add;
	add_button.onclick = e => toggleAddRow(add_row);
	entries_list.appendChild(add_button);

	return entries_list;
};

function toggleAddRow(row) {
	if (row.classList.contains('hidden')) {
		// Show row
		const add_input = row.querySelector('input');
		add_input.value = '';
		row.classList.remove('hidden');
		add_input.focus();
	} else {
		// Hide row
		row.classList.add('hidden');
	};
};

function addEntry(entries_list) {
	const value = entries_list.querySelector('.add-row > input').value;
	const entry = document.createElement('div');
	entry.innerText = value;
	entries_list.querySelector('.input-entries').appendChild(entry);
	toggleAddRow(entries_list.querySelector('.add-row'));
};

function showAddServiceWindow(index) {
	const window = NotiEls.add_service_window;
	window.innerHTML = '';
	window.dataset.index = index;

	const data = notification_services[index];
	console.log(data);

	const title = document.createElement('h3');
	title.innerText = data.name;
	window.appendChild(title);

	if (data.doc_url) {
		const docs = document.createElement('a');
		docs.href = data.doc_url;
		docs.target = '_blank';
		docs.innerText = 'Documentation';
		window.appendChild(docs);
	}

	window.appendChild(createTitle());

	[[data.details.tokens, 'tokens'], [data.details.args, 'args']].forEach(vars => {
		if (vars[1] === 'args' && vars[0].length > 0) {
			// The args are hidden behind a "Show Advanced Settings" button
			const show_args = document.createElement('button');
			show_args.classList.add('input-style');
			show_args.type = 'button';
			show_args.innerText = 'Show Advanced Settings';
			show_args.onclick = e => {
				window.querySelectorAll('[data-is_arg="true"]').forEach(el => el.classList.toggle('hidden'));
				show_args.innerText = show_args.innerText === 'Show Advanced Settings' ? 'Hide Advanced Settings' : 'Show Advanced Settings';
			};
			window.appendChild(show_args);
		};

		vars[0].forEach(token => {
			let result = null;
			if (token.type === 'choice') {
				const desc = document.createElement('p');
				desc.innerText = `${token.name}${!token.required ? ' (Optional)' : ''}`;
				desc.dataset.is_arg = vars[1] === 'args';
				window.appendChild(desc);
				result = createChoice(token);

			} else if (token.type === 'list') {
				const joint_list = document.createElement('div');
				joint_list.dataset.map = token.map_to;
				joint_list.dataset.delim = token.delim;

				const desc = document.createElement('p');
				desc.innerText = `${token.name}${!token.required ? ' (Optional)' : ''}`;
				joint_list.appendChild(desc);

				if (token.content.length === 0)
					joint_list.appendChild(createEntriesList(token));
				else
					token.content.forEach(content =>
						joint_list.appendChild(createEntriesList(content))
					);

				result = joint_list;

			} else if (token.type === 'string')
				result = createString(token);
			else if (token.type === 'int')
				result = createInt(token);
			else if (token.type === 'float')
				result = createFloat(token);
			else if (token.type === 'bool') {
				const desc = document.createElement('p');
				desc.innerText = `${token.name}${!token.required ? ' (Optional)' : ''}`;
				desc.dataset.is_arg = vars[1] === 'args';
				window.appendChild(desc);
				result = createBool(token);
			};

			result.dataset.is_arg = vars[1] === 'args';
			window.appendChild(result);
		});

		if (vars[1] === 'args' && vars[0].length > 0)
			window.querySelectorAll('[data-is_arg="true"]').forEach(
				el => el.classList.toggle('hidden')
			);
	})

	// Bottom options
	const options = document.createElement('div');
	options.classList.add('options');

	const cancel = document.createElement('button');
	cancel.classList.add('input-style');
	cancel.type = 'button';
	cancel.innerText = 'Cancel';
	cancel.onclick = e => NotiEls.triggers.add_service.checked = false;
	options.appendChild(cancel);

	const test = document.createElement('button');
	test.classList.add('input-style');
	test.id = 'test-service';
	test.type = 'button';
	test.onclick = e => testService();
	options.appendChild(test);
	const test_text = document.createElement('div');
	test_text.innerText = 'Test';
	test.appendChild(test_text);
	const test_sent_text = document.createElement('div');
	test_sent_text.innerText = 'Sent';
	test.appendChild(test_sent_text);

	const add = document.createElement('button');
	add.classList.add('input-style');
	add.type = 'submit';
	add.innerText = 'Add';
	options.appendChild(add);
	window.appendChild(options);

	NotiEls.triggers.add_service.checked = true;
};

function buildAppriseURL() {
	const data = notification_services[NotiEls.add_service_window.dataset.index];
	const inputs = NotiEls.add_service_window.querySelectorAll('[data-map][data-is_arg="false"]');
	const values = {};

	// Gather all values and format
	inputs.forEach(i => {
		if (['INPUT', 'SELECT'].includes(i.nodeName)) {
			// Standard input
			let value = `${i.dataset.prefix || ''}${i.value}`;
			if (value)
				values[i.dataset.map] = value;
		} else if (i.nodeName === 'DIV') {
			let value =
				[...i.querySelectorAll('.entries-list')]
				.map(l =>
					[...l.querySelectorAll('.input-entries > div')]
					.map(e => `${l.dataset.prefix || ''}${e.innerText}`)
				)
				.flat()
				.join(i.dataset.delim)

			if (value)
				values[i.dataset.map] = value;
		};
	});

	// Find template(s) that match the given tokens
	const input_keys = Object.keys(values).sort().join();
	const matching_templates = data.details.templates.filter(template =>
		input_keys === template.replaceAll('}', '{').split('{').filter((e, i) => i % 2).sort().join()
	);

	if (!matching_templates.length)
		return null;

	// Build URL with template and values
	let template = matching_templates[0];

	for (const [key, value] of Object.entries(values))
		template = template.replace(`{${key}}`, value);

	// Add args
	const args = [...NotiEls.add_service_window.querySelectorAll('[data-map][data-is_arg="true"]')]
		.map(el => {
			if (['INPUT', 'SELECT'].includes(el.nodeName) && el.value && el.value !== el.dataset.default)
				return `${el.dataset.map}=${el.value}`;
			else if (el.nodeName == 'DIV') {
				let value =
					[...el.querySelectorAll('.entries-list')]
					.map(l =>
						[...l.querySelectorAll('.input-entries > div')]
						.map(e => `${l.dataset.prefix || ''}${e.innerText}`)
					)
					.flat()
					.join(el.dataset.delim)

				if (value)
					return `${el.dataset.map}=${value}`;
			};

			return null;
		})
		.filter(el => el !== null)
		.join('&')
	if (args)
		template += (template.includes('?') ? '&' : '?') + args;
	template = template.replaceAll(' ', '%20');

	console.debug(matching_templates);
	console.debug(template);

	return template;
};

function testService() {
	const test_button = document.querySelector('#test-service');

	// Check regexes for input's
	[...NotiEls.add_service_window.querySelectorAll('input:not([data-regex=""])[data-regex]')]
		.forEach(el => el.classList.remove('error-input'));

	const faulty_inputs =
		[...NotiEls.add_service_window.querySelectorAll('input:not([data-regex=""])[data-regex]')]
			.filter(el =>
				!(
					(!el.required && el.value === '')
					||
					new RegExp(
						el.dataset.regex.split(',').slice(0, el.dataset.regex.split(',').length-1).join(','),
						el.dataset.regex.split(',')[el.dataset.regex.split(',').length-1]
					).test(el.value)
				)
			);
	if (faulty_inputs.length > 0) {
		faulty_inputs.forEach(el => el.classList.add('error-input'));
		return;
	};

	const data = {
		'url': buildAppriseURL()
	};
	if (!data.url) {
		test_button.classList.add('error-input');
		test_button.title = 'Required field missing';
		return;
	};
	fetch(`${urlPrefix}/api/notificationservices/test?api_key=${apiKey}`, {
		'method': 'POST',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);

		test_button.classList.remove('error-input');
		test_button.title = '';
		test_button.classList.add('show-sent');
	})
	.catch(e => {
		if (e === 401)
			window.location.href = `${urlPrefix}/`;
		else if (e === 400) {
			test_button.classList.add('error-input');
			test_button.title = 'Invalid Apprise URL';
		} else
			console.log(e);
	});
};

function addService() {
	const add_button = NotiEls.add_service_window.querySelector('.options > button[type="submit"]');

	// Check regexes for input's
	[...NotiEls.add_service_window.querySelectorAll('input:not([data-regex=""])[data-regex]')]
		.forEach(el => el.classList.remove('error-input'));

	const faulty_inputs =
		[...NotiEls.add_service_window.querySelectorAll('input:not([data-regex=""])[data-regex]')]
			.filter(el =>
				!(
					(!el.required && el.value === '')
					||
					new RegExp(
						el.dataset.regex.split(',').slice(0, el.dataset.regex.split(',').length-1).join(','),
						el.dataset.regex.split(',')[el.dataset.regex.split(',').length-1]
					).test(el.value)
				)
			);
	if (faulty_inputs.length > 0) {
		faulty_inputs.forEach(el => el.classList.add('error-input'));
		return;
	};

	const data = {
		'title': document.querySelector('#service-title').value,
		'url': buildAppriseURL()
	};
	if (!data.url) {
		add_button.classList.add('error-input');
		add_button.title = 'Required field missing';
		return;
	};
	fetch(`${urlPrefix}/api/notificationservices?api_key=${apiKey}`, {
		'method': 'POST',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);

		add_button.classList.remove('error-input');
		add_button.title = '';

		NotiEls.triggers.service_list.checked = false;
		NotiEls.triggers.add_service.checked = false;
		fillNotificationServices();
	})
	.catch(e => {
		if (e === 401)
			window.location.href = `${urlPrefix}/`;
		else if (e === 400) {
			add_button.classList.add('error-input');
			add_button.title = 'Invalid Apprise URL';
		} else
			console.log(e);
	});
};

// code run on load

fillNotificationServices();

let notification_services = null;

NotiEls.triggers.service_list.onchange = showServiceList;
NotiEls.add_service_window.action = 'javascript:addService();';

NotiEls.windows.editService.dialog.onclick = e => {
	if (e.target === e.currentTarget) {
		e.stopPropagation()
		NotiEls.windows.editService.dialog.close();
	}
}
NotiEls.windows.editService.form.action = 'javascript:editNotificationService()'
NotiEls.windows.editService.close.onclick = e => NotiEls.windows.editService.dialog.close();

NotiEls.windows.deleteService.dialog.onclick = e => {
	if (e.target === e.currentTarget) {
		e.stopPropagation()
		NotiEls.windows.deleteService.dialog.close()
	}
}
NotiEls.windows.deleteService.close.onclick = e => NotiEls.windows.deleteService.dialog.close()

var autoSearchTimerNs = null
NotiEls.search_input.oninput = e => {
	if (autoSearchTimerNs !== null)
		clearTimeout(autoSearchTimerNs)

	autoSearchTimerNs = setTimeout(searchServiceList, constants.autoSearchTimeoutNs)
}
