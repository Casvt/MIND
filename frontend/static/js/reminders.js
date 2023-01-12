function fillTable(result) {
	const table = document.getElementById('reminder-list');
	table.querySelectorAll('button:not(#add-entry)').forEach(e => e.remove());

	result.forEach(reminder => {
		const entry = document.createElement('button');
		entry.classList.add('entry');
		entry.dataset.id = reminder.id;
		
		const title = document.createElement('h2');
		title.innerText = reminder.title;
		entry.appendChild(title);

		const time = document.createElement('p');
		var d = new Date(reminder.time * 1000);
		var formatted_date = d.toLocaleString('en-CA').slice(0,10) + ' ' + d.toTimeString().slice(0,5);
		time.innerText = formatted_date;
		entry.appendChild(time);
		
		const options = document.createElement('div');
		options.classList.add('entry-overlay');
		entry.appendChild(options);
		
		const edit_entry = document.createElement('button');
		edit_entry.addEventListener('click', e => showEdit(reminder.id));
		edit_entry.innerHTML = edit_icon;
		edit_entry.title = 'Edit reminder';
		edit_entry.setAttribute('aria-label', 'Edit reminder');
		options.appendChild(edit_entry);
		
		const delete_entry = document.createElement('button');
		delete_entry.addEventListener('click', e => deleteReminder(reminder.id));
		delete_entry.innerHTML = delete_icon;
		delete_entry.title = 'Delete reminder';
		delete_entry.setAttribute('aria-label', 'Delete reminder');
		options.appendChild(delete_entry);

		table.appendChild(entry);
	});
};

function fillList() {
	fetch(`/api/reminders?api_key=${api_key}`)
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		return response.json();
	})
	.then(json => {
		fillTable(json.result);
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		} else {
			console.log(e);
		};
	});
};

function search() {
	const query = document.getElementById('search-input').value;
	fetch(`/api/reminders/search?api_key=${api_key}&query=${query}`)
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		return response.json();
	})
	.then(json => {
		fillTable(json.result);
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		} else {
			console.log(e);
		};
	});
};

function clearSearch() {
	document.getElementById('search-input').value = '';
	fillList();
}

function deleteReminder(id) {
	const entry = document.querySelector(`button.entry[data-id="${id}"]`);
	entry.remove();
	
	fetch(`/api/reminders/${id}?api_key=${api_key}`, {
		'method': 'DELETE'
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		} else if (e === 404) {
			fillList();
		} else {
			console.log(e);
		};
	});
};

// code run on load

fillList();
setInterval(fillList, 60000);

document.getElementById('search-form').setAttribute('action', 'javascript:search();');
document.getElementById('clear-button').addEventListener('click', e => clearSearch());
document.getElementById('add-entry').addEventListener('click', e => showAdd());
