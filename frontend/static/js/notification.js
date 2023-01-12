function fillNotificationSelection() {
	fetch(`/api/notificationservices?api_key=${api_key}`)
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		
		return response.json();
	})
	.then(json => {
		if (json.result.length) {
			document.getElementById('no-service-error').classList.add('hidden');
			[document.getElementById('notification-service-input'),
			document.getElementById('notification-service-edit-input')].forEach(options => {
				options.innerHTML = '';
				json.result.forEach(service => {
					const entry = document.createElement('option');
					entry.value = service.id;
					entry.innerText = service.title;
					options.appendChild(entry);
				});
				options.querySelector(':nth-child(1)').setAttribute('selected', '');
			});
			
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
				edit_button.innerHTML = edit_icon;
				actions.appendChild(edit_button);
				
				const save_button = document.createElement('button');
				save_button.dataset.type = 'save';
				save_button.addEventListener('click', e => saveService(service.id));
				save_button.title = 'Save Edits';
				save_button.setAttribute('aria-label', 'Save Edits');
				save_button.innerHTML = save_icon;
				actions.appendChild(save_button);
				
				const delete_button = document.createElement('button');
				delete_button.dataset.type = 'delete';
				delete_button.addEventListener('click', e => deleteService(service.id));
				delete_button.title = 'Delete';
				delete_button.setAttribute('aria-label', 'Delete');
				delete_button.innerHTML = delete_icon;
				actions.appendChild(delete_button);
				
				table.appendChild(entry);
			});	
		} else {
			document.getElementById('no-service-error').classList.remove('hidden');
		};
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		} else {
			console.log(e);
		};
	});
};

function deleteService(id) {
	const row = document.querySelector(`tr[data-id="${id}"]`);
	fetch(`/api/notificationservices/${id}?api_key=${api_key}`, {
		'method': 'DELETE'
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		
		row.remove();
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		} else if (e === 400) {
			const delete_button = row.querySelector('button[title="Delete"]');
			delete_button.classList.add('error-icon');
			delete_button.title = 'The notification service is still in use by a reminder';
		} else {
			console.log(e);
		};
	});
};

function editService(id) {
	document.querySelectorAll(`tr[data-id="${id}"] input`).forEach(e => e.removeAttribute('readonly'));
};

function saveService(id) {
	const row = document.querySelector(`tr[data-id="${id}"]`);
	const save_button = row.querySelector('button[data-type="save"]');
	const data = {
		'title': row.querySelector(`td.title-column > input`).value,
		'url': row.querySelector(`td.url-column > input`).value
	};
	fetch(`/api/notificationservices/${id}?api_key=${api_key}`, {
		'method': 'PUT',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		
		fillNotificationSelection();
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		} else if (e === 400) {
			save_button.classList.add('error-icon');
			save_button.title = 'Invalid Apprise URL';
			save_button.setAttribute('aria-label', 'Invalid Apprise URL');
		} else {
			console.log(e);
		};
	});
};

function toggleAddService() {
	document.getElementById('add-row').classList.toggle('hidden');
};

function addService() {
	const inputs_buttons = {
		'save_button': document.querySelector('#add-row button[data-type="save"]'),
		'title': document.querySelector('#add-row td.title-column input'),
		'url': document.querySelector('#add-row td.url-column input')
	};
	const data = {
		'title': inputs_buttons.title.value,
		'url': inputs_buttons.url.value
	};
	fetch(`/api/notificationservices?api_key=${api_key}`, {
		'method': 'POST',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		
		inputs_buttons.title.value = '';
		inputs_buttons.url.value = '';

		inputs_buttons.save_button.classList.remove('error-icon');
		inputs_buttons.save_button.title = 'Add';
		inputs_buttons.save_button.setAttribute('aria-label', 'Add');
		
		toggleAddService();
		fillNotificationSelection();
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		} else if (e === 400) {
			inputs_buttons.save_button.classList.add('error-icon');
			inputs_buttons.save_button.title = 'Invalid Apprise URL';
			inputs_buttons.save_button.setAttribute('aria-label', 'Invalid Apprise URL');
		} else {
			console.log(e);
		};
	});
};

// code run on load

fillNotificationSelection();

document.getElementById('add-service-button').addEventListener('click', e => toggleAddService());
document.querySelector('#add-row button[data-type="save"]').addEventListener('click', e => addService());
