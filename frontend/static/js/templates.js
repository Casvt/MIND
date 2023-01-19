const template_inputs = {
	'title': document.getElementById('title-template-input'),
	'notification-service': document.getElementById('notification-service-template-input'),
	'text': document.getElementById('text-template-input')
};

const edit_template_inputs = {
	'title': document.getElementById('title-template-edit-input'),
	'notification-service': document.getElementById('notification-service-template-edit-input'),
	'text': document.getElementById('text-template-edit-input')
};

function loadTemplates(force=true) {
	const table = document.getElementById('template-list');
	if (!force && !!table.querySelector('button:not(#add-template)')) {
		return
	};

	fetch(`/api/templates?api_key=${api_key}`)
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		return response.json();
	})
	.then(json => {
		const select_list = document.getElementById('template-selection');
		select_list.querySelectorAll('option:not([selected])').forEach(e => e.remove());
		json.result.forEach(template => {
			const entry = document.createElement('option');
			entry.value = template.id;
			entry.innerText = template.title;

			select_list.appendChild(entry);
		});
		
		table.querySelectorAll('button:not(#add-template)').forEach(e => e.remove());
		json.result.forEach(template => {
			const entry = document.createElement('button');
			entry.classList.add('entry');
			entry.addEventListener('click', e => showEditTemplate(template.id));

			const title = document.createElement('h2');
			title.innerText = template.title;
			entry.appendChild(title);
			
			table.appendChild(entry);
			
			if (title.clientHeight < title.scrollHeight) {
				entry.classList.add('expand');
			};
		});
		table.querySelectorAll('button:not(#add-template)').forEach(template => template.classList.add('fit'));
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		} else {
			console.log(e);
		};
	});
};

function loadTemplate() {
	const id = document.getElementById('template-selection').value;
	if (id === "0") {
		inputs.title.value = '';
		inputs.notification_service.value = document.querySelector('#notification-service-input option[selected]').value;
		inputs.text.value = '';
	} else {
		fetch(`/api/templates/${id}?api_key=${api_key}`)
		.then(response => {
			// catch errors
			if (!response.ok) {
				return Promise.reject(response.status);
			};
			return response.json();
		})
		.then(json => {
			inputs.title.value = json.result.title;
			inputs.notification_service.value = json.result.notification_service;
			inputs.text.value = json.result.text;
		})
		.catch(e => {
			if (e === 401) {
				window.location.href = '/';
			} else {
				console.log(e);
			};
		});
	};
};

function addTemplate() {
	const data = {
		'title': template_inputs.title.value,
		'notification_service': template_inputs["notification-service"].value,
		'text': template_inputs.text.value
	};
	fetch(`/api/templates?api_key=${api_key}`, {
		'method': 'POST',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};

		loadTemplates();
		closeAddTemplate();
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

function closeAddTemplate() {
	hideWindow();
	setTimeout(() => {
		template_inputs.title.value = '';
		template_inputs['notification-service'].value = document.querySelector('#notification-service-template-input option[selected]').value;
		template_inputs.text.value = '';
	}, 500);
};

function showEditTemplate(id) {
	fetch(`/api/templates/${id}?api_key=${api_key}`)
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		return response.json();
	})
	.then(json => {
		document.getElementById('template-edit-form').dataset.id = id;
		edit_template_inputs.title.value = json.result.title;
		edit_template_inputs['notification-service'].value = json.result.notification_service;
		edit_template_inputs.text.value = json.result.text;
		showWindow('edit-template');
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		} else {
			console.log(e);
		};
	});
};

function saveTemplate() {
	const id = document.getElementById('template-edit-form').dataset.id;
	const data = {
		'title': edit_template_inputs.title.value,
		'notification_service': edit_template_inputs['notification-service'].value,
		'text': edit_template_inputs.text.value
	};
	fetch(`/api/templates/${id}?api_key=${api_key}`, {
		'method': 'PUT',
		'headers': {'Content-Type': 'application/json'},
		'body': JSON.stringify(data)
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		loadTemplates();
		hideWindow();
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		} else {
			console.log(e);
		};
	});
};

function deleteTemplate() {
	const id = document.getElementById('template-edit-form').dataset.id;
	fetch(`/api/templates/${id}?api_key=${api_key}`, {
		'method': 'DELETE'
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		
		loadTemplates();
		hideWindow();
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		} else {
			console.log(e);
		};
	});
};

// code run on load

document.getElementById('template-form').setAttribute('action', 'javascript:addTemplate();');
document.getElementById('close-template').addEventListener('click', e => closeAddTemplate());
document.getElementById('template-edit-form').setAttribute('action', 'javascript:saveTemplate()');
document.getElementById('close-edit-template').addEventListener('click', e => hideWindow());
document.getElementById('delete-template').addEventListener('click', e => deleteTemplate());
