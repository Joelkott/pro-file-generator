#!/usr/bin/env python3
"""
Convert simple txt files to ProPresenter .pro files
Format: 2 lines per slide, organized into sections

Example txt format:
# Song Title: Amazing Grace

[Verse 1]
Amazing grace how sweet the sound
That saved a wretch like me

[Chorus]
Amazing grace how sweet the sound
That saved a wretch like me
"""

import sys
import os
import uuid
import time
import re

# Add proto_generated to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'proto_generated'))

import presentation_pb2
import action_pb2
import slide_pb2
import cue_pb2
import groups_pb2
import uuid_pb2
import rvtimestamp_pb2
import applicationInfo_pb2
import version_pb2
import color_pb2
import background_pb2
import graphicsData_pb2
import rv2d_pb2
import font_pb2


def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())


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
            if current_section and current_lines:
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


def create_text_element(line1, line2):
    """Create a text element with 2 lines"""
    text = f"{line1}\\par\\n{line2}"

    # Create RTF data (simplified)
    rtf_data = (
        "{\\rtf0\\ansi\\ansicpg1252"
        "{\\fonttbl\\f0\\fnil Arial;}"
        "{\\colortbl;\\red255\\green255\\blue255;}"
        "{\\*\\expandedcolortbl;\\csgenericrgb\\c100000\\c100000\\c100000\\c100000;}"
        "{\\*\\listtable}{\\*\\listoverridetable}"
        "\\uc1\\paperw38400\\margl0\\margr0\\margt0\\margb0"
        "\\pard\\li0\\fi0\\ri0\\qc\\sb0\\sa0\\sl240\\slmult1\\slleading0"
        "\\f0\\b0\\i0\\ul0\\strike0\\fs120\\expnd0\\expndtw0"
        "\\CocoaLigature1\\cf1\\strokewidth0\\strokec1\\nosupersub\\ulc0"
        f"{line1}\\par\\n{line2}"
        "}"
    )

    # Create Graphics.Element
    element = graphicsData_pb2.Graphics.Element()
    element.uuid.string = generate_uuid()
    element.name = "Line one..."
    element.bounds.origin.x = 0
    element.bounds.origin.y = 0
    element.bounds.size.width = 1920
    element.bounds.size.height = 540
    element.opacity = 1.0

    # Set up path (rectangle)
    element.path.closed = True
    for i in range(4):
        point = element.path.points.add()
        if i == 0:  # top-left
            point.point.x = 0
            point.point.y = 0
        elif i == 1:  # top-right
            point.point.x = 1
            point.point.y = 0
        elif i == 2:  # bottom-right
            point.point.x = 1
            point.point.y = 1
        elif i == 3:  # bottom-left
            point.point.x = 0
            point.point.y = 1
        point.q0.CopyFrom(point.point)
        point.q1.CopyFrom(point.point)

    element.path.shape.type = graphicsData_pb2.Graphics.Path.Shape.TYPE_RECTANGLE

    # Fill color (blue)
    element.fill.color.red = 0.117647059
    element.fill.color.green = 0.564705908
    element.fill.color.blue = 1.0
    element.fill.color.alpha = 1.0

    # Stroke (white)
    element.stroke.width = 3
    element.stroke.color.red = 1.0
    element.stroke.color.green = 1.0
    element.stroke.color.blue = 1.0
    element.stroke.color.alpha = 1.0

    # Shadow
    element.shadow.angle = 315
    element.shadow.offset = 5
    element.shadow.radius = 5
    element.shadow.color.alpha = 1.0
    element.shadow.opacity = 0.75

    # Feather
    element.feather.radius = 0.05

    # Text attributes
    element.text.attributes.font.name = "Arial"
    element.text.attributes.font.size = 60
    element.text.attributes.font.family = "Arial"
    element.text.attributes.font.face = "Regular"

    # Text color (white)
    element.text.attributes.text_solid_fill.red = 1.0
    element.text.attributes.text_solid_fill.green = 1.0
    element.text.attributes.text_solid_fill.blue = 1.0
    element.text.attributes.text_solid_fill.alpha = 1.0

    # Paragraph style
    element.text.attributes.paragraph_style.alignment = graphicsData_pb2.TextAttributes.ParagraphStyle.ALIGNMENT_CENTER
    element.text.attributes.paragraph_style.line_height_multiple = 1.0

    # Stroke color
    element.text.attributes.stroke_color.red = 1.0
    element.text.attributes.stroke_color.green = 1.0
    element.text.attributes.stroke_color.blue = 1.0
    element.text.attributes.stroke_color.alpha = 1.0

    # Set RTF data
    element.text.rtf_data = rtf_data
    element.text.vertical_alignment = graphicsData_pb2.Text.VERTICAL_ALIGNMENT_MIDDLE
    element.text.is_superscript_standardized = True
    element.text.transformDelimiter = "  •  "
    element.text.chord_pro.color.alpha = 1.0

    return element


def create_slide(line1, line2):
    """Create a slide with 2 lines of text"""
    slide = slide_pb2.Slide()
    slide.size.width = 1920
    slide.size.height = 1080
    slide.uuid.string = generate_uuid()
    slide.background_color.alpha = 1.0

    # Add text element
    element = create_text_element(line1, line2)
    slide.elements.add().element.CopyFrom(element)
    slide.elements[0].info = 3

    return slide


def create_cue(lines, section_name):
    """Create a cue (slide) from lines"""
    cue = cue_pb2.Cue()
    cue.uuid.string = generate_uuid()
    cue.completion_target_uuid.string = "00000000-0000-0000-0000-000000000000"
    cue.completion_action_type = cue_pb2.Cue.COMPLETION_ACTION_TYPE_LAST
    cue.completion_action_uuid.string = "00000000-0000-0000-0000-000000000000"
    cue.isEnabled = True

    # Create slide action
    action = cue.actions.add()
    action.uuid.string = generate_uuid()
    action.isEnabled = True
    action.type = action_pb2.Action.ACTION_TYPE_PRESENTATION_SLIDE

    # Create slide
    line1 = lines[0] if len(lines) > 0 else ""
    line2 = lines[1] if len(lines) > 1 else ""
    slide = create_slide(line1, line2)

    action.slide.presentation.base_slide.CopyFrom(slide)

    # Add empty notes
    action.slide.presentation.notes.rtf_data = "{\\rtf0\\ansi\\ansicpg1252{\\fonttbl\\f0\\fnil ArialMT;}{\\colortbl;\\red0\\green0\\blue0;\\red255\\green255\\blue255;\\red255\\green255\\blue255;}{\\*\\expandedcolortbl;\\csgenericrgb\\c0\\c0\\c0\\c100000;\\csgenericrgb\\c100000\\c100000\\c100000\\c100000;\\csgenericrgb\\c100000\\c100000\\c100000\\c0;}{\\*\\listtable}{\\*\\listoverridetable}\\uc1\\paperw12240\\margl0\\margr0\\margt0\\margb0\\pard\\li0\\fi0\\ri0\\ql\\sb0\\sa0\\sl240\\slmult1\\slleading0\\f0\\b0\\i0\\ul0\\strike0\\fs100\\expnd0\\expndtw0\\CocoaLigature1\\cf1\\strokewidth0\\strokec2\\nosupersub\\ulc0\\highlight3\\cb3}"

    action.slide.presentation.notes.attributes.font.name = "ArialMT"
    action.slide.presentation.notes.attributes.font.size = 50
    action.slide.presentation.notes.attributes.font.family = "Arial"
    action.slide.presentation.notes.attributes.font.face = "Regular"
    action.slide.presentation.notes.attributes.text_solid_fill.alpha = 1.0
    action.slide.presentation.notes.attributes.paragraph_style.line_height_multiple = 1.0
    action.slide.presentation.notes.attributes.stroke_color.red = 1.0
    action.slide.presentation.notes.attributes.stroke_color.green = 1.0
    action.slide.presentation.notes.attributes.stroke_color.blue = 1.0
    action.slide.presentation.notes.attributes.stroke_color.alpha = 1.0

    return cue


def get_section_color(section_name):
    """Get color for section based on name"""
    section_lower = section_name.lower()

    # Default colors for common sections
    if 'verse' in section_lower:
        return {'red': 0.0, 'green': 0.466666669, 'blue': 0.8, 'alpha': 1.0}
    elif 'chorus' in section_lower:
        return {'red': 0.8, 'green': 0.0, 'blue': 0.305882365, 'alpha': 1.0}
    elif 'bridge' in section_lower:
        return {'red': 0.4627451, 'green': 0.0, 'blue': 0.8, 'alpha': 1.0}
    elif 'intro' in section_lower:
        return {'red': 0.0, 'green': 0.8, 'blue': 0.4, 'alpha': 1.0}
    elif 'outro' in section_lower or 'ending' in section_lower:
        return {'red': 0.8, 'green': 0.4, 'blue': 0.0, 'alpha': 1.0}
    else:
        # Default gray
        return {'red': 0.5, 'green': 0.5, 'blue': 0.5, 'alpha': 1.0}


def create_presentation(data):
    """Create a ProPresenter presentation from parsed data"""
    pres = presentation_pb2.Presentation()

    # Set application info
    pres.application_info.platform = applicationInfo_pb2.ApplicationInfo.PLATFORM_MACOS
    pres.application_info.platform_version.major_version = 14
    pres.application_info.platform_version.minor_version = 0
    pres.application_info.platform_version.patch_version = 0
    pres.application_info.application = applicationInfo_pb2.ApplicationInfo.APPLICATION_PROPRESENTER
    pres.application_info.application_version.major_version = 7
    pres.application_info.application_version.minor_version = 16
    pres.application_info.application_version.build = "118766559"

    # Set basic properties
    pres.uuid.string = generate_uuid()
    pres.name = data['title']

    current_time = int(time.time())
    pres.last_date_used.seconds = current_time
    pres.last_modified_date.seconds = current_time

    # Background
    pres.background.color.alpha = 1.0

    # Create arrangement (default)
    arrangement_uuid = generate_uuid()
    pres.selected_arrangement.string = arrangement_uuid

    # Create cue groups and cues for each section
    for section in data['sections']:
        section_name = section['name']
        slides = section['slides']

        if not slides:
            continue

        # Create cue group
        cue_group = pres.cue_groups.add()
        group_uuid = generate_uuid()

        cue_group.group.uuid.string = group_uuid
        cue_group.group.name = section_name

        # Set color based on section name
        color = get_section_color(section_name)
        cue_group.group.color.red = color['red']
        cue_group.group.color.green = color['green']
        cue_group.group.color.blue = color['blue']
        cue_group.group.color.alpha = color['alpha']

        # Set application group identifiers
        app_group_uuid = generate_uuid()
        cue_group.group.application_group_identifier.string = app_group_uuid
        cue_group.group.application_group_name = section_name

        # Create cues for each slide
        for slide_lines in slides:
            cue = create_cue(slide_lines, section_name)
            pres.cues.add().CopyFrom(cue)

            # Add cue identifier to group
            cue_group.cue_identifiers.add().string = cue.uuid.string

    return pres


def txt_to_pro(txt_path, output_path=None):
    """Convert a txt file to a .pro file"""
    if not os.path.exists(txt_path):
        print(f"Error: File not found: {txt_path}")
        return False

    # Parse txt file
    print(f"Parsing {txt_path}...")
    data = parse_txt_file(txt_path)

    print(f"Creating presentation: {data['title']}")
    print(f"Sections: {len(data['sections'])}")

    # Create presentation
    pres = create_presentation(data)

    # Determine output path
    if not output_path:
        output_path = txt_path.rsplit('.', 1)[0] + '.pro'

    # Write to file
    print(f"Writing to {output_path}...")
    with open(output_path, 'wb') as f:
        f.write(pres.SerializeToString())

    print(f"Success! Created {output_path}")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 txt_to_pro.py <input.txt> [output.pro]")
        print("\nExample txt format:")
        print("# Song Title: Amazing Grace")
        print("\n[Verse 1]")
        print("Amazing grace how sweet the sound")
        print("That saved a wretch like me")
        print("\n[Chorus]")
        print("...")
        sys.exit(1)

    txt_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    success = txt_to_pro(txt_path, output_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
