# C3 Blender Add-On

[![Release](https://img.shields.io/github/v/release/abdouthematrix/c3-blender-addon?include_prereleases&label=Latest%20Release)](https://github.com/abdouthematrix/c3-blender-addon/releases/latest)
[![Build Status](https://img.shields.io/github/actions/workflow/status/abdouthematrix/c3-blender-addon/release.yml?label=Build)](https://github.com/abdouthematrix/c3-blender-addon/actions/workflows/release.yml)
[![Downloads](https://img.shields.io/github/downloads/abdouthematrix/c3-blender-addon/total)](https://github.com/abdouthematrix/c3-blender-addon/releases)
[![License](https://img.shields.io/github/license/abdouthematrix/c3-blender-addon)](LICENSE)

A Blender add-on for importing and animating C3 model format files, with support for multiple PHY types and animation keyframe formats.

## 📥 Download

**[⬇️ Download Latest Release](https://github.com/abdouthematrix/c3-blender-addon/releases/latest/download/c3-blender-addon-latest.zip)**

Or browse all releases: [Releases Page](https://github.com/abdouthematrix/c3-blender-addon/releases)

## Features

- **Import C3 Models** - Full support for PHY, PHY3, and PHY4 format variants
- **Animation Support** - Handles XKEY, KKEY, ZKEY, and legacy keyframe formats
- **Shape Key Animation** - Bakes vertex animations to Blender shape keys for smooth playback
- **Texture Loading** - Automatic texture detection and material setup (DDS, TGA, PNG, JPG)
- **Multiple PHY Support** - Imports all PHY objects from a single C3 file into organized collections
- **Animation Replacement** - Re-import animations on existing meshes without reimporting geometry

## Installation

1. **Download** the latest release zip file from the link above
2. In Blender, go to `Edit > Preferences > Add-ons`
3. Click `Install` and select the downloaded zip file
4. Enable the add-on by checking the box next to "Import-Export: C3 Add-On"

**Note:** Do not unzip the file - Blender will install it directly from the zip.

## Usage

### Importing a C3 Model

1. Go to the top menu bar and click `C3 Add-On > Import .C3 Model`
2. Browse to your `.c3` file and select it
3. Options:
   - **New Scene** - Import into a new scene (enabled by default)
   - **debugpy** - Enable remote debugging (for development)
4. Click `Import .C3 Model`

The add-on will:
- Create a collection named after the file
- Import all PHY objects as separate sub-collections
- Automatically load matching textures from the same directory
- Bake animations to shape keys if motion data is present
- Set up the viewport for textured preview

### Importing a Texture

1. Select a mesh object
2. Go to `C3 Add-On > Import Texture`
3. Select a texture file (DDS, TGA, PNG, or JPG)
4. The texture will be applied to the selected mesh

### Importing/Replacing Animation

1. Select a mesh object that was previously imported from a C3 file
2. Go to `C3 Add-On > Import Animation`
3. Options:
   - **Use Original File** - Uses the stored file path from the original import (enabled by default)
   - If disabled, browse to select a different C3 file
4. Click `Import Animation`

The add-on will:
- Clear existing shape keys (except Basis)
- Bake new animation frames to shape keys
- Update the timeline length to match the animation

## Technical Details

### Supported Formats

**PHY Variants:**
- `PHY ` - Standard PHY format with 4 morph targets
- `PHY3` - Simplified format with 1 morph target and additional normal data
- `PHY4` - Similar to PHY3 with 1 morph target

**Keyframe Types:**
- `KKEY` - Full 4x4 matrix keyframes
- `ZKEY` - Compressed quaternion + translation keyframes
- `XKEY` - Compressed 3x4 matrix keyframes (no rotation quaternion)
- Legacy - Full frame-by-frame matrices

### File Structure

The add-on expects C3 files with the version header: `MAXFILE C3 00001`

Each C3 file can contain:
- Multiple PHY chunks (mesh geometry)
- MOTI chunks (motion/animation data)
- Texture references
- Keyframe animation data

### Custom Properties

The add-on stores metadata as custom properties on Blender objects:

- `c3_source_file` - Original file path (on collections and objects)
- `c3_phy_index` - PHY index within the source file (on objects)

These properties enable animation reimport without manual file selection.

## Known Limitations

- Bone-based skeletal animation is commented out in favor of shape key animation
- Maximum 16 PHY objects per file
- Maximum 16 motion tracks per file
- UV coordinates are inverted on the V axis (1-v)

## Credits

- **Author:** abdouthematrix
- **Development Assistance:** Claude (Anthropic)
- **Inspired by:** [C3-Operator](https://github.com/Tachyon-S/C3-Operator) by Tachyon-S

## Version

1.0.0 - Initial release

## Requirements

- Blender 3.0.0 or higher
- Python 3.x (bundled with Blender)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.