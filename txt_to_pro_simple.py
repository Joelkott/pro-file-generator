#!/usr/bin/env python3
"""
Simple approach: Decode an existing .pro file as a template, modify it, and re-encode
"""

import sys
import os
import uuid
import time

# Add proto_generated to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'proto_generated'))

import presentation_pb2


def parse_txt_file(txt_path):
    """Parse a txt file and return structured data"""
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    # Extract song title
    song_title = "Untitled"
    for line in lines:
        if line.startswith('# Song Title:'):
            song_title = line.replace('# Song Title:', '').strip()
            break

    # Parse sections and slides
    sections = []
    current_section = None
    current_slides = []
    current_lines = []

    for line in lines:
        # Skip title line
        if line.startswith('# Song Title:'):
            continue

        # Section header
        if line.startswith('[') and line.endswith(']'):
            # Save previous section
            if current_lines:
                current_slides.append(current_lines)
            if current_section and current_slides:
                sections.append({
                    'name': current_section,
                    'slides': current_slides
                })

            # Start new section
            current_section = line[1:-1]
            current_slides = []
            current_lines = []
            continue

        # Skip empty lines between slides
        if not line.strip():
            if current_lines:
                current_slides.append(current_lines)
                current_lines = []
            continue

        # Add line to current slide
        current_lines.append(line.strip())

        # If we have 2 lines, create a slide
        if len(current_lines) == 2:
            current_slides.append(current_lines)
            current_lines = []

    # Save last section
    if current_lines:
        current_slides.append(current_lines)
    if current_section and current_slides:
        sections.append({
            'name': current_section,
            'slides': current_slides
        })

    return {
        'title': song_title,
        'sections': sections
    }


def load_template(template_path):
    """Load a template .pro file"""
    with open(template_path, 'rb') as f:
        pres = presentation_pb2.Presentation()
        pres.ParseFromString(f.read())
    return pres


def update_rtf_text(rtf_data, line1, line2):
    """Update RTF data with new text - simple string replacement"""
    # This is a simplified approach - just replace the text content
    # A more robust solution would parse and rebuild the RTF properly
    new_text = f"{line1}\\par\\n{line2}"
    return rtf_data


def txt_to_pro(txt_path, template_path, output_path=None):
    """Convert a txt file to a .pro file using a template"""
    if not os.path.exists(txt_path):
        print(f"Error: File not found: {txt_path}")
        return False

    if not os.path.exists(template_path):
        print(f"Error: Template file not found: {template_path}")
        return False

    # Parse txt file
    print(f"Parsing {txt_path}...")
    data = parse_txt_file(txt_path)

    print(f"Song: {data['title']}")
    print(f"Sections: {len(data['sections'])}")
    for section in data['sections']:
        print(f"  - {section['name']}: {len(section['slides'])} slides")

    # Load template
    print(f"\nLoading template from {template_path}...")
    pres = load_template(template_path)

    # Update presentation name
    pres.name = data['title']

    # Update timestamp
    current_time = int(time.time())
    pres.last_date_used.seconds = current_time
    pres.last_modified_date.seconds = current_time

    # Generate new UUID for presentation
    pres.uuid.string = str(uuid.uuid4())

    print(f"\nTemplate has {len(pres.cue_groups)} cue groups and {len(pres.cues)} cues")

    # TODO: Actually modify the slides with the new text
    # For now, this just copies the template with updated metadata
    print("\nWARNING: Slide content modification not yet implemented!")
    print("This version only updates the presentation name and metadata.")

    # Determine output path
    if not output_path:
        output_path = txt_path.rsplit('.', 1)[0] + '.pro'

    # Write to file
    print(f"\nWriting to {output_path}...")
    with open(output_path, 'wb') as f:
        f.write(pres.SerializeToString())

    print(f"Success! Created {output_path}")
    print("\nNote: To properly create slides with your text, we need to implement")
    print("RTF generation and protobuf structure creation. For now, use this as a starting point.")
    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 txt_to_pro_simple.py <input.txt> <template.pro> [output.pro]")
        print("\nExample:")
        print('python3 txt_to_pro_simple.py sample_song.txt "/mnt/c/Users/joelv/Downloads/No One Like The Lord.proBundle/No One Like The Lord.pro" output.pro')
        sys.exit(1)

    txt_path = sys.argv[1]
    template_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None

    success = txt_to_pro(txt_path, template_path, output_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
