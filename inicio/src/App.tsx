// App.tsx
import * as React from "react";
import {
	createBrowserRouter,
	RouterProvider,
} from "react-router-dom";
import { FrappeProvider } from 'frappe-react-sdk'
import { Toaster } from 'sonner'
import './index.css'
import LoginPage from './pages/login-page';
import HomePage from "./pages/home";

function App() {
	const getSiteName = () => {
		// @ts-ignore
		if (window.frappe?.boot?.versions?.frappe && (window.frappe.boot.versions.frappe.startsWith('15') || window.frappe.boot.versions.frappe.startsWith('16'))) {
			// @ts-ignore
			return window.frappe?.boot?.sitename ?? import.meta.env.VITE_SITE_NAME
		}
		return import.meta.env.VITE_SITE_NAME
	}

	const router = createBrowserRouter([
		{
			path: "/",
			element: <HomePage />,
		},
		{
			path: "/inicio",
			element: <HomePage />,
		},
		{
			path: "/inicio/login",
			element: <LoginPage />,
		},
	]);

	return (
		<div className="App">
			<FrappeProvider
				socketPort={import.meta.env.VITE_SOCKET_PORT}
				siteName={getSiteName()}
			>
				<RouterProvider router={router} />
				<Toaster richColors closeButton position="top-center" />
			</FrappeProvider>
		</div>
	);
}

export default App;
