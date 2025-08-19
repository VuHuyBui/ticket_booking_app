// auth.js

// Wrapper for fetch that automatically refreshes access token if expired
export async function fetchWithAuth(url, options = {}) {
	let token = sessionStorage.getItem("access");

	if (!options.headers) {
		options.headers = {
			// "Access-Control-Allow-Origin": "*",
		};
	}
	options.headers["Authorization"] = `Bearer ${token}`;

	let res = await fetch(url, options);

	// If unauthorized, try refresh
	if (res.status === 401) {
		console.warn("Access token expired, trying refresh...");

		const refreshRes = await fetch("http://127.0.0.1:8000/auth/refresh/", {
			method: "POST",
			credentials: "include", // include cookies
		});

		if (refreshRes.ok) {
			const data = await refreshRes.json();
			sessionStorage.setItem("access", data.access);

			// Retry original request with new access token
			options.headers["Authorization"] = `Bearer ${data.access}`;
			res = await fetch(url, options);
		} else {
			// Refresh failed → redirect to login
			console.error("Refresh failed, redirecting to login...");
			window.location.href = "login.html";
			return;
		}
	}

	return res;
}

export function logout() {
	// Clear access token
	sessionStorage.removeItem("access");

	// Call backend to clear refresh cookie
	fetch("http://127.0.0.1:8000/auth/logout", {
		method: "POST",
		credentials: "include", // send cookies
	}).finally(() => {
		// Redirect to login after logout
		window.location.href = "login.html";
	});
}
