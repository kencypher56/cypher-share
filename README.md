<div align="center">
  <h1>
    <img src="https://raw.githubusercontent.com/kencypher56/cypher-share/main/assets/logo.png" alt="Cypher-Share Logo" width="80" height="80" style="vertical-align: middle;">
    <span style="color: #ff4d4d;">⚡ CYPHER-SHARE ⚡</span>
  </h1>
  <p><strong>Peer‑to‑peer file transfer over local networks – with a simple 6‑digit PIN handshake and a mad‑scientist CLI.</strong></p>
  <p>
    <a href="https://github.com/kencypher56/cypher-share/stargazers"><img src="https://img.shields.io/github/stars/kencypher56/cypher-share?style=for-the-badge&logo=github&color=ffd700" alt="Stars"></a>
    <a href="https://github.com/kencypher56/cypher-share/network/members"><img src="https://img.shields.io/github/forks/kencypher56/cypher-share?style=for-the-badge&logo=github&color=blue" alt="Forks"></a>
    <a href="https://github.com/kencypher56/cypher-share/issues"><img src="https://img.shields.io/github/issues/kencypher56/cypher-share?style=for-the-badge&logo=github&color=red" alt="Issues"></a>
    <a href="https://github.com/kencypher56/cypher-share/blob/main/LICENSE"><img src="https://img.shields.io/github/license/kencypher56/cypher-share?style=for-the-badge&logo=mit&color=brightgreen" alt="License"></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.11-blue?style=for-the-badge&logo=python" alt="Python 3.11"></a>
  </p>
  <br>
  <img src="https://raw.githubusercontent.com/kencypher56/cypher-share/main/assets/demo.gif" alt="Cypher-Share Demo" width="800">
</div>

---

## 🧪 **What is Cypher-Share?**

Cypher‑Share lets you send files and folders between devices on the **same WiFi or Ethernet network** without cloud services, USB sticks, or manual IP configuration. Just pick a 6‑digit PIN on the sender, enter it on the receiver, and watch the data flow – accompanied by a dramatic, emoji‑filled terminal straight from a **Frankenstein laboratory**.

> **“It’s alive! ALIVE!”**  
> — Dr. Frankenstein (probably)

---

## ✨ **Key Features**

<div style="display: flex; flex-wrap: wrap; gap: 20px; justify-content: center;">
  <div style="border: 1px solid #444; border-radius: 10px; padding: 15px; width: 250px; background: #1e1e1e;">
    <h3>🔍 Zero‑conf discovery</h3>
    <p>mDNS/Zeroconf automatically finds the sender – no IP addresses needed.</p>
  </div>
  <div style="border: 1px solid #444; border-radius: 10px; padding: 15px; width: 250px; background: #1e1e1e;">
    <h3>🔐 PIN‑based handshake</h3>
    <p>A simple 6‑digit code secures the session.</p>
  </div>
  <div style="border: 1px solid #444; border-radius: 10px; padding: 15px; width: 250px; background: #1e1e1e;">
    <h3>📁 Send anything</h3>
    <p>Files, folders, entire directory trees – preserved structure.</p>
  </div>
  <div style="border: 1px solid #444; border-radius: 10px; padding: 15px; width: 250px; background: #1e1e1e;">
    <h3>📊 Live progress</h3>
    <p>Overall and per‑file progress bars, speed, ETA – all animated.</p>
  </div>
  <div style="border: 1px solid #444; border-radius: 10px; padding: 15px; width: 250px; background: #1e1e1e;">
    <h3>🔄 Resume interrupted transfers</h3>
    <p>Pick up where you left off, even after a crash.</p>
  </div>
  <div style="border: 1px solid #444; border-radius: 10px; padding: 15px; width: 250px; background: #1e1e1e;">
    <h3>🧾 Transfer logging</h3>
    <p>Everything saved to <code>~/cypher-share.log</code>.</p>
  </div>
  <div style="border: 1px solid #444; border-radius: 10px; padding: 15px; width: 250px; background: #1e1e1e;">
    <h3>🖥️ System info</h3>
    <p>CPU, RAM, GPU with coloured usage bars.</p>
  </div>
  <div style="border: 1px solid #444; border-radius: 10px; padding: 15px; width: 250px; background: #1e1e1e;">
    <h3>🎨 Frankenstein UI</h3>
    <p>Narrative logs, emojis, lightning bolts – a “living” terminal.</p>
  </div>
  <div style="border: 1px solid #444; border-radius: 10px; padding: 15px; width: 250px; background: #1e1e1e;">
    <h3>🌍 Cross‑platform</h3>
    <p>Linux, macOS, Windows – works everywhere.</p>
  </div>
</div>

---

## 🧰 **Tech Stack**

| Component           | Technology                                                                 |
|---------------------|----------------------------------------------------------------------------|
| **Language**        | Python 3.11                                                                |
| **Discovery**       | `zeroconf` (mDNS)                                                          |
| **Network**         | TCP sockets (custom protocol)                                              |
| **CLI & Animation** | `rich` + `questionary` + `prompt_toolkit`                                  |
| **Resume & Logging**| JSON files + Python `logging`                                              |
| **QR Codes**        | `qrcode` (optional)                                                        |
| **System Info**     | `psutil`                                                                   |

---

## ⚙️ **How It Works (The Experiment)**

1. **Sender** chooses files/folders → generates a random 6‑digit PIN → advertises itself via **mDNS** (service `_cypher-share._tcp.local.`) with the PIN in TXT records.
2. **Receiver** enters the PIN → scans the network for matching services → connects to the sender’s TCP port.
3. **Handshake**:
   - Sender sends a **metadata JSON** (file list, sizes, device name).
   - Receiver replies with **resume info** (which files are partially received) and its own device name.
4. **File transfer** begins – each file is streamed in chunks, with progress updated live on both ends.
5. On completion (or interruption), transfer is logged and resume state is saved.

### 📡 Protocol Details

All JSON messages are **length‑prefixed** (4‑byte big‑endian header) to avoid truncation.

**Metadata (sender → receiver)**
```json
{
  "total_files": 42,
  "total_size": 1234567890,
  "files": [
    {"rel_path": "docs/report.pdf", "size": 1048576},
    ...
  ],
  "device": "lonely-igorr",
  "pin": "782579"
}
```

**Resume info (receiver → sender)**
```json
{
  "device": "vengeful-dalek",
  "docs/report.pdf": {"transferred": 524288},
  ...
}
```

---

## 🚀 **Why Use Cypher-Share?**

- ✅ **No internet required** – works entirely on your local network.
- ✅ **No IP addresses to type** – just a 6‑digit PIN.
- ✅ **Fast** – direct TCP transfer, no middleman.
- ✅ **Resilient** – resumes interrupted transfers automatically.
- ✅ **Fun** – immersive CLI makes file transfers feel like a mad experiment.

---

## 📦 **Installation**

### One‑click setup (recommended)

```bash
git clone https://github.com/kencypher56/cypher-share.git
cd cypher-share
python setup.py
```

The `setup.py` script will:
- Detect your OS and architecture.
- Download and install **Miniconda** if not present.
- Create a conda environment `cypher-share` with Python 3.11.
- Install all dependencies from `requirements.txt`.
- Print activation instructions.

After it finishes, activate the environment:

```bash
conda activate cypher-share
```

### Manual setup (if you prefer venv)

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

---

## 🕹️ **Usage**

Run the tool:

```bash
python run.py
```

You’ll be greeted by the banner and the main menu (arrow‑key navigable):

```
? What experiment shall we run?
  ⚡ Send Experiment
  ⚡ Receive Experiment
  📡 System Inspection
  ⚡ Exit Laboratory
```

### 📤 Sending files

1. Choose **Send Experiment**.
2. Type or tab‑complete paths to files/folders (empty line to finish).
3. The system generates a device name (e.g. `lonely-igorr`) and a 6‑digit PIN.
4. Wait for a receiver to connect – progress bars and logs will appear.

### 📥 Receiving files

1. Choose **Receive Experiment**.
2. Enter the 6‑digit PIN shown on the sender.
3. The tool scans for the sender, connects, and starts downloading.
4. All files are saved to `~/Desktop/cypher-share/`, preserving folder structure.

### 🖥️ System inspection

Select **System Inspection** to see OS, CPU, RAM, and GPU information with colourful usage bars.

---

## 📁 **Project Structure**

```
cypher-share/
├── setup.py              # One‑click environment setup (Miniconda + deps)
├── requirements.txt      # Python dependencies
├── run.py                # Main entry point
├── design.py             # Live UI, animations, narrative helpers
├── interactive.py        # Menus, file selector, PIN prompt
├── sysinfo.py            # System information display
├── name_generator.py     # Random Frankenstein/Doctor Who names
├── pin_generator.py      # 6‑digit PIN generation
├── operations.py         # File walking, size calculation, human‑readable sizes
├── protocol.py           # Length‑prefixed JSON send/receive
├── send.py               # Sender logic (Zeroconf + TCP)
├── receive.py            # Receiver logic (Zeroconf + TCP)
├── resume.py             # Resume state management
├── logger.py             # Transfer history logging
└── network.py            # Local IP and subnet helpers
```

---

## 📝 **Logging & Resume**

- All transfers are logged to `~/cypher-share.log` with timestamps, device names, and status.
- Resume information is stored in `~/.cypher-share-resume.json`. If a transfer is interrupted, the receiver can resume from the last byte on the next attempt.

---

## 🧪 **Troubleshooting**

### “No sender found with that PIN”
- Ensure both devices are on the **same local network** (WiFi/Ethernet).
- Check that **mDNS** is allowed (port 5353 UDP). Some firewalls may block it.
- Try disabling firewalls temporarily.

### Connection reset / metadata error
- This can happen if the network is unstable or the receiver closes the connection. The protocol now handles length‑prefixed JSON to avoid truncation; retry the transfer.

### Conda installation fails
- If the automatic Miniconda download fails, you can install Miniconda manually from [here](https://docs.conda.io/en/latest/miniconda.html) and then rerun `python setup.py`.

### The live UI looks glitchy
- Make sure your terminal supports **true colour** and is wide enough (at least 100 columns). Use a modern terminal like Windows Terminal, GNOME Terminal, or iTerm2.

---

## 🤝 **Contributing**

Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change. Keep the Frankenstein spirit alive 😈

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 **License**

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">
  <h3>
    <a href="https://github.com/kencypher56/cypher-share">📦 GitHub Repository</a> •
    <a href="https://github.com/kencypher56/cypher-share/issues">🐛 Report Bug</a> •
    <a href="https://github.com/kencypher56/cypher-share/issues">✨ Request Feature</a>
  </h3>
  <p>Made with ⚡ by <a href="https://github.com/kencypher56">kencypher56</a></p>

</div>
