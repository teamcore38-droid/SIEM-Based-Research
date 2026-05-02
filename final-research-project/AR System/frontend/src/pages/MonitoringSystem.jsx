import React, { useState, useEffect } from 'react';
import { Microscope, AlertTriangle, ShieldCheck, Activity } from 'lucide-react';

const MonitoringSystem = () => {
    const [alerts, setAlerts] = useState([]);
    const [stats, setStats] = useState({ CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFO: 0 });

    useEffect(() => {
        const fetchAlerts = async () => {
            try {
                const res = await fetch('http://localhost:5000/api/iomt/alerts');
                const data = await res.json();

                // Sort by time descending
                const sorted = data.slice().reverse();
                setAlerts(sorted);

                // Calculate Counts
                const newStats = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFO: 0 };
                data.forEach(a => {
                    if (newStats[a.priority] !== undefined) {
                        newStats[a.priority]++;
                    }
                });
                setStats(newStats);

            } catch (e) {
                console.error("Failed to fetch IoMT alerts", e);
            }
        };

        fetchAlerts(); // Initial load
        const interval = setInterval(fetchAlerts, 2000); // Polling
        return () => clearInterval(interval);
    }, []);

    const StatCard = ({ title, count, color, icon: Icon }) => (
        <div className={`p-4 rounded-xl border ${color} bg-opacity-10 backdrop-blur-sm flex items-center justify-between`}>
            <div>
                <p className="text-slate-400 text-xs font-bold uppercase tracking-wider">{title}</p>
                <p className="text-3xl font-black text-white mt-1">{count}</p>
            </div>
            <Icon className={`w-8 h-8 opacity-80 ${color.replace('border', 'text').replace('bg', 'text')}`} />
        </div>
    );

    return (
        <div className="space-y-6 text-slate-100 p-6 animate-in fade-in duration-500">
            {/* HEADER */}
            <div className="flex items-center gap-3 mb-8">
                <div className="p-3 bg-blue-600 rounded-lg shadow-lg shadow-blue-500/20">
                    <Microscope className="w-8 h-8 text-white" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-white">IoMT Monitoring System</h1>
                    <p className="text-slate-400">Real-time AI Alert Prioritization & Grouping</p>
                </div>
            </div>

            {/* STATS ROW */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <StatCard
                    title="CRITICAL ALERTS"
                    count={stats.CRITICAL}
                    color="border-red-500 bg-red-900"
                    icon={AlertTriangle}
                />
                <StatCard
                    title="HIGH PRIORITY"
                    count={stats.HIGH}
                    color="border-orange-500 bg-orange-900"
                    icon={Activity}
                />
                <StatCard
                    title="MEDIUM PRIORITY"
                    count={stats.MEDIUM}
                    color="border-yellow-500 bg-yellow-900"
                    icon={ShieldCheck}
                />
                <StatCard
                    title="LOW / INFO"
                    count={stats.LOW + stats.INFO}
                    color="border-blue-500 bg-blue-900"
                    icon={Microscope}
                />
            </div>

            {/* MAIN CONTENT: GROUPED ALERTS */}
            <div className="bg-slate-800/80 border border-slate-700 rounded-xl overflow-hidden shadow-2xl">
                <div className="p-4 border-b border-slate-700 bg-slate-900/50 flex justify-between items-center">
                    <h3 className="font-bold flex items-center gap-2">
                        <ListIcon className="w-5 h-5 text-blue-400" />
                        Live Alert Stream
                    </h3>
                    <span className="text-xs bg-slate-700 px-2 py-1 rounded text-slate-300">
                        Auto-refreshing every 2s
                    </span>
                </div>

                <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-slate-900 text-slate-400 uppercase text-xs sticky top-0 z-10">
                            <tr>
                                <th className="p-4">Time</th>
                                <th className="p-4">Priority Level</th>
                                <th className="p-4">AI Confidence</th>
                                <th className="p-4">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700">
                            {alerts.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="p-8 text-center text-slate-500 italic">
                                        Waiting for AI predictions...
                                    </td>
                                </tr>
                            ) : (
                                alerts.map((alert, idx) => (
                                    <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                                        <td className="p-4 font-mono text-slate-300">{alert.timestamp}</td>
                                        <td className="p-4">
                                            <span className={`px-3 py-1 rounded-full text-xs font-bold border ${alert.priority === 'CRITICAL' ? 'bg-red-900/40 text-red-400 border-red-800' :
                                                    alert.priority === 'HIGH' ? 'bg-orange-900/40 text-orange-400 border-orange-800' :
                                                        alert.priority === 'MEDIUM' ? 'bg-yellow-900/40 text-yellow-400 border-yellow-800' :
                                                            'bg-blue-900/40 text-blue-400 border-blue-800'
                                                }`}>
                                                {alert.priority}
                                            </span>
                                        </td>
                                        <td className="p-4">
                                            <div className="flex items-center gap-2">
                                                <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full rounded-full ${alert.confidence > 80 ? 'bg-green-500' :
                                                                alert.confidence > 50 ? 'bg-yellow-500' : 'bg-red-500'
                                                            }`}
                                                        style={{ width: `${alert.confidence}%` }}
                                                    ></div>
                                                </div>
                                                <span className="font-mono text-xs">{alert.confidence}%</span>
                                            </div>
                                        </td>
                                        <td className="p-4 text-slate-400 text-xs">
                                            {alert.priority === 'CRITICAL' ? 'Requires Immediate Attention' : 'Monitoring Normal Vitals'}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

const ListIcon = (props) => (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
)

export default MonitoringSystem;
