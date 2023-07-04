function fillNotificationSelection() {
	fetch(`${url_prefix}/api/notificationservices?api_key=${api_key}`)
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);
		return response.json();
	})
	.then(json => {
		if (json.result.length) {
			document.getElementById('add-reminder').classList.remove('error', 'error-icon');

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
			table.querySelectorAll('tr:not(#add-row)').forEach(e => e.remove());
			// table.innerHTML = '';
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
		if (document.querySelectorAll('#services-list > tr:not(#add-row)').length === 0)
			document.getElementById('add-entry').classList.add('error', 'error-icon');
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
	document.getElementById('add-row').classList.toggle('hidden');
	return;
	
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

function showAddServiceWindow(index) {
	const window = document.getElementById('add-service-window');
	window.innerHTML = '';

	if (index === -1) {
		// Custom url
		const title = document.createElement('h3');
		title.innerText = 'Custom URL';
		window.appendChild(title);
		
		const desc = document.createElement('p');
		desc.innerHTML = 'Enter a custom Apprise URL. See the <a target="_blank" href="https://github.com/caronc/apprise#supported-notifications">Apprise URL documentation</a>.';
		window.appendChild(desc);

		const service_title = document.createElement('input');
		service_title.id = 'service-title';
		service_title.type = 'text';
		service_title.placeholder = 'Service Title';
		service_title.required = true;
		window.appendChild(service_title);
			
		const url_input = document.createElement('input');
		url_input.type = 'text';
		url_input.placeholder = 'Apprise URL';
		window.appendChild(url_input);
	} else {
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

		const service_title = document.createElement('input');
		service_title.id = 'service-title';
		service_title.type = 'text';
		service_title.placeholder = 'Service Title';
		service_title.required = true;
		window.appendChild(service_title);	
		
		data.details.tokens.forEach(token => {
			if (token.type === 'choice') {
				const choice = document.createElement('select');
				choice.dataset.map = token.map_to;
				choice.dataset.prefix = '';
				choice.placeholder = token.name;
				choice.required = token.required;
				token.options.forEach(option => {
					const entry = document.createElement('option');
					entry.value = option;
					entry.innerText = option;
					choice.appendChild(entry);
				});
				window.appendChild(choice);

			} else if (token.type === 'list') {
				if (token.content.length === 0) {
					
				} else {
					token.content.forEach(content => {
						
					});
				};

			} else if (token.type === 'string') {
				const str_input = document.createElement('input');
				str_input.dataset.map = token.map_to;
				str_input.dataset.prefix = token.prefix;
				str_input.dataset.regex = token.regex;
				str_input.type = 'text';
				str_input.placeholder = `${token.name}${!token.required ? ' (Optional)' : ''}`;
				str_input.required = token.required;
				window.appendChild(str_input);

			} else if (token.type === 'int') {
				const int_input = document.createElement('input');
				int_input.dataset.map = token.map_to;
				int_input.dataset.prefix = token.prefix;
				int_input.type = 'number';
				int_input.placeholder = `${token.name}${!token.required ? ' (Optional)' : ''}`;
				int_input.required = token.required;
				if (token.min !== null)
					int_input.min = token.min;
				if (token.max !== null)
					int_input.max = token.max;
				window.appendChild(int_input);
			};
		});
	};
	
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
	return null;
};

function addService() {
	const add_button = document.querySelector('#add-row > .action-column > button');
	const data = {
		'title': document.querySelector('#add-row > .title-column > input').value,
		'url': document.querySelector('#add-row > .url-column > input').value
	};
	// const add_button = document.querySelector('#add-service-window > .options > button[type="submit"]');
	// const data = {
	// 	'title': document.querySelector('#service-title').value,
	// 	'url': buildAppriseURL()
	// };
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
			// add_button.classList.add('error-input');
			add_button.classList.add('error-icon');
			add_button.title = 'Invalid Apprise URL';
		} else
			console.log(e);
	});
};

// code run on load

fillNotificationSelection();

let notification_services = null;

document.getElementById('add-service-button').addEventListener('click', e => toggleAddService());
// document.querySelector('#service-list button').addEventListener('click', e => showAddServiceWindow(-1));
// document.getElementById('add-service-window').setAttribute('action', 'javascript:addService();');
document.querySelector('#add-row > .action-column > button').addEventListener('click', e => addService());
