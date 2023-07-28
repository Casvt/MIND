function fillNotificationSelection() {
	fetch(`${url_prefix}/api/notificationservices?api_key=${api_key}`)
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);
		return response.json();
	})
	.then(json => {
		if (json.result.length) {
			document.getElementById('add-reminder').classList.remove('error', 'error-icon');

			const default_select = document.querySelector('#default-service-input');
			default_select.innerHTML = '';
			let default_service = getLocalStorage('default_service')['default_service'];
			json.result.forEach(service => {
				const entry = document.createElement('option');
				entry.value = service.id;
				entry.innerText = service.title;
				if (default_service === service.id)
					entry.setAttribute('selected', '');
				default_select.appendChild(entry);
			});
			if (!document.querySelector(`#default-service-input > option[value="${default_service}"]`))
				setLocalStorage({'default_service': 
					parseInt(document.querySelector('#default-service-input > option')?.value)
					|| null
				});
				default_service = getLocalStorage('default_service')['default_service'];

			inputs.notification_service.innerHTML = '';
			json.result.forEach(service => {
				const entry = document.createElement('div');
				
				const select = document.createElement('input');
				select.dataset.id = service.id;
				select.type = 'checkbox';
				entry.appendChild(select);

				const title = document.createElement('p');
				title.innerText = service.title;
				entry.appendChild(title);
				
				inputs.notification_service.appendChild(entry);
			});
			inputs.notification_service.querySelector(':first-child input').checked = true;
			
			const table = document.getElementById('services-list');
			table.innerHTML = '';
			json.result.forEach(service => {
				const entry = document.createElement('tr');
				entry.dataset.id = service.id;
	
				const title_container = document.createElement('td');
				title_container.classList.add('title-column');
				const title = document.createElement('input');
				title.setAttribute('readonly', '');
				title.setAttribute('type', 'text');
				title.value = service.title;
				title_container.appendChild(title);
				entry.appendChild(title_container);
	
				const url_container = document.createElement('td');
				url_container.classList.add('url-column');
				const url = document.createElement('input');
				url.setAttribute('readonly', '');
				url.setAttribute('type', 'text');
				url.value = service.url;
				url.addEventListener('keydown', e => {
					if (e.key === 'Enter')
						saveService(service.id);
				});
				url_container.appendChild(url);
				entry.appendChild(url_container);
				
				const actions = document.createElement('td');
				actions.classList.add('action-column');
				entry.appendChild(actions);
	
				const edit_button = document.createElement('button');
				edit_button.dataset.type = 'edit';
				edit_button.addEventListener('click', e => editService(service.id));
				edit_button.title = 'Edit';
				edit_button.setAttribute('aria-label', 'Edit');
				edit_button.innerHTML = icons.edit;
				actions.appendChild(edit_button);
				
				const save_button = document.createElement('button');
				save_button.dataset.type = 'save';
				save_button.addEventListener('click', e => saveService(service.id));
				save_button.title = 'Save Edits';
				save_button.setAttribute('aria-label', 'Save Edits');
				save_button.innerHTML = icons.save;
				actions.appendChild(save_button);
				
				const delete_button = document.createElement('button');
				delete_button.dataset.type = 'delete';
				delete_button.addEventListener('click', e => deleteService(service.id));
				delete_button.title = 'Delete';
				delete_button.setAttribute('aria-label', 'Delete');
				delete_button.innerHTML = icons.delete;
				actions.appendChild(delete_button);
				
				table.appendChild(entry);
			});	
		} else {
			document.getElementById('add-reminder').classList.add('error', 'error-icon');

			inputs.notification_service.innerHTML = '';

			const default_select = document.querySelector('#default-service-input');
			default_select.innerHTML = '';

			const default_service = getLocalStorage('default_service')['default_service'];
			if (!document.querySelector(`#default-service-input > option[value="${default_service}"]`))
				setLocalStorage({'default_service': 
					parseInt(document.querySelector('#default-service-input > option')?.value)
					|| null
				});
		};
	})
	.catch(e => {
		if (e === 401)
			window.location.href = `${url_prefix}/`;
		else
			console.log(e);
	});
};

function editService(id) {
	document.querySelectorAll(`tr[data-id="${id}"] input`).forEach(e => e.removeAttribute('readonly'));
	document.querySelector(`tr[data-id="${id}"]`).classList.add('edit');
};

function saveService(id) {
	const row = document.querySelector(`tr[data-id="${id}"]`);
	const save_button = row.querySelector('button[data-type="save"]');
	const data = {
		'title': row.querySelector(`td.title-column > input`).value,
		'url': row.querySelector(`td.url-column > input`).value
	};
	fetch(`${url_prefix}/api/notificationservices/${id}?api_key=${api_key}`, {
		'method': 'PUT',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);
		
		fillNotificationSelection();
	})
	.catch(e => {
		if (e === 401)
			window.location.href = `${url_prefix}/`;
		else if (e === 400) {
			save_button.classList.add('error-icon');
			save_button.title = 'Invalid Apprise URL';
			save_button.setAttribute('aria-label', 'Invalid Apprise URL');
		} else
			console.log(e);
	});
};

function deleteService(id) {
	const row = document.querySelector(`tr[data-id="${id}"]`);
	fetch(`${url_prefix}/api/notificationservices/${id}?api_key=${api_key}`, {
		'method': 'DELETE'
	})
	.then(response => response.json())
	.then(json => {
		if (json.error !== null) return Promise.reject(json);
		
		row.remove();
		fillNotificationSelection();
		if (document.querySelectorAll('#services-list > tr').length === 0)
			document.getElementById('add-reminder').classList.add('error', 'error-icon');
	})
	.catch(e => {
		if (e.error === 'ApiKeyExpired' || e.error === 'ApiKeyInvalid')
			window.location.href = `${url_prefix}/`;
		else if (e.error === 'NotificationServiceInUse') {
			const delete_button = row.querySelector('button[title="Delete"]');
			delete_button.classList.add('error-icon');
			delete_button.title = `The notification service is still in use by a ${e.result.type}`;
		} else
			console.log(e);
	});
};

function toggleAddService() {
	const cont = document.querySelector('.overflow-container');
	if (cont.classList.contains('show-add')) {
		// Hide add
		cont.classList.remove('show-add');
		hideAddServiceWindow();
	} else {
		// Show add
		if (notification_services === null) {
			fetch(`${url_prefix}/api/notificationservices/available?api_key=${api_key}`)
			.then(response => response.json())
			.then(json => {
				notification_services = json.result;
				const table = document.querySelector('#service-list');
				json.result.forEach((result, index) => {
					const entry = document.createElement('button');
					entry.innerText = result.name;
					entry.addEventListener('click', e => showAddServiceWindow(index));
					table.appendChild(entry);
				});
			});
		};
		cont.classList.add('show-add');
	};
};

function createTitle() {
	const service_title = document.createElement('input');
	service_title.id = 'service-title';
	service_title.type = 'text';
	service_title.placeholder = 'Service Title';
	service_title.required = true;
	return service_title;
};

function createChoice(token) {
	const choice = document.createElement('select');
	choice.dataset.map = token.map_to || '';
	choice.dataset.prefix = '';
	choice.placeholder = token.name;
	choice.required = token.required;
	token.options.forEach(option => {
		const entry = document.createElement('option');
		entry.value = option;
		entry.innerText = option;
		choice.appendChild(entry);
	});
	if (token.default)
		choice.querySelector(`option[value="${token.default}"]`).setAttribute('selected', '');

	return choice;
};

function createString(token) {
	const str_input = document.createElement('input');
	str_input.dataset.map = token.map_to || '';
	str_input.dataset.prefix = token.prefix || '';
	str_input.dataset.regex = token.regex || '';
	str_input.type = 'text';
	str_input.placeholder = `${token.name}${!token.required ? ' (Optional)' : ''}`;
	str_input.required = token.required;
	return str_input;
};

function createInt(token) {
	const int_input = document.createElement('input');
	int_input.dataset.map = token.map_to || '';
	int_input.dataset.prefix = token.prefix || '';
	int_input.type = 'number';
	int_input.placeholder = `${token.name}${!token.required ? ' (Optional)' : ''}`;
	int_input.required = token.required;
	if (token.min !== null)
		int_input.min = token.min;
	if (token.max !== null)
		int_input.max = token.max;
	return int_input;
};

function createBool(token) {
	const bool_input = document.createElement('select');
	bool_input.dataset.map = token.map_to || '';
	bool_input.dataset.prefix = '';
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
	add_input.type = 'text';
	add_input.addEventListener('keydown', e => {
		if (e.key === "Enter") {
			e.preventDefault();
			e.stopImmediatePropagation();
			addEntry(entries_list);
		};
	});
	add_row.appendChild(add_input);
	const add_entry_button = document.createElement('button');
	add_entry_button.type = 'button';
	add_entry_button.innerText = 'Add';
	add_entry_button.addEventListener('click', e => addEntry(entries_list));
	add_row.appendChild(add_entry_button);
	entries_list.appendChild(add_row);

	const add_button = document.createElement('button');
	add_button.type = 'button';
	add_button.innerHTML = icons.add;
	add_button.addEventListener('click', e => toggleAddRow(add_row));
	entries_list.appendChild(add_button);
	
	return entries_list;
};

function toggleAddRow(row) {
	if (row.classList.contains('hidden')) {
		// Show row
		row.querySelector('input').value = '';
		row.classList.remove('hidden');
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
	const window = document.getElementById('add-service-window');
	window.innerHTML = '';
	window.dataset.index = index;

	const data = notification_services[index];
	console.log(data);
	
	const title = document.createElement('h3');
	title.innerText = data.name;
	window.appendChild(title);

	const docs = document.createElement('a');
	docs.href = data.doc_url;
	docs.target = '_blank';
	docs.innerText = 'Documentation';
	window.appendChild(docs);

	window.appendChild(createTitle());	
	
	[[data.details.tokens, 'tokens'], [data.details.args, 'args']].forEach(vars => {
		if (vars[1] === 'args' && vars[0].length > 0) {
			// The args are hidden behind a "Show Advanced Settings" button
			const show_args = document.createElement('button');
			show_args.type = 'button';
			show_args.innerText = 'Show Advanced Settings';
			show_args.addEventListener('click', e => {
				window.querySelectorAll('[data-is_arg="true"]').forEach(el => el.classList.toggle('hidden'));
				show_args.innerText = show_args.innerText === 'Show Advanced Settings' ? 'Hide Advanced Settings' : 'Show Advanced Settings';
			});
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
			window.querySelectorAll('[data-is_arg="true"]').forEach(el => el.classList.toggle('hidden'));
	})
	
	// Bottom options
	const options = document.createElement('div');
	options.classList.add('options');
	const cancel = document.createElement('button');
	cancel.type = 'button';
	cancel.innerText = 'Cancel';
	cancel.addEventListener('click', e => toggleAddService());
	options.appendChild(cancel);
	const add = document.createElement('button');
	add.type = 'submit';
	add.innerText = 'Add';
	options.appendChild(add);
	window.appendChild(options);
	
	document.getElementById('add-service-container').classList.add('show-add-window');
};

function hideAddServiceWindow() {
	document.getElementById('add-service-container').classList.remove('show-add-window');
};

function buildAppriseURL() {
	const data = notification_services[document.querySelector('#add-service-window').dataset.index];
	const inputs = document.querySelectorAll('#add-service-window > [data-map][data-is_arg="false"]');
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
	const args = [...document.querySelectorAll('#add-service-window > [data-map][data-is_arg="true"]')]
		.map(el => {
			if (['INPUT', 'SELECT'].includes(el.nodeName) && el.value)
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
	template += (template.includes('?') ? '&' : '?') + args;
	template = template.replaceAll(' ', '%20');

	console.debug(matching_templates);
	console.debug(template);

	return template;
};

function addService() {
	const add_button = document.querySelector('#add-service-window > .options > button[type="submit"]');
	const data = {
		'title': document.querySelector('#service-title').value,
		'url': buildAppriseURL()
	};
	if (!data.url) {
		add_button.classList.add('error-input');
		add_button.title = 'Required field missing';
		return;
	}
	fetch(`${url_prefix}/api/notificationservices?api_key=${api_key}`, {
		'method': 'POST',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);
		
		add_button.classList.remove('error-input');
		add_button.title = '';

		toggleAddService();
		fillNotificationSelection();
	})
	.catch(e => {
		if (e === 401)
			window.location.href = `${url_prefix}/`;
		else if (e === 400) {
			add_button.classList.add('error-input');
			add_button.title = 'Invalid Apprise URL';
		} else
			console.log(e);
	});
};

// code run on load

fillNotificationSelection();

let notification_services = null;

document.getElementById('add-service-button').addEventListener('click', e => toggleAddService());
document.getElementById('add-service-window').setAttribute('action', 'javascript:addService();');
