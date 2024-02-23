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
		inputs.notification_service.querySelectorAll(
			'input[type="checkbox"]:checked'
		).forEach(c => c.checked = false)
		inputs.text.value = '';
		selectColor(colors[0]);

	} else {
		fetch(`${url_prefix}/api/templates/${inputs.template.value}?api_key=${api_key}`)
		.then(response => {
			if (!response.ok) return Promise.reject(response.status);
			else return response.json();
		})
		.then(json => {
			inputs.title.value = json.result.title;
			inputs.notification_service.querySelectorAll('input[type="checkbox"]').forEach(
				c => c.checked = json.result.notification_services.includes(parseInt(c.dataset.id))
			);
			inputs.text.value = json.result.text;
			selectColor(json.result.color || colors[0]);
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
