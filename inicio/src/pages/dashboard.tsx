import React, { useState } from 'react';
import { Pill, ClipboardList, DollarSign, Users, ShoppingCart, BarChart, MapPin, Truck, PhoneCall } from 'lucide-react';

type Role = 'Farmacéutico' | 'Técnico' | 'Cajero' | 'Gerente' | 'Repartidor';

interface App {
  name: string;
  icon: React.ElementType;
  roles: Role[];
}

const roles: Role[] = ['Farmacéutico', 'Técnico', 'Cajero', 'Gerente', 'Repartidor'];

const apps: App[] = [
  { name: 'Inventario', icon: ShoppingCart, roles: ['Farmacéutico', 'Técnico', 'Gerente'] },
  { name: 'Dispensación', icon: Pill, roles: ['Farmacéutico', 'Técnico'] },
  { name: 'Ventas', icon: DollarSign, roles: ['Cajero', 'Gerente'] },
  { name: 'Recursos Humanos', icon: Users, roles: ['Gerente'] },
  { name: 'Reportes', icon: BarChart, roles: ['Gerente'] },
  { name: 'Recetas', icon: ClipboardList, roles: ['Farmacéutico', 'Técnico'] },
  { name: 'Rutas de Entrega', icon: MapPin, roles: ['Repartidor', 'Gerente'] },
  { name: 'Estado de Entregas', icon: Truck, roles: ['Repartidor', 'Gerente', 'Cajero'] },
  { name: 'Contacto Cliente', icon: PhoneCall, roles: ['Repartidor', 'Cajero'] },
];

export default function DashboardFarmacia() {
  const [selectedRole, setSelectedRole] = useState<Role | ''>('');

  const availableApps = apps.filter(app => app.roles.includes(selectedRole as Role));

  const openApp = (appName: string) => {
    console.log(`Abriendo la aplicación: ${appName}`);
  };

  return (
    <div className="min-h-screen bg-white text-purple-800 p-8">
      <h1 className="text-4xl font-bold mb-8 text-center">Dashboard Barriofarma</h1>
      
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <label htmlFor="role" className="block text-sm font-medium mb-2">Selecciona tu rol:</label>
          <select
            id="role"
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value as Role)}
            className="w-full p-2 border border-purple-700 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-700 bg-white text-purple-800"
          >
            <option value="">Selecciona un rol</option>
            {roles.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        </div>

        {selectedRole ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {availableApps.map((app) => (
              <button
                key={app.name}
                onClick={() => openApp(app.name)}
                className="p-4 bg-purple-700 hover:bg-purple-800 text-white rounded-lg transition-colors duration-200 flex flex-col items-center justify-center"
              >
                <app.icon className="w-12 h-12 mb-2" />
                <span className="text-lg font-medium">{app.name}</span>
              </button>
            ))}
          </div>
        ) : (
          <p className="text-center text-purple-700 mt-8">
            Por favor, selecciona un rol para ver las aplicaciones disponibles.
          </p>
        )}
      </div>
    </div>
  );
}