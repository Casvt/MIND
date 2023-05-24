function loadTemplateSelection() {
	fetch(`${url_prefix}/api/templates?api_key=${api_key}`)
	.then(response => {
		if (!response.ok) return Promise.reject(response.status);
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
	})
	.catch(e => {
		if (e === 401)
			window.location.href = `${url_prefix}/`;
		else
			console.log(e);
	});
};

function applyTemplate() {
	if (inputs.template.value === '0') {
		inputs.title.value = '';
		inputs.notification_service.value = document.querySelector('#notification-service-input option[selected]').value;
		inputs.text.value = '';
		toggleColor(true);
	} else {
		fetch(`${url_prefix}/api/templates/${inputs.template.value}?api_key=${api_key}`)
		.then(response => {
			if (!response.ok) return Promise.reject(response.status);
			else return response.json();
		})
		.then(json => {
			inputs.title.value = json.result.title;
			inputs.notification_service.value = json.result.notification_service;
			inputs.text.value = json.result.text;
			if (json.result.color !== null) {
				if (inputs.color.classList.contains('hidden'))
					toggleColor();
				selectColor(json.result.color);
			} else
				toggleColor(true);
		})
		.catch(e => {
			if (e === 401)
				window.location.href = `${url_prefix}/`;
			else
				console.log(e);
		});
	};
};

// code run on load

loadTemplateSelection();

// function addTemplate() {
// 	const data = {
// 		'title': template_inputs.title.value,
// 		'notification_service': template_inputs["notification-service"].value,
// 		'text': template_inputs.text.value,
// 		'color': null
// 	};
// 	if (!template_inputs.color.classList.contains('hidden')) {
// 		data['color'] = template_inputs.color.querySelector('button[data-selected="true"]').dataset.color;
// 	};
// 	fetch(`${url_prefix}/api/templates?api_key=${api_key}`, {
// 		'method': 'POST',
// 		'headers': {'Content-Type': 'application/json'},
// 		'body': JSON.stringify(data)
// 	})
// 	.then(response => {
// 		// catch errors
// 		if (!response.ok) {
// 			return Promise.reject(response.status);
// 		};

// 		loadTemplateSelection();
// 		closeAddTemplate();
// 		return
// 	})
// 	.catch(e => {
// 		if (e === 401) {
// 			window.location.href = `${url_prefix}/`;
// 		} else {
// 			console.log(e);
// 		};
// 	});
// };

// function closeAddTemplate() {
// 	hideWindow();
// 	setTimeout(() => {
// 		template_inputs.title.value = '';
// 		template_inputs['notification-service'].value = document.querySelector('#notification-service-template-input option[selected]').value;
// 		template_inputs.text.value = '';
// 		if (!template_inputs.color.classList.contains('hidden')) {
// 			toggleColor(inputs.color);
// 		};
// 	}, 500);
// };

// function showEditTemplate(id) {
// 	fetch(`${url_prefix}/api/templates/${id}?api_key=${api_key}`)
// 	.then(response => {
// 		// catch errors
// 		if (!response.ok) {
// 			return Promise.reject(response.status);
// 		};
// 		return response.json();
// 	})
// 	.then(json => {
// 		document.getElementById('template-edit-form').dataset.id = id;
// 		edit_template_inputs.title.value = json.result.title;
// 		edit_template_inputs['notification-service'].value = json.result.notification_service;
// 		edit_template_inputs.text.value = json.result.text;
// 		if (json.result.color !== null) {
// 			if (edit_template_inputs.color.classList.contains('hidden')) {
// 				toggleColor(edit_template_inputs.color);
// 			};
// 			selectColor(edit_template_inputs.color, json.result.color);
// 		};
// 		showWindow('edit-template');
// 	})
// 	.catch(e => {
// 		if (e === 401) {
// 			window.location.href = `${url_prefix}/`;
// 		} else {
// 			console.log(e);
// 		};
// 	});
// };

// function saveTemplate() {
// 	const id = document.getElementById('template-edit-form').dataset.id;
// 	const data = {
// 		'title': edit_template_inputs.title.value,
// 		'notification_service': edit_template_inputs['notification-service'].value,
// 		'text': edit_template_inputs.text.value,
// 		'color': null
// 	};
// 	if (!edit_template_inputs.color.classList.contains('hidden')) {
// 		data['color'] = edit_template_inputs.color.querySelector('button[data-selected="true"]').dataset.color;
// 	};
// 	fetch(`${url_prefix}/api/templates/${id}?api_key=${api_key}`, {
// 		'method': 'PUT',
// 		'headers': {'Content-Type': 'application/json'},
// 		'body': JSON.stringify(data)
// 	})
// 	.then(response => {
// 		// catch errors
// 		if (!response.ok) {
// 			return Promise.reject(response.status);
// 		};
// 		loadTemplateSelection();
// 		hideWindow();
// 	})
// 	.catch(e => {
// 		if (e === 401) {
// 			window.location.href = `${url_prefix}/`;
// 		} else {
// 			console.log(e);
// 		};
// 	});
// };

// function deleteTemplate() {
// 	const id = document.getElementById('template-edit-form').dataset.id;
// 	fetch(`${url_prefix}/api/templates/${id}?api_key=${api_key}`, {
// 		'method': 'DELETE'
// 	})
// 	.then(response => {
// 		// catch errors
// 		if (!response.ok) {
// 			return Promise.reject(response.status);
// 		};
		
// 		loadTemplateSelection();
// 		hideWindow();
// 	})
// 	.catch(e => {
// 		if (e === 401) {
// 			window.location.href = `${url_prefix}/`;
// 		} else {
// 			console.log(e);
// 		};
// 	});
// };
