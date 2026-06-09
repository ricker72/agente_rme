# Installation Guide — RME Map AI Agent v2.0

## Requirements

- **Python**: 3.9 or higher
- **Operating System**: Windows, macOS, or Linux
- **Ollama**: For AI-powered map generation (optional but recommended)

## Quick Install

### 1. Clone or Download

```bash
git clone <repository-url>
cd agente_rme
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Installer

```bash
# Check system status
python installer/setup.py --check-only

# Install missing dependencies
python installer/setup.py --install-deps

# Full install with directory creation
python installer/setup.py
```

### 4. Start the Application

```bash
# GUI mode
python main.py

# CLI mode
python cli.py info
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| customtkinter | >=5.2.1 | GUI framework (dark theme) |
| ollama | >=0.1.9 | Local AI model integration |
| requests | >=2.31.0 | HTTP client (Ollama fallback) |
| Pillow | >=10.1.0 | Image rendering/previews |
| lxml | >=4.9.3 | XML parsing (items.xml, monsters, NPCs) |
| numpy | >=1.26.0 | RAG vector operations |
| pyyaml | >=6.0 | YAML config files |

### Optional Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| sentence-transformers | >=2.2.2 | Embeddings for RAG system |
| pytest | >=7.0 | Testing framework |
| pytest-cov | >=4.0 | Coverage reporting |

## Configuration

### First Run

On first launch, the GUI will show a setup wizard asking for:

1. **Tibia Client Path**: Path to `appearances.dat` or Tibia client folder
2. **items.xml Path**: Path to server's `items.xml` file
3. **Monsters Folder**: Path to `data/monster/` folder
4. **NPCs Folder**: Path to `data/npc/` folder
5. **Mounts Folder** (optional): Path to `data/mounts/` folder

### Configuration File

Settings are stored in `config.json`:

```json
{
  "tibia_client_path": "/path/to/tibia",
  "items_xml_path": "/path/to/items.xml",
  "monsters_folder": "/path/to/data/monster",
  "npcs_folder": "/path/to/data/npc",
  "mounts_folder": "",
  "configured": true,
  "last_model": "llama3"
}
```

### Reconfiguration

To reconfigure after initial setup:
1. Open the GUI
2. Click "Reconfigurar" in the top bar
3. Update paths as needed

## Ollama Setup (AI Features)

For AI-powered generation, install Ollama:

```bash
# Windows: Download from https://ollama.com
# macOS:
brew install ollama

# Linux:
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama
ollama serve

# Pull a model
ollama pull llama3
```

## Directory Structure

The installer creates these directories:

```
agente_rme/
├── output/          # Generated maps, scripts, previews
├── cache/           # Item/monster/NPC caches
├── config/          # Environment configs (dev, prod)
├── data/            # Blueprints, embeddings
├── logs/            # Application logs
├── exports/         # Exported artifacts
└── release/         # Release packages
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=core --cov=cli --cov-report=term-missing

# Run the production test suite
python installer/run_tests.py --coverage --verbose

# Minimum coverage target: 80%
```

## Troubleshooting

### PIL/Pillow not found

```bash
pip install Pillow
```

### Ollama not available

The application works without Ollama but cannot use AI generation.
Install Ollama and ensure it's running on `localhost:11434`.

### XML parsing errors

Ensure you have `lxml` installed:
```bash
pip install lxml
```

### GUI not displaying

Ensure `customtkinter` is installed:
```bash
pip install customtkinter
```

## Uninstall

```bash
# Remove generated files
rm -rf output/ cache/ logs/ exports/

# Remove Python packages
pip uninstall customtkinter ollama requests Pillow lxml numpy pyyaml