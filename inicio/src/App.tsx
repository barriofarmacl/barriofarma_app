// App.tsx
import * as React from "react";
import * as ReactDOM from "react-dom/client";
import {
	createBrowserRouter,
	RouterProvider,
} from "react-router-dom"; // Asegúrate de importar RouterProvider
import { FrappeProvider } from 'frappe-react-sdk'
import './index.css'
import LoginPage from './pages/login-page'; // Importa LoginPage
import POSSystem from './pages/pos-system'; // Importa POSSystem
import DashboardFarmacia from "./pages/dashboard";
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
			path: "/inicio",
			element: <HomePage />, // Agrega la ruta para HomePage
		},
		{
			path: "/inicio/login",
			element: <LoginPage />, // Agrega la ruta para LoginPage
		},
		{
			path: "/inicio/pos",
			element: <POSSystem />, // Agrega la ruta para POSSystem
		},
		{
			path: "/inicio/dashboard",
			element: <DashboardFarmacia />, // Agrega la ruta para POSSystem
		},
	]);

	return (
		<div className="App">
			<FrappeProvider
				socketPort={import.meta.env.VITE_SOCKET_PORT}
				siteName={getSiteName()}
			>
				<RouterProvider router={router} />
				{/* El RouterProvider ahora gestiona las rutas */}
			</FrappeProvider>
		</div>
	);
}

export default App;
