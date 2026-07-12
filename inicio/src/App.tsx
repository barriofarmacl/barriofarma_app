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
import CatalogoPage from './pages/catalogo-page';
import { RequireAuth } from './components/require-auth';
import { AppShell } from './components/app-shell';

function App() {
	const getSiteName = () => {
		// @ts-expect-error Frappe injects boot data into the browser at runtime.
		if (window.frappe?.boot?.versions?.frappe && (window.frappe.boot.versions.frappe.startsWith('15') || window.frappe.boot.versions.frappe.startsWith('16'))) {
			// @ts-expect-error Frappe injects boot data into the browser at runtime.
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
		{
			path: "/inicio/catalogo",
			element: (
				<RequireAuth>
					<AppShell pageTitle="Catalogo terreno">
						<CatalogoPage />
					</AppShell>
				</RequireAuth>
			),
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
