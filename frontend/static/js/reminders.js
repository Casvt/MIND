function fillTable(result) {
	const table = document.getElementById('reminder-list');
	table.querySelectorAll('button.entry:not(#add-entry)').forEach(e => e.remove());

	result.forEach(reminder => {
		const entry = document.createElement('button');
		entry.classList.add('entry');
		entry.dataset.id = reminder.id;
		entry.addEventListener('click', e => showEdit(reminder.id));
		if (reminder.color !== null) {
			entry.style.setProperty('--color', reminder.color);
		};
		
		const title = document.createElement('h2');
		title.innerText = reminder.title;
		entry.appendChild(title);

		const time = document.createElement('p');
		var offset = new Date(reminder.time * 1000).getTimezoneOffset() * -60;
		var d = new Date((reminder.time + offset) * 1000);
		var formatted_date = d.toLocaleString('en-CA').slice(0,10) + ' ' + d.toTimeString().slice(0,5);
		if (reminder.repeat_interval !== null) {
			if (reminder.repeat_interval === 1) {
				var quantity = reminder.repeat_quantity.endsWith('s') ? reminder.repeat_quantity.slice(0, -1) : reminder.repeat_quantity;
				var interval_text = ` (each ${quantity})`;
			} else {
				var quantity = reminder.repeat_quantity.endsWith('s') ? reminder.repeat_quantity : reminder.repeat_quantity + 's';
				var interval_text = ` (every ${reminder.repeat_interval} ${quantity})`;
			};
			formatted_date += interval_text;
		};
		time.innerText = formatted_date;
		entry.appendChild(time);

		table.appendChild(entry);
		
		if (title.clientHeight < title.scrollHeight) {
			entry.classList.add('expand');
		};
	});
	table.querySelectorAll('button.entry:not(#add-entry)').forEach(reminder => reminder.classList.add('fit'));
};

function fillList() {
	fetch(`${url_prefix}/api/reminders?api_key=${api_key}`)
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
			window.location.href = `${url_prefix}/`;
		} else {
			console.log(e);
		};
	});
};

function search() {
	const query = document.getElementById('search-input').value;
	fetch(`${url_prefix}/api/reminders/search?api_key=${api_key}&query=${query}`)
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
			window.location.href = `${url_prefix}/`;
		} else {
			console.log(e);
		};
	});
};

function clearSearch() {
	document.getElementById('search-input').value = '';
	fillList();
}

// code run on load

fillList();
setInterval(fillList, 60000);

document.getElementById('search-form').setAttribute('action', 'javascript:search();');
document.getElementById('clear-button').addEventListener('click', e => clearSearch());
document.getElementById('add-entry').addEventListener('click', e => showAdd());
document.getElementById('add-template').addEventListener('click', e => showWindow('add-template'));
