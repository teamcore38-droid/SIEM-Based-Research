import React from 'react';
import { Bell, Search, User } from 'lucide-react';

const Header = () => {
    return (
        <header className="h-16 bg-cyber-dark/95 backdrop-blur-md border-b border-cyber-light flex items-center justify-between px-8 sticky top-0 z-50">
            <div className="flex items-center gap-4 w-96">
                <div className="relative w-full">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-muted" />
                    <input
                        type="text"
                        placeholder="Search logs, IPs, or devices..."
                        className="w-full bg-cyber-light border border-cyber-light rounded-md py-1.5 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-cyber-accent transition-colors font-mono"
                    />
                </div>
            </div>

            <div className="flex items-center gap-6">
                <button className="relative text-cyber-muted hover:text-cyber-accent transition-colors">
                    <Bell className="w-5 h-5" />
                    <span className="absolute -top-1 -right-1 w-2 h-2 bg-cyber-danger rounded-full animate-pulse"></span>
                </button>

                <div className="flex items-center gap-3 pl-6 border-l border-cyber-light">
                    <div className="text-right hidden md:block">
                        <p className="text-sm font-bold text-white">Admin Console</p>
                        <p className="text-xs text-cyber-success font-mono">SECURE CONNECTED</p>
                    </div>
                    <div className="w-8 h-8 bg-cyber-light rounded-full flex items-center justify-center border border-cyber-accent">
                        <User className="w-4 h-4 text-cyber-accent" />
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
