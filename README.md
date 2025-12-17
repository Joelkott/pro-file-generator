# ProPresenter Text to .pro Converter

Convert simple text files into ProPresenter 7 presentation files (.pro) automatically. Perfect for quickly creating worship song presentations from lyrics.

## Features

✅ **Full Text Conversion** - Converts lyrics from txt files to .pro format
✅ **Section Tagging** - Automatically creates cue groups (Verse, Chorus, Bridge, etc.)
✅ **Color Coding** - Auto-assigns colors based on section names
✅ **Template Support** - Uses existing .pro files as formatting templates
✅ **Proper Formatting** - Preserves fonts, colors, and styles from template
✅ **No Capitalization Issues** - Displays text exactly as typed

## Quick Start

### 1. Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd pro-file-generator

# Initialize the ProPresenter7-Proto submodule
git submodule update --init --recursive

# Install dependencies
pip3 install protobuf
# Or if you get an error, use: pip3 install --break-system-packages protobuf

# Generate Python code from proto files
mkdir -p proto_generated
protoc --python_out=proto_generated --proto_path=ProPresenter7-Proto/proto ProPresenter7-Proto/proto/*.proto
```

### 2. Convert a Song

```bash
python3 txt_to_pro.py input.txt template.pro output.pro
```

**Example:**
```bash
python3 txt_to_pro.py example_song.txt template.pro amazing_grace.pro
```

## Input File Format

Create a text file with this simple structure:

```
# Song Title: Amazing Grace

[Verse 1]
Amazing grace how sweet the sound
That saved a wretch like me

I once was lost but now am found
Was blind but now I see

[Chorus]
Amazing grace how sweet the sound
That saved a wretch like me

[Bridge]
When we've been there ten thousand years
Bright shining as the sun
```

### Format Rules

- **Title**: `# Song Title: Your Song Name`
- **Sections**: `[Verse 1]`, `[Chorus]`, `[Bridge]`, `[Ending]`, etc.
- **Slides**: Every 2 lines = 1 slide
- **Spacing**: Blank lines between slides are optional (for readability)

### Section Colors

Sections are automatically color-coded:
- **Verse** → Blue
- **Chorus** → Red/Pink
- **Bridge** → Purple
- **Intro** → Green
- **Ending/Outro** → Orange

## How It Works

1. **Parse** the text file to extract song structure
2. **Load** a template .pro file for formatting
3. **Generate** slides with your lyrics
4. **Apply** section colors and metadata
5. **Output** a complete .pro file ready for ProPresenter

### Technical Details

ProPresenter .pro files use Google Protocol Buffers for encoding. This tool:
- Uses reverse-engineered .proto definitions from [greyshirtguy/ProPresenter7-Proto](https://github.com/greyshirtguy/ProPresenter7-Proto)
- Generates proper RTF formatting for text
- Maintains compatibility with ProPresenter 7.16+

## Project Structure

```
├── txt_to_pro.py                   # Main converter script
├── ProPresenter7-Proto/            # Proto definitions (submodule)
├── example_song.txt                # Example input file
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
└── README.md                       # This file

# Generated during setup (not in repo):
├── proto_generated/                # Generated Python protobuf code
```

## Requirements

- Python 3.9+
- protobuf library
- protoc compiler
- A template .pro file from ProPresenter

## Usage Examples

### Basic Conversion
```bash
python3 txt_to_pro.py song.txt template.pro output.pro
```

### Using Default Output Name
```bash
python3 txt_to_pro.py song.txt template.pro
# Creates song.pro
```

### Decode/Inspect a .pro File
```bash
cd "ProPresenter7-Proto/Proto 7.16"
protoc --decode rv.data.Presentation ./propresenter.proto < file.pro
```

## Troubleshooting

### Text appears in ALL CAPS
The script automatically sets capitalization to `NONE`. If issues persist, check your template file.

### Missing lyrics
Ensure your text file follows the 2-lines-per-slide format and has proper section headers.

### Template not found
Provide the full path to your template .pro file.

## Credits

- **Proto Definitions**: [greyshirtguy/ProPresenter7-Proto](https://github.com/greyshirtguy/ProPresenter7-Proto)
- **ProPresenter**: Renewed Vision
- **Protocol Buffers**: Google

## Disclaimer

⚠️ **Unofficial Tool** - This is a reverse-engineered, unofficial tool. Not affiliated with or endorsed by Renewed Vision.

- Always backup your ProPresenter files
- Test generated files before using in production
- The .proto definitions are community-created and may not be complete

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or pull request.

---

**Made with ❤️ for worship teams**
