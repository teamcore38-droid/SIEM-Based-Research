import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, Activity, Lock, History, Microscope } from 'lucide-react';

const Sidebar = () => {
    const location = useLocation();

    const menuItems = [
        { icon: Activity, label: 'Dashboard', path: '/' },
        { icon: Shield, label: 'Threat Monitor', path: '/threats' },
        { icon: Microscope, label: 'Monitoring System', path: '/monitoring' }, // NEW
        { icon: Lock, label: 'Privacy Vault', path: '/vault' },
        { icon: History, label: 'Incident Log', path: '/logs' },
    ];

    return (
        <div className="h-screen w-64 bg-slate-900 border-r border-slate-700 flex flex-col">
            <div className="p-6 flex flex-col items-center gap-3 border-b border-slate-700">
                <img src="/logo.jpg" alt="MedGuard-X Logo" className="w-16 h-16 object-contain" />
                <h1 className="text-xl font-bold tracking-wider text-white">
                    MEDGUARD-<span className="text-blue-500">X</span>
                </h1>
            </div>

            <nav className="flex-1 px-4 py-8 space-y-2">
                {menuItems.map((item) => (
                    <Link
                        key={item.path}
                        to={item.path}
                        className={`w-full flex items-center gap-4 px-4 py-3 rounded-lg transition-all duration-300 font-mono text-sm
                            ${location.pathname === item.path
                                ? 'bg-blue-600/20 text-blue-400 border-l-2 border-blue-500'
                                : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                            }`}
                    >
                        <item.icon className="w-5 h-5" />
                        {item.label}
                    </Link>
                ))}
            </nav>

            <div className="p-6 border-t border-slate-700">
                <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                    <span className="text-xs font-mono text-slate-400">SYSTEM ONLINE</span>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
