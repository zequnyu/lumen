# 🌟 Lumen - AI Ebook Search for Claude Desktop

Transform your ebook collection into an AI-searchable library that works seamlessly with Claude Desktop.

**🐳 Fully Containerized** - Everything runs in Docker containers for complete isolation and easy distribution.

## ⚡ Quick Install

**One command installation:**
```bash
curl -sSL https://raw.githubusercontent.com/your-repo/lumen/main/install.sh | bash
```

**That's it!** Lumen is now installed and ready to use.

**What gets installed:**
- 🐳 **Lumen containers** - All code runs in Docker (nothing on your host)
- 📚 **Ebooks directory** - `~/lumen-ebooks/` (your books)  
- 💾 **Data directory** - `~/.lumen-data/` (indexed metadata)
- ⚡ **Global command** - `lumen` (works from anywhere)

## 🚀 Quick Start

**1. Add your ebooks:**
```bash
# Your ebooks go here (the installer created this folder)
cp your-book.epub ~/lumen-ebooks/
cp your-book.pdf ~/lumen-ebooks/
```

**2. Index your books:**
```bash
lumen index --mode all
```

**3. Start Lumen:**
```bash
lumen start
```

**4. Restart Claude Desktop (CRITICAL):**
```bash
# The installer auto-configured Claude Desktop, but you MUST restart it:
# 1. Quit Claude Desktop completely (Cmd+Q on Mac)
# 2. Wait 2 seconds  
# 3. Reopen Claude Desktop
# 4. Lumen MCP server is now active!
```

**5. Use Claude Desktop:**
Open Claude Desktop and start asking questions about your books! 

Example: *"What does Morgan Housel say about compound interest in The Psychology of Money?"*

## 💡 Daily Usage

```bash
# Add new books and index them
lumen index

# Start when you want to use Claude Desktop
lumen start

# Stop when done (cleans up containers)
lumen stop

# Get help
lumen --help
```

## 📚 Supported Formats

- **EPUB files** - Full support with metadata
- **PDF files** - Full support with metadata

## 🎛️ Advanced Options

**Embedding Models:**
```bash
# Use local embeddings (default, fast, no API key needed)
lumen index --model local

# Use Google Gemini embeddings (better quality, requires API key)
export GEMINI_API_KEY="your-key-here"
lumen index --model gemini
```

**Indexing Modes:**
```bash
# Index only new books (default, fast)
lumen index

# Re-index all books (slower, but ensures everything is up to date)
lumen index --mode all
```

## 🔧 Requirements

- **Docker** - [Install Docker](https://docs.docker.com/get-docker/)
- **Claude Desktop** - [Download Claude Desktop](https://claude.ai/download)
- **macOS/Linux** - Windows support coming soon

## 📁 File Locations

- **Ebooks**: `~/lumen-ebooks/` (add your .epub/.pdf files here)
- **Lumen**: `~/.lumen/` (installation directory)
- **Config**: `~/Library/Application Support/Claude/claude_desktop_config.json`

## 🆘 Troubleshooting

**Claude Desktop not finding books?**
```bash
# 1. Make sure you restarted Claude Desktop after installation
# 2. Check if Lumen is running:
lumen start

# 3. Verify Claude Desktop config was created:
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
# Should show "lumen" MCP server

# 4. Try restarting Claude Desktop again (common fix)
```

**Lumen commands not working?**
```bash
# Check if global command exists:
which lumen
# Should show: /usr/local/bin/lumen

# If not found, try reinstalling:
curl -sSL https://raw.githubusercontent.com/your-repo/lumen/main/install.sh | bash
```

**Want to start fresh?**
```bash
# Remove everything and reinstall
rm -rf ~/.lumen-data ~/lumen-ebooks
sudo rm /usr/local/bin/lumen
curl -sSL https://raw.githubusercontent.com/your-repo/lumen/main/install.sh | bash
```

**Check what's running:**
```bash
docker ps  # Should show lumen containers when active
lumen --help  # Should show available commands
```

## 🚀 That's It!

Drop books in `~/lumen-ebooks/`, run `lumen index`, then `lumen start`, and enjoy AI-powered book search in Claude Desktop!

---

*Built with ❤️ for the Claude Desktop community*