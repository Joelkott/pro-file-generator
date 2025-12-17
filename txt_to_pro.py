#!/usr/bin/env python3
"""
Full implementation: Parse txt file and generate .pro with actual slide content
"""

import sys
import os
import uuid
import time
import re

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
    has_section_tags = False

    for line in lines:
        # Skip title line
        if line.startswith('# Song Title:'):
            continue

        # Section header
        if line.startswith('[') and line.endswith(']'):
            has_section_tags = True
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

    # If no sections were found (file has no tags), treat entire file as one section
    if not has_section_tags and current_slides:
        sections.append({
            'name': song_title if song_title != "Untitled" else 'Lyrics',
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


def escape_rtf_text(text):
    """Escape special characters for RTF"""
    # Basic escaping - may need more comprehensive handling
    text = text.replace('\\', '\\\\')
    text = text.replace('{', '\\{')
    text = text.replace('}', '\\}')
    return text


def update_slide_text(cue, line1, line2):
    """Update the text in a cue's slide"""
    # Navigate to the text element
    if not cue.actions:
        return False

    action = cue.actions[0]
    if not action.HasField('slide'):
        return False

    slide = action.slide.presentation.base_slide
    if not slide.elements:
        return False

    element = slide.elements[0].element
    if not element.HasField('text'):
        return False

    # Remove ALL_CAPS capitalization from template
    # Set capitalization to NONE (0) to display text as-is
    element.text.attributes.capitalization = 0  # CAPITALIZATION_NONE

    # Also update custom_attributes if they exist
    for custom_attr in element.text.attributes.custom_attributes:
        custom_attr.capitalization = 0  # CAPITALIZATION_NONE

    # Escape text for RTF
    line1_escaped = escape_rtf_text(line1)
    line2_escaped = escape_rtf_text(line2)

    # Update RTF data - try to preserve formatting
    old_rtf = element.text.rtf_data

    # Convert bytes to string if needed
    if isinstance(old_rtf, bytes):
        old_rtf = old_rtf.decode('utf-8', errors='ignore')

    # Strategy: Find the formatting preamble and the middle formatting separator
    # The RTF structure is: PREAMBLE + TEXT1 + MIDDLE_FORMATTING + TEXT2 + }
    # We want to keep PREAMBLE and MIDDLE_FORMATTING, but replace TEXT1 and TEXT2

    # Find the last occurrence of \cb followed by space before text starts
    # Then find the \par\pard section in the middle
    # Then find the closing brace

    # Match pattern: (preamble with \cb2 ) + (first text) + (\par...\cb2 ) + (second text) + (})
    match = re.search(r'^(.+\\cb\d+\s+)(.+?)(\\par\\pard.+?\\cb\d+\s+)(.+?)(\})$', old_rtf, re.DOTALL)

    if match:
        # Extract the formatting parts we want to keep
        preamble = match.group(1)
        middle_formatting = match.group(3)
        closing_brace = match.group(5)

        # Build new RTF with our text
        new_rtf = f"{preamble}{line1_escaped}{middle_formatting}{line2_escaped}{closing_brace}"
        element.text.rtf_data = new_rtf.encode('utf-8')
        return True

    # If first pattern didn't match, try fallback patterns
    else:
        # Fallback: try simpler pattern without middle formatting
        match2 = re.search(r'^(.+\\cb\d+\s+)(.+?)(\})$', old_rtf, re.DOTALL)

        if match2:
            preamble = match2.group(1)
            closing_brace = match2.group(3)

            # For single line or simple format
            if line2:
                # Try to find any \par in the old content to use as separator
                old_content = match2.group(2)
                par_match = re.search(r'(\\par[^}]+)', old_content)
                if par_match:
                    separator = par_match.group(1)
                    new_rtf = f"{preamble}{line1_escaped}{separator}{line2_escaped}{closing_brace}"
                else:
                    new_rtf = f"{preamble}{line1_escaped}\\par {line2_escaped}{closing_brace}"
            else:
                new_rtf = f"{preamble}{line1_escaped}{closing_brace}"

            element.text.rtf_data = new_rtf.encode('utf-8')
        else:
            # Last resort: build from scratch
            new_rtf = (
                "{\\rtf0\\ansi\\ansicpg1252"
                "{\\fonttbl\\f0\\fnil Arial;}"
                "{\\colortbl;\\red255\\green255\\blue255;}"
                "{\\*\\expandedcolortbl;\\csgenericrgb\\c100000\\c100000\\c100000\\c100000;}"
                "{\\*\\listtable}{\\*\\listoverridetable}"
                "\\uc1\\paperw38400\\margl0\\margr0\\margt0\\margb0"
                "\\pard\\li0\\fi0\\ri0\\qc\\sb0\\sa0\\sl240\\slmult1\\slleading0"
                "\\f0\\b0\\i0\\ul0\\strike0\\fs120\\expnd0\\expndtw0"
                "\\CocoaLigature1\\cf1\\strokewidth0\\strokec1\\nosupersub\\ulc0\\highlight2\\cb2 "
                f"{line1_escaped}\\par\\pard\\li0\\fi0\\ri0\\qc\\sb0\\sa0\\sl240\\slmult1\\slleading0"
                "\\f0\\b0\\i0\\ul0\\strike0\\fs120\\expnd0\\expndtw0"
                "\\CocoaLigature1\\cf1\\strokewidth0\\strokec1\\nosupersub\\ulc0\\highlight2\\cb2 "
                f"{line2_escaped}"
                "}"
            )
            element.text.rtf_data = new_rtf.encode('utf-8')
            return True

    # If nothing matched, return False
    return False


def update_cue_group_name(cue_group, new_name):
    """Update the name of a cue group"""
    cue_group.group.name = new_name
    cue_group.group.application_group_name = new_name


def get_section_color(section_name):
    """Get color for section based on name"""
    section_lower = section_name.lower()

    if 'verse' in section_lower:
        return {'red': 0.0, 'green': 0.466666669, 'blue': 0.8, 'alpha': 1.0}
    elif 'chorus' in section_lower:
        return {'red': 0.8, 'green': 0.0, 'blue': 0.305882365, 'alpha': 1.0}
    elif 'bridge' in section_lower:
        return {'red': 0.4627451, 'green': 0.0, 'blue': 0.8, 'alpha': 1.0}
    elif 'intro' in section_lower:
        return {'red': 0.0, 'green': 0.8, 'blue': 0.4, 'alpha': 1.0}
    elif 'ending' in section_lower or 'outro' in section_lower or 'tag' in section_lower:
        return {'red': 0.8, 'green': 0.4, 'blue': 0.0, 'alpha': 1.0}
    else:
        return {'red': 0.5, 'green': 0.5, 'blue': 0.5, 'alpha': 1.0}


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

    total_slides = sum(len(section['slides']) for section in data['sections'])
    print(f"Total slides needed: {total_slides}")

    for section in data['sections']:
        print(f"  - {section['name']}: {len(section['slides'])} slides")

    # Load template
    print(f"\nLoading template from {template_path}...")
    pres = load_template(template_path)

    print(f"Template has {len(pres.cue_groups)} cue groups and {len(pres.cues)} cues")

    # Update presentation metadata
    pres.name = data['title']
    current_time = int(time.time())
    pres.last_date_used.seconds = current_time
    pres.last_modified_date.seconds = current_time
    pres.uuid.string = str(uuid.uuid4())

    # Get template cue and cue_group as reference
    if not pres.cues or not pres.cue_groups:
        print("Error: Template must have at least one cue and cue group")
        return False

    template_cue = pres.cues[0]
    template_group = pres.cue_groups[0]

    # Clear existing cues and groups
    del pres.cues[:]
    del pres.cue_groups[:]

    print("\nCreating slides...")

    # Create new cues and groups based on parsed data
    for section_idx, section in enumerate(data['sections']):
        section_name = section['name']
        slides = section['slides']

        print(f"  Section: {section_name} ({len(slides)} slides)")

        # Create cue group
        cue_group = pres.cue_groups.add()
        cue_group.CopyFrom(template_group)

        # Update group properties
        cue_group.group.uuid.string = str(uuid.uuid4())
        cue_group.group.name = section_name
        cue_group.group.application_group_identifier.string = str(uuid.uuid4())
        cue_group.group.application_group_name = section_name

        # Set color
        color = get_section_color(section_name)
        cue_group.group.color.red = color['red']
        cue_group.group.color.green = color['green']
        cue_group.group.color.blue = color['blue']
        cue_group.group.color.alpha = color['alpha']

        # Clear cue identifiers
        del cue_group.cue_identifiers[:]

        # Create cues for each slide in this section
        for slide_idx, slide_lines in enumerate(slides):
            # Create new cue from template
            cue = pres.cues.add()
            cue.CopyFrom(template_cue)

            # Generate new UUID
            cue_uuid = str(uuid.uuid4())
            cue.uuid.string = cue_uuid

            # Update action UUID
            if cue.actions:
                cue.actions[0].uuid.string = str(uuid.uuid4())

            # Update slide UUID
            if cue.actions and cue.actions[0].HasField('slide'):
                cue.actions[0].slide.presentation.base_slide.uuid.string = str(uuid.uuid4())

            # Update text content
            line1 = slide_lines[0] if len(slide_lines) > 0 else ""
            line2 = slide_lines[1] if len(slide_lines) > 1 else ""

            success = update_slide_text(cue, line1, line2)
            if success:
                print(f"    Slide {slide_idx + 1}: '{line1}' / '{line2}'")
            else:
                print(f"    Warning: Could not update slide {slide_idx + 1}")

            # Add cue identifier to group
            cue_group.cue_identifiers.add().string = cue_uuid

    # Determine output path
    if not output_path:
        output_path = txt_path.rsplit('.', 1)[0] + '.pro'

    # Write to file
    print(f"\nWriting to {output_path}...")
    with open(output_path, 'wb') as f:
        f.write(pres.SerializeToString())

    print(f"Success! Created {output_path}")
    print(f"\nCreated {len(pres.cue_groups)} cue groups with {len(pres.cues)} total slides")
    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 txt_to_pro_full.py <input.txt> <template.pro> [output.pro]")
        print("\nExample:")
        print('python3 txt_to_pro_full.py sample_song.txt "/mnt/c/Users/joelv/Downloads/No One Like The Lord.proBundle/No One Like The Lord.pro" output.pro')
        sys.exit(1)

    txt_path = sys.argv[1]
    template_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None

    success = txt_to_pro(txt_path, template_path, output_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
