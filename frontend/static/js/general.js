const types = {
	'reminder': document.getElementById('reminder-tab'),
	'static_reminder': document.getElementById('static-reminder-tab'),
	'template': document.getElementById('template-tab')
};

const icons = {
	'save': '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:svgjs="http://svgjs.com/svgjs" width="256" height="256" x="0" y="0" viewBox="0 0 24 24" style="enable-background:new 0 0 512 512" xml:space="preserve"><g><path d="M12,10a4,4,0,1,0,4,4A4,4,0,0,0,12,10Zm0,6a2,2,0,1,1,2-2A2,2,0,0,1,12,16Z"></path><path d="M22.536,4.122,19.878,1.464A4.966,4.966,0,0,0,16.343,0H5A5.006,5.006,0,0,0,0,5V19a5.006,5.006,0,0,0,5,5H19a5.006,5.006,0,0,0,5-5V7.657A4.966,4.966,0,0,0,22.536,4.122ZM17,2.08V3a3,3,0,0,1-3,3H10A3,3,0,0,1,7,3V2h9.343A2.953,2.953,0,0,1,17,2.08ZM22,19a3,3,0,0,1-3,3H5a3,3,0,0,1-3-3V5A3,3,0,0,1,5,2V3a5.006,5.006,0,0,0,5,5h4a4.991,4.991,0,0,0,4.962-4.624l2.16,2.16A3.02,3.02,0,0,1,22,7.657Z"></path></g></svg>',
	'edit': '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:svgjs="http://svgjs.com/svgjs" width="256" height="256" x="0" y="0" viewBox="0 0 24 24" style="enable-background:new 0 0 512 512" xml:space="preserve"><g><g id="_01_align_center" data-name="01 align center"><path d="M22.94,1.06a3.626,3.626,0,0,0-5.124,0L0,18.876V24H5.124L22.94,6.184A3.627,3.627,0,0,0,22.94,1.06ZM4.3,22H2V19.7L15.31,6.4l2.3,2.3ZM21.526,4.77,19.019,7.277l-2.295-2.3L19.23,2.474a1.624,1.624,0,0,1,2.3,2.3Z"></path></g></g></svg>',
	'delete': '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:svgjs="http://svgjs.com/svgjs" width="256" height="256" x="0" y="0" viewBox="0 0 24 24" style="enable-background:new 0 0 512 512" xml:space="preserve"><g><g id="_01_align_center" data-name="01 align center"><path d="M22,4H17V2a2,2,0,0,0-2-2H9A2,2,0,0,0,7,2V4H2V6H4V21a3,3,0,0,0,3,3H17a3,3,0,0,0,3-3V6h2ZM9,2h6V4H9Zm9,19a1,1,0,0,1-1,1H7a1,1,0,0,1-1-1V6H18Z"></path><rect x="9" y="10" width="2" height="8"></rect><rect x="13" y="10" width="2" height="8"></rect></g></g></svg>',
	'add': '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:svgjs="http://svgjs.com/svgjs" width="256" height="256" x="0" y="0" viewBox="0 0 512 512" style="enable-background:new 0 0 512 512" xml:space="preserve"><g><g><path d="M480,224H288V32c0-17.673-14.327-32-32-32s-32,14.327-32,32v192H32c-17.673,0-32,14.327-32,32s14.327,32,32,32h192v192   c0,17.673,14.327,32,32,32s32-14.327,32-32V288h192c17.673,0,32-14.327,32-32S497.673,224,480,224z"></path></g></g></svg>'
};

const info_classes = [
	'show-add-reminder', 'show-add-template', 'show-add-static-reminder',
	'show-edit-reminder', 'show-edit-template', 'show-edit-static-reminder'
];

function toggleNav() {
	document.querySelector('.nav-divider').classList.toggle('show-nav');
};

function showWindow(id) {
	document.querySelectorAll('.window-container > div').forEach(e => {
		if (e.id === id || e.id === 'home') {
			e.classList.remove('hidden');
			setTimeout(() => e.classList.add('show-window'), 0);
		} else {
			e.classList.add('hidden');
			e.classList.remove('show-window');
		};
	});
};

function hideWindow() {
	document.querySelectorAll('.show-window').forEach(e => {
		e.classList.remove('show-window');
	});
	setTimeout(() => {
		document.querySelectorAll('.window-container > div:not(#home)').forEach(
			e => e.classList.add('hidden')
		);
	}, 500);
};

function logout() { 
	fetch(`${url_prefix}/api/auth/logout?api_key=${api_key}`, {
		'method': 'POST'
	})
	.then(response => {
		const new_stor = JSON.parse(localStorage.getItem('MIND'))
		new_stor.api_key = null
		localStorage.setItem('MIND', JSON.stringify(new_stor));
		window.location.href = `${url_prefix}/`;
	});
};

// code run on load

if (localStorage.getItem('MIND') === null)
	localStorage.setItem('MIND', JSON.stringify({'api_key': null, 'locale': 'en-GB'}))

const url_prefix = document.getElementById('url_prefix').dataset.value;
const api_key = JSON.parse(localStorage.getItem('MIND')).api_key;
if (api_key === null) {
	window.location.href = `${url_prefix}/`;
};

document.getElementById('toggle-nav').addEventListener('click', e => toggleNav());

document.getElementById('home-button').addEventListener('click', e => hideWindow());
document.getElementById('notification-services-button').addEventListener('click', e => showWindow('notification'));
document.getElementById('settings-button').addEventListener('click', e => showWindow('settings'));
document.getElementById('logout-button').addEventListener('click', e => logout());
