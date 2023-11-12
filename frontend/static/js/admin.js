function checkLogin() {
	fetch(`${url_prefix}/api/auth/status?api_key=${api_key}`)
	.then(response => {
		if (!response.ok) return Promise.reject(response.status)
		return response.json();
	})
	.then(json => {
		if (!json.result.admin)
			window.location.href = `${url_prefix}/reminders`;
	})
	.catch(e => {
		if (e === 401)
			window.location.href = `${url_prefix}/`;
		else
			console.log(e);
	});
};

// code run on load

checkLogin();
