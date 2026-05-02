# 🔌 How to Connect ARS to Wazuh

You have generated the necessary configuration files in this folder. Follow these 2 steps to verify the connection.

## Step 1: Configure Your PC (The Agent)
1. Open this file on your computer: `C:\Program Files (x86)\ossec-agent\ossec.conf` (You need Administrator Notepad).
2. Open the file `agent_ossec_snippet.xml` from this folder.
3. Copy the `<localfile>` block and paste it at the bottom of your `ossec.conf` (inside the `<ossec_config>` tags).
4. Save and Restart the Wazuh Agent service:
   - PowerShell: `Restart-Service -Name WazuhSvc`

## Step 2: Configure the Dashboard (The Manager)
1. Log into your **Wazuh Dashboard** (Admin).
2. Go to **Management > Rules > Custom Rules**.
   - Click "Manage Files" (top right) -> `local_rules.xml`.
   - Copy-paste the content of `manager_rules.xml` into this file.
   - Save.
3. Go to **Management > Decoders > Custom Decoders**.
   - Click "Manage Files" -> `local_decoder.xml`.
   - Copy-paste the content of `manager_decoders.xml` into this file.
   - Save.
4. Click **Restart Manager** (top right corner).

## ✅ Verification
1. Run the `START_ARS_SYSTEM.bat` on your PC.
2. Go to Wazuh Dashboard -> **Security Events**.
3. Search for: `rule.groups:ars_defense_system`.
4. You should see your AI Model's decisions appearing live in the dashboard!
