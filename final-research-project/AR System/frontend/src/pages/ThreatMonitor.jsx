import React, { useState, useEffect } from 'react';
import { Shield, Server, AlertTriangle, CheckCircle, Lock, Power, RefreshCw, Trash2, Plus, X } from 'lucide-react';

const ThreatMonitor = () => {
    // State for Real Devices
    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);

    // Add Device State
    const [showAddModal, setShowAddModal] = useState(false);
    const [newDeviceIp, setNewDeviceIp] = useState('');
    const [isAdding, setIsAdding] = useState(false);

    // Fetch Devices from Backend
    const fetchDevices = async () => {
        try {
            const res = await fetch('http://localhost:5000/api/devices');
            const data = await res.json();
            setDevices(data);
            setLoading(false);
        } catch (err) {
            console.error("Failed to fetch devices", err);
        }
    };

    useEffect(() => {
        fetchDevices();
        const interval = setInterval(fetchDevices, 2000); // Poll status every 2s
        return () => clearInterval(interval);
    }, []);

    // Handle Isolation Toggle
    const toggleIsolation = async (id, currentStatus) => {
        try {
            const action = currentStatus === 'ISOLATED' ? 'RELEASE' : 'ISOLATE';
            await fetch('http://localhost:5000/api/isolate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ device_id: id, action })
            });
            // Optimistic update
            setDevices(prev => prev.map(d =>
                d.id === id ? { ...d, status: action === 'ISOLATE' ? 'ISOLATED' : 'SAFE' } : d
            ));
        } catch (err) {
            console.error("Action failed:", err);
        }
    };

    // Handle Add Device
    const handleAddDevice = async () => {
        if (!newDeviceIp) return;
        setIsAdding(true);
        try {
            const res = await fetch('http://localhost:5000/api/devices/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ ip: newDeviceIp, type: "Manual Entry" })
            });
            if (res.ok) {
                setShowAddModal(false);
                setNewDeviceIp('');
                fetchDevices(); // Refresh list
            }
        } catch (err) {
            console.error("Add failed:", err);
        } finally {
            setIsAdding(false);
        }
    };

    // Handle Remove Device
    const handleRemoveDevice = async (ip) => {
        if (!window.confirm(`Are you sure you want to remove device ${ip}?`)) return;
        try {
            await fetch('http://localhost:5000/api/devices/remove', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ ip })
            });
            fetchDevices(); // Refresh list
        } catch (err) {
            console.error("Remove failed:", err);
        }
    };

    return (
        <div className="space-y-6 text-slate-100 h-screen flex flex-col p-8 animate-in fade-in duration-500">
            {/* Header Area */}
            <div className="flex justify-between items-center bg-slate-800/90 p-6 rounded-xl shadow-lg border border-slate-700">
                <div>
                    <h2 className="text-2xl font-display font-bold text-white flex items-center gap-3">
                        <Lock className="text-amber-500 w-6 h-6" /> Device Quarantine Manager
                    </h2>
                    <p className="text-slate-400 font-mono text-sm mt-1">
                        Active Threat Response Interface (Manual Override)
                    </p>
                </div>
                <div className="flex gap-4 items-center">
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-bold transition-all shadow-lg hover:shadow-blue-500/25">
                        <Plus className="w-4 h-4" /> Add Device
                    </button>
                    <div className="h-8 w-px bg-slate-600 mx-2"></div>
                    <StatusBadge label="Total Agents" value={devices.length} color="text-blue-400" />
                    <StatusBadge label="Compromised" value={devices.filter(d => d.status === 'CRITICAL').length} color="text-red-500" />
                    <StatusBadge label="Isolated" value={devices.filter(d => d.status === 'ISOLATED' || d.status === 'QUARANTINED').length} color="text-amber-500" />
                </div>
            </div>

            {/* Device Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl flex-1 overflow-hidden flex flex-col">
                <div className="overflow-auto custom-scrollbar flex-1">
                    <table className="w-full text-left font-mono">
                        <thead className="bg-slate-950 sticky top-0 z-10 shadow-md">
                            <tr className="text-slate-400 text-xs uppercase tracking-wider">
                                <th className="p-4 border-b border-slate-800">Device IP</th>
                                <th className="p-4 border-b border-slate-800">Current Status</th>
                                <th className="p-4 border-b border-slate-800">Risk Score</th>
                                <th className="p-4 border-b border-slate-800">Last Activity</th>
                                <th className="p-4 border-b border-slate-800 text-right">Controls</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {devices.length === 0 && !loading && (
                                <tr><td colSpan="5" className="p-12 text-center text-slate-500 italic">No devices found in inventory.</td></tr>
                            )}
                            {devices.map((device) => (
                                <tr key={device.id} className="hover:bg-slate-800/30 transition-colors group">
                                    <td className="p-4 flex items-center gap-3 font-bold text-slate-200">
                                        <Server className={`w-4 h-4 ${device.status === 'CRITICAL' ? 'text-red-500 animate-pulse' : 'text-slate-500'}`} />
                                        {device.ip}
                                    </td>

                                    <td className="p-4">
                                        <StatusTag status={device.status} />
                                    </td>

                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden border border-slate-700">
                                                <div
                                                    className={`h-full rounded-full transition-all duration-500 ${device.score > 0.8 ? 'bg-red-500 w-[90%]' :
                                                        device.score > 0.5 ? 'bg-amber-500 w-[60%]' : 'bg-emerald-500 w-[10%]'
                                                        }`}
                                                ></div>
                                            </div>
                                            <span className="text-xs text-slate-400">{device.score ? device.score.toFixed(2) : "0.00"}</span>
                                        </div>
                                    </td>

                                    <td className="p-4 text-slate-400 text-xs">
                                        {device.lastSeen || 'Just now'}
                                    </td>

                                    <td className="p-4 text-right flex justify-end items-center gap-2">
                                        {device.status === 'QUARANTINED' ? (
                                            <span className="flex items-center justify-end gap-1 text-red-400 font-bold text-xs uppercase cursor-not-allowed opacity-80 px-3 py-1 bg-red-950/30 rounded border border-red-900/50">
                                                <Lock className="w-3 h-3" /> Locked by AI
                                            </span>
                                        ) : (
                                            <button
                                                onClick={() => toggleIsolation(device.id, device.status)}
                                                className={`text-xs font-bold px-3 py-1.5 rounded shadow transition-all flex items-center gap-2
                                                    ${device.status === 'ISOLATED'
                                                        ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/20'
                                                        : 'bg-red-600 hover:bg-red-500 text-white shadow-red-900/20'
                                                    }`}
                                            >
                                                {device.status === 'ISOLATED' ? <UnlockIcon /> : <PowerIcon />}
                                                {device.status === 'ISOLATED' ? 'RELEASE' : 'ISOLATE'}
                                            </button>
                                        )}

                                        <button
                                            onClick={() => handleRemoveDevice(device.ip)}
                                            className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-950/30 rounded transition-colors"
                                            title="Remove Device"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Add Device Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-md shadow-2xl">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold text-white">Add New Device</h3>
                            <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-white"><X className="w-5 h-5" /></button>
                        </div>
                        <input
                            autoFocus
                            type="text"
                            placeholder="IP Address (e.g. 192.168.1.55)"
                            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none mb-6 font-mono"
                            value={newDeviceIp}
                            onChange={(e) => setNewDeviceIp(e.target.value)}
                        />
                        <div className="flex justify-end gap-3">
                            <button
                                onClick={() => setShowAddModal(false)}
                                disabled={isAdding}
                                className="px-4 py-2 text-slate-400 hover:text-white font-medium disabled:opacity-50">
                                Cancel
                            </button>
                            <button
                                onClick={handleAddDevice}
                                disabled={isAdding}
                                className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold shadow-lg shadow-blue-900/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
                                {isAdding && <RefreshCw className="w-4 h-4 animate-spin" />}
                                {isAdding ? 'Adding...' : 'Add Device'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// UI Helpers
const StatusBadge = ({ label, value, color }) => (
    <div className="text-center px-4 py-1 bg-slate-950/50 rounded border border-slate-800">
        <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">{label}</p>
        <p className={`text-lg font-bold ${color}`}>{value}</p>
    </div>
);

const StatusTag = ({ status }) => {
    const styles = {
        SAFE: "bg-emerald-900/30 text-emerald-400 border-emerald-800",
        CRITICAL: "bg-red-900/30 text-red-400 border-red-800 animate-pulse",
        ISOLATED: "bg-amber-900/30 text-amber-400 border-amber-800",
        QUARANTINED: "bg-purple-900/30 text-purple-400 border-purple-800"
    };
    return (
        <span className={`px-2 py-0.5 rounded text-xs font-bold border border-opacity-50 ${styles[status] || styles.SAFE}`}>
            {status}
        </span>
    );
};

const UnlockIcon = () => <RefreshCw className="w-3 h-3" />;
const PowerIcon = () => <Power className="w-3 h-3" />;

export default ThreatMonitor;
