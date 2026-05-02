import React, { useState, useEffect } from 'react';
import { Shield, Lock, Eye, CheckCircle, AlertTriangle } from 'lucide-react';

const PrivacyVault = () => {
    const [logs, setLogs] = useState([]);

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const res = await fetch('http://localhost:5000/api/privacy');
                const data = await res.json();
                setLogs(data.reverse()); // Newest first
            } catch (error) {
                console.error("Error fetching privacy logs:", error);
            }
        };

        fetchLogs();
        const interval = setInterval(fetchLogs, 2000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="p-8 space-y-6 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="text-3xl font-display font-bold text-white tracking-wide">
                        PRIVACY VAULT
                    </h2>
                    <p className="text-slate-400 mt-1 flex items-center gap-2">
                        <Lock className="w-4 h-4 text-emerald-400" />
                        HIPAA/GDPR Compliance Module
                    </p>
                </div>
                <div className="bg-emerald-500/10 border border-emerald-500/30 px-4 py-2 rounded-lg flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                    <span className="text-emerald-400 font-mono text-sm">REDACTION ENGINE ACTIVE</span>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-slate-800/50 border border-slate-700 p-6 rounded-xl">
                    <div className="flex items-center gap-3 mb-2">
                        <Shield className="w-5 h-5 text-blue-400" />
                        <span className="text-slate-400 text-sm font-mono">TOTAL PROTECTED</span>
                    </div>
                    <div className="text-3xl font-bold text-white">{logs.length} <span className="text-sm font-normal text-slate-500">records</span></div>
                </div>

                <div className="bg-slate-800/50 border border-slate-700 p-6 rounded-xl">
                    <div className="flex items-center gap-3 mb-2">
                        <AlertTriangle className="w-5 h-5 text-amber-400" />
                        <span className="text-slate-400 text-sm font-mono">PHI ATTEMPTS</span>
                    </div>
                    <div className="text-3xl font-bold text-white">{logs.length} <span className="text-sm font-normal text-slate-500">blocked</span></div>
                </div>
            </div>

            {/* Secure Logs Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
                <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/50 flex items-center gap-2">
                    <Eye className="w-4 h-4 text-slate-400" />
                    <h3 className="text-slate-300 font-mono text-sm">AUDIT TRAIL (OFF-CHAIN)</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-950/50 text-slate-400 text-xs font-mono uppercase tracking-wider">
                                <th className="px-6 py-4 font-medium">Timestamp</th>
                                <th className="px-6 py-4 font-medium">Source IP</th>
                                <th className="px-6 py-4 font-medium">Detection Trigger</th>
                                <th className="px-6 py-4 font-medium text-right">Redacted Content</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            {logs.map((log, index) => (
                                <tr key={index} className="hover:bg-slate-800/30 transition-colors group">
                                    <td className="px-6 py-4 text-slate-400 text-sm font-mono">
                                        {log.timestamp}
                                    </td>
                                    <td className="px-6 py-4 text-blue-400 font-mono text-sm">
                                        {log.src_ip}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-500 border border-amber-500/20">
                                            PHI_PATTERN_MATCH
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="font-mono text-sm text-emerald-400 bg-emerald-950/30 px-3 py-1 rounded inline-block border border-emerald-900">
                                            {log.message.replace("PHI Detected & Redacted: ", "")}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                            {logs.length === 0 && (
                                <tr>
                                    <td colSpan="4" className="px-6 py-12 text-center text-slate-500 font-mono">
                                        No Privacy Violations Detected yet...
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default PrivacyVault;
