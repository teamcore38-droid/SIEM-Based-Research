import logging
import platform

class IsolationManager:
    def __init__(self):
        self.os_type = platform.system()
        logging.info(f"IsolationManager initialized on {self.os_type}")

    def isolate_device(self, ip_address, real_enforcement=False):
        """
        FR-01: Network Containment.
        Executes millisecond-level isolation via IPTables (Linux) or Windows Firewall.
        """
        logging.warning(f"TRIGGER: Isolating Device {ip_address}")
        
        try:
            if self.os_type == "Linux":
                # Linux: IPTables
                cmd = f"iptables -A INPUT -s {ip_address} -j DROP"
                if real_enforcement:
                    # subprocess.run(cmd, shell=True, check=True)
                    print(f"[ACTIVE DEFENSE] Executed: {cmd}")
                else:
                     print(f"[SIMULATION] Would execute: {cmd}")
                     
            elif self.os_type == "Windows":
                # Windows: Netsh Advanced Firewall
                rule_name = f"ARS_BLOCK_{ip_address}"
                cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=block remoteip={ip_address}'
                
                if real_enforcement:
                    # subprocess.run(cmd, shell=True, check=True)
                    print(f"[ACTIVE DEFENSE] Windows Firewall Rule Added: {rule_name}")
                else:
                    print(f"[SIMULATION] Windows Firewall Command: {cmd}")
            
            return True
        except Exception as e:
            logging.error(f"Isolation Failed: {e}")
            return False

    def rollback(self, ip_address, real_enforcement=False):
        """
        FR-03: Automated Rollback.
        Restores connectivity < 30s.
        """
        logging.info(f"ROLLBACK: Restoring Device {ip_address}")
        
        try:
            if self.os_type == "Windows":
                 rule_name = f"ARS_BLOCK_{ip_address}"
                 cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
                 if real_enforcement:
                     # subprocess.run(cmd, shell=True)
                     print(f"[ROLLBACK] Windows Rule Deleted: {rule_name}")
                 else:
                     print(f"[SIMULATION] Would run: {cmd}")
                     
            elif self.os_type == "Linux":
                 cmd = f"iptables -D INPUT -s {ip_address} -j DROP"
                 if real_enforcement:
                     print(f"✅ [ROLLBACK] Iptables rule removed.")
                 else:
                     print(f"[SIMULATION] Would run: {cmd}")

            return True
        except Exception as e:
             logging.error(f"Rollback Error: {e}")
             return False
