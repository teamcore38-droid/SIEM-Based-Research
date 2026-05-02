import React, { useState } from 'react';
import { Activity, ShieldAlert, Heart, Thermometer, Wind, Wifi, Database, CheckCircle, AlertTriangle } from 'lucide-react';

const IoMTAnalyzer = ({ onClose }) => {
    // Form State
    const [formData, setFormData] = useState({
        device_type: 'ESP32_Pulse_Oximeter',
        ward: 'ICU',
        protocol: 'MQTT',
        criticality: 5,
        life_support: false,
        packet_rate: 50,
        failed_connections: 0,
        attack_type: 'normal',
        attack_severity: 0
    });

    // Result State
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleChange = (e) => {
        const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
        setFormData({ ...formData, [e.target.name]: value });
    };

    const handleAnalyze = async () => {
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const token = localStorage.getItem('token');
            const res = await fetch('http://localhost:5000/api/iomt/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            });
            const data = await res.json();

            if (res.ok) {
                setResult(data);
            } else {
                setError(data.error || "Analysis Failed");
            }
        } catch (err) {
            setError("Connection Error");
        } finally {
            setLoading(false);
        }
    };

    // Helper to get color based on priority
    const getPriorityColor = (p) => {
        if (!p) return 'text-slate-500';
        const colors = {
            'CRITICAL': 'text-red-500 border-red-500 bg-red-950/30',
            'HIGH': 'text-orange-500 border-orange-500 bg-orange-950/30',
            'MEDIUM': 'text-yellow-500 border-yellow-500 bg-yellow-950/30',
            'LOW': 'text-blue-400 border-blue-400 bg-blue-950/30',
            'INFO': 'text-slate-400 border-slate-400 bg-slate-900'
        };
        return colors[p] || 'text-white';
    };

    return (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-300">
            <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-4xl shadow-2xl flex flex-col md:flex-row overflow-hidden max-h-[90vh]">

                {/* LEFT: INPUTS */}
                <div className="flex-1 p-6 overflow-y-auto border-r border-slate-800">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                            <Activity className="text-blue-500" /> Patient Threat Analyzer
                        </h2>
                    </div>

                    <div className="space-y-4">
                        {/* Device Info */}
                        <div className="bg-slate-950/50 p-4 rounded border border-slate-800">
                            <h3 className="text-sm font-bold text-slate-400 uppercase mb-3">Device Configuration</h3>

                            <div className="grid grid-cols-1 gap-3">
                                <label className="block text-xs text-slate-400">Device Type</label>
                                <select name="device_type" value={formData.device_type} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white text-sm">
                                    <option value="ESP32_Pulse_Oximeter">Pulse Oximeter (MAX30102)</option>
                                    <option value="ESP32_Temperature">Temperature Sensor</option>
                                    <option value="ESP32_Fall_Detection">Fall Detector</option>
                                    <option value="ESP32_ECG_Monitor">ECG Monitor</option>
                                </select>

                                <label className="block text-xs text-slate-400">Hospital Ward</label>
                                <select name="ward" value={formData.ward} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white text-sm">
                                    <option value="ICU">ICU (Intensive Care)</option>
                                    <option value="Emergency">Emergency Room</option>
                                    <option value="General_Ward">General Ward</option>
                                    <option value="Home_Care">Home Care</option>
                                </select>

                                <div className="flex gap-4">
                                    <div className="flex-1">
                                        <label className="block text-xs text-slate-400">Protocol</label>
                                        <select name="protocol" value={formData.protocol} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white text-sm">
                                            <option value="MQTT">MQTT</option>
                                            <option value="HTTP">HTTP</option>
                                            <option value="BLE">BLE</option>
                                        </select>
                                    </div>
                                    <div className="flex-1">
                                        <label className="block text-xs text-slate-400">Criticality (1-10)</label>
                                        <input type="number" name="criticality" value={formData.criticality} onChange={handleChange} min="1" max="10" className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white text-sm" />
                                    </div>
                                </div>

                                <label className="flex items-center gap-2 mt-2 cursor-pointer">
                                    <input type="checkbox" name="life_support" checked={formData.life_support} onChange={handleChange} className="w-4 h-4 rounded bg-slate-800" />
                                    <span className="text-sm text-red-400 font-bold">Is Life Support Device?</span>
                                </label>
                            </div>
                        </div>

                        {/* Network Stats */}
                        <div className="bg-slate-950/50 p-4 rounded border border-slate-800">
                            <h3 className="text-sm font-bold text-slate-400 uppercase mb-3">Traffic Simulation</h3>

                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-xs text-slate-400">Est. Attack Type</label>
                                    <select name="attack_type" value={formData.attack_type} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white text-sm">
                                        <option value="normal">Normal Traffic</option>
                                        <option value="ddos">DDoS Attack</option>
                                        <option value="mqtt_injection">MQTT Injection</option>
                                        <option value="ble_spoofing">BLE Spoofing</option>
                                        <option value="mitm_ssl_strip">Man-in-the-Middle</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-400">Attack Severity (0-45)</label>
                                    <input type="number" name="attack_severity" value={formData.attack_severity} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white text-sm" />
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-400">Packet Rate (p/min)</label>
                                    <input type="number" name="packet_rate" value={formData.packet_rate} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white text-sm" />
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-400">Failed Connections</label>
                                    <input type="number" name="failed_connections" value={formData.failed_connections} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white text-sm" />
                                </div>
                            </div>
                        </div>

                        <div className="flex gap-3 pt-2">
                            <button onClick={onClose} className="flex-1 py-3 text-slate-400 hover:text-white font-bold border border-slate-700 rounded hover:bg-slate-800 transition-all">
                                Cancel
                            </button>
                            <button onClick={handleAnalyze} disabled={loading} className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded shadow-lg shadow-blue-900/20 disabled:opacity-50 flex items-center justify-center gap-2">
                                {loading ? 'Computing AI Model...' : 'RUN ANALYSIS'}
                            </button>
                        </div>
                    </div>
                </div>

                {/* RIGHT: RESULTS */}
                <div className="w-[400px] bg-slate-950 p-8 flex flex-col justify-center border-l border-slate-800 relative">
                    {!result ? (
                        <div className="text-center text-slate-500 opacity-50">
                            <Database className="w-16 h-16 mx-auto mb-4" />
                            <p className="text-lg font-mono">Ready to Analyze</p>
                            <p className="text-xs max-w-[200px] mx-auto mt-2">Enter device parameters and traffic stats to predict threat priority.</p>
                        </div>
                    ) : (
                        <div className="animate-in slide-in-from-right duration-500">
                            <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest text-center mb-6">Prediction Result</h3>

                            <div className={`border-4 rounded-full w-40 h-40 mx-auto flex items-center justify-center mb-6 ${getPriorityColor(result.priority)}`}>
                                <div className="text-center">
                                    <p className="text-3xl font-black">{result.priority}</p>
                                    <p className="text-xs font-bold opacity-75">PRIORITY</p>
                                </div>
                            </div>

                            <div className="text-center space-y-4">
                                <div className="bg-slate-900 p-3 rounded border border-slate-800">
                                    <span className="text-slate-400 text-xs">AI Confidence Score</span>
                                    <div className="text-xl font-bold text-white">{result.confidence}%</div>
                                </div>

                                <div className="text-left space-y-2 text-sm bg-slate-900/50 p-4 rounded border border-slate-800">
                                    <p className="text-slate-400 text-xs uppercase font-bold mb-2">Recommendation</p>
                                    {result.priority === 'CRITICAL' && (
                                        <ul className="list-disc pl-4 space-y-1 text-red-400">
                                            <li>IMMEDIATE Isolation Required</li>
                                            <li>Alert Clinical Staff</li>
                                            <li>Initiate Emergency Protocol</li>
                                        </ul>
                                    )}
                                    {result.priority === 'HIGH' && (
                                        <ul className="list-disc pl-4 space-y-1 text-orange-400">
                                            <li>Priority Investigation</li>
                                            <li>Notify SOC Team</li>
                                        </ul>
                                    )}
                                    {result.priority === 'MEDIUM' && (
                                        <ul className="list-disc pl-4 space-y-1 text-yellow-400">
                                            <li>Monitor Closely</li>
                                            <li>Log Incident</li>
                                        </ul>
                                    )}
                                    {result.priority === 'LOW' && (
                                        <ul className="list-disc pl-4 space-y-1 text-blue-400">
                                            <li>Routine Check</li>
                                            <li>No Action Required</li>
                                        </ul>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default IoMTAnalyzer;
