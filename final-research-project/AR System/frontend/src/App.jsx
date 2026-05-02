import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import ThreatMonitor from './pages/ThreatMonitor';
import MonitoringSystem from './pages/MonitoringSystem';

import PrivacyVault from './pages/PrivacyVault';
import IncidentLog from './pages/IncidentLog';

function App() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    useEffect(() => {
        // Check session persistence
        const token = localStorage.getItem('token');
        if (token) setIsAuthenticated(true);
    }, []);

    const handleLogin = (isSuccess) => {
        setIsAuthenticated(isSuccess);
    };

    return (
        <Router>
            <Routes>
                <Route path="/login" element={!isAuthenticated ? <Login onLogin={handleLogin} /> : <Navigate to="/" />} />

                {/* Protected Routes */}
                {isAuthenticated && (
                    <Route element={<Layout />}>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/threats" element={<ThreatMonitor />} />
                        <Route path="/monitoring" element={<MonitoringSystem />} />
                        <Route path="/vault" element={<PrivacyVault />} />
                        <Route path="/logs" element={<IncidentLog />} />
                    </Route>
                )}

                <Route path="*" element={<Navigate to={isAuthenticated ? "/" : "/login"} />} />
            </Routes>
        </Router>
    );
}

export default App;
