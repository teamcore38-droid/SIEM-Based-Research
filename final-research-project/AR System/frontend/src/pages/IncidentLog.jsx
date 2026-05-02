import React, { useState, useEffect } from 'react';
import { History, Search, Filter, AlertCircle, CheckCircle, XCircle } from 'lucide-react';

const IncidentLog = () => {
    const [events, setEvents] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [filter, setFilter] = useState('ALL'); // ALL, DANGER, INFO

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const res = await fetch('http://localhost:5000/api/history');
                const data = await res.json();
                setEvents(data);
            } catch (error) {
                console.error("Error fetching history:", error);
            }
        };
        fetchHistory();
        const interval = setInterval(fetchHistory, 3000);
        return () => clearInterval(interval);
    }, []);

    const filteredEvents = events.filter(e => {
        const matchesSearch = e.src_ip.includes(searchTerm) || e.message.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesFilter = filter === 'ALL' || e.event_type === filter;
        return matchesSearch && matchesFilter;
    });

    return (
        <div className="p-8 space-y-6 animate-in fade-in duration-500 h-screen flex flex-col">
            {/* Header */}
            <div>
                <h2 className="text-3xl font-display font-bold text-white tracking-wide">
                    INCIDENT LOG
                </h2>
                <p className="text-slate-400 mt-1 flex items-center gap-2">
                    <History className="w-4 h-4 text-blue-400" />
                    Historical Forensics & AI Decisions
                </p>
            </div>

            {/* Controls */}
            <div className="flex gap-4 bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-3 w-5 h-5 text-slate-500" />
                    <input
                        type="text"
                        placeholder="Search IP, threats, or keywords..."
                        className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="flex gap-2">
                    {['ALL', 'DANGER', 'INFO'].map(f => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-4 py-2 rounded-lg font-mono text-sm border transition-colors ${filter === f
                                    ? 'bg-blue-600 border-blue-500 text-white'
                                    : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-white'
                                }`}
                        >
                            {f}
                        </button>
                    ))}
                </div>
            </div>

            {/* Table */}
            <div className="flex-1 overflow-hidden bg-slate-900 border border-slate-800 rounded-xl shadow-2xl flex flex-col">
                <div className="overflow-auto custom-scrollbar flex-1">
                    <table className="w-full text-left border-collapse relative">
                        <thead className="sticky top-0 bg-slate-950 z-10 shadow-md">
                            <tr className="text-slate-400 text-xs font-mono uppercase tracking-wider">
                                <th className="px-6 py-4 font-medium border-b border-slate-800">Time</th>
                                <th className="px-6 py-4 font-medium border-b border-slate-800">Severity</th>
                                <th className="px-6 py-4 font-medium border-b border-slate-800">Decision</th>
                                <th className="px-6 py-4 font-medium border-b border-slate-800">Device IP</th>
                                <th className="px-6 py-4 font-medium border-b border-slate-800">Details</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {filteredEvents.map((e, index) => (
                                <tr key={index} className="hover:bg-slate-800/30 transition-colors">
                                    <td className="px-6 py-4 text-slate-500 font-mono text-xs whitespace-nowrap">
                                        {e.timestamp}
                                    </td>
                                    <td className="px-6 py-4">
                                        {e.event_type === 'DANGER' ? (
                                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-500 border border-red-500/20">
                                                <XCircle className="w-3 h-3" /> CRITICAL
                                            </span>
                                        ) : (
                                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-500 border border-blue-500/20">
                                                <CheckCircle className="w-3 h-3" /> SYSTEM
                                            </span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className={`font-bold text-sm ${e.decision === 'ISOLATE' ? 'text-orange-400' :
                                                e.decision === 'QUARANTINE' ? 'text-red-500' :
                                                    e.decision === 'ROLLBACK' ? 'text-emerald-400' : 'text-slate-400'
                                            }`}>
                                            {e.decision}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 font-mono text-sm text-slate-300">
                                        {e.src_ip}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-400 truncate max-w-xs">
                                        {e.message}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div className="p-4 bg-slate-950 border-t border-slate-800 text-right text-xs text-slate-500 font-mono">
                    Showing {filteredEvents.length} records
                </div>
            </div>
        </div>
    );
};

export default IncidentLog;
