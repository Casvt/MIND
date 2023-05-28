const inputs_buttons = {
	'save_button': document.querySelector('#add-row button[data-type="save"]'),
	'title': document.querySelector('#add-row td.title-column input'),
	'url': document.querySelector('#add-row td.url-column input')
};

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
};

function addService() {
	const data = {
		'title': inputs_buttons.title.value,
		'url': inputs_buttons.url.value
	};
	fetch(`${url_prefix}/api/notificationservices?api_key=${api_key}`, {
		'method': 'POST',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);
		
		inputs_buttons.title.value = '';
		inputs_buttons.url.value = '';

		inputs_buttons.save_button.classList.remove('error-icon');
		inputs_buttons.save_button.title = 'Add';
		inputs_buttons.save_button.setAttribute('aria-label', 'Add');
		
		toggleAddService();
		fillNotificationSelection();
	})
	.catch(e => {
		if (e === 401)
			window.location.href = `${url_prefix}/`;
		else if (e === 400) {
			inputs_buttons.save_button.classList.add('error-icon');
			inputs_buttons.save_button.title = 'Invalid Apprise URL';
			inputs_buttons.save_button.setAttribute('aria-label', 'Invalid Apprise URL');
		} else
			console.log(e);
	});
};

// code run on load

fillNotificationSelection();

document.getElementById('add-service-button').addEventListener('click', e => toggleAddService());
document.querySelector('#add-row button[data-type="save"]').addEventListener('click', e => addService());
