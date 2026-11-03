// App.tsx
import * as React from "react";
import {
	createBrowserRouter,
	Navigate,
	RouterProvider,
} from "react-router-dom";
import { FrappeProvider } from 'frappe-react-sdk'
import { Toaster } from 'sonner'
import './index.css'
import LoginPage from './pages/login-page';
import HomePage from "./pages/home";
import TurnoKioscoPage from './pages/turno-kiosco-page';
import TurnoPantallaPage from './pages/turno-pantalla-page';
import { RequireAuth } from './components/require-auth';
import { AppShell } from './components/app-shell';
import { isCatalogoTerrenoEnabled } from './lib/inicio-features';
import CatalogoPage from './pages/catalogo-page';

function App() {
	const getSiteName = () => {
		// @ts-expect-error Frappe injects boot data into the browser at runtime.
		if (window.frappe?.boot?.versions?.frappe && (window.frappe.boot.versions.frappe.startsWith('15') || window.frappe.boot.versions.frappe.startsWith('16'))) {
			// @ts-expect-error Frappe injects boot data into the browser at runtime.
			return window.frappe?.boot?.sitename ?? import.meta.env.VITE_SITE_NAME
		}
		// @ts-expect-error Frappe injects boot data into the browser at runtime.
		return window.frappe?.boot?.sitename ?? import.meta.env.VITE_SITE_NAME
	}

	const getSocketPort = () => {
		// @ts-expect-error Frappe injects boot data into the browser at runtime.
		const fromBoot = window.frappe?.boot?.socketio_port
		if (fromBoot != null && String(fromBoot).trim() !== '') {
			return String(fromBoot)
		}
		const fromEnv = import.meta.env.VITE_SOCKET_PORT
		return fromEnv ? String(fromEnv) : undefined
	}

	const routes = [
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
	];

	if (isCatalogoTerrenoEnabled()) {
		routes.push({
			path: "/inicio/catalogo",
			element: (
				<RequireAuth>
					<AppShell pageTitle="Catalogo terreno">
						<CatalogoPage />
					</AppShell>
				</RequireAuth>
			),
		});
	}

	const router = createBrowserRouter([
		...routes,
		{
			path: "/turno",
			element: (
				<RequireAuth>
					<TurnoKioscoPage />
				</RequireAuth>
			),
		},
		{
			path: "/pantalla",
			element: <TurnoPantallaPage />,
		},
		{
			path: "/inicio/turno",
			element: <Navigate to="/turno" replace />,
		},
		{
			path: "/inicio/pantalla",
			element: <Navigate to="/pantalla" replace />,
		},
	]);

	return (
		<div className="App">
			<FrappeProvider
				socketPort={getSocketPort()}
				siteName={getSiteName()}
				enableSocket
			>
				<RouterProvider router={router} />
				<Toaster richColors closeButton position="top-center" />
			</FrappeProvider>
		</div>
	);
}

export default App;
