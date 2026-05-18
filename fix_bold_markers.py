#!/usr/bin/env python3
"""
Fix two issues in Markdown files under content/website/:
1. Remove **bold markers** from description: fields in frontmatter YAML
2. Remove **bold markers** from the blockquote intro line (> **text** → > text)
"""

import os
import re
import glob

CONTENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content/website")

# Stats
files_checked = 0
files_modified_desc = 0
files_modified_intro = 0
files_modified_both = 0
errors = []


def fix_description_text(text):
    """Remove first ** pair from description: string value."""
    line = text
    m = re.match(r'(description:\s*")(.*)(")', line)
    if m:
        prefix = m.group(1)
        val = m.group(2)
        suffix = m.group(3)
        if val.startswith('**'):
            close_idx = val.find('**', 2)
            if close_idx > 0:
                val = val[2:close_idx] + val[close_idx+2:]
                return prefix + val + suffix
    return line


def fix_intro_text(text):
    """Remove ** markers from > **text** lines."""
    line = text
    m = re.match(r'^(>\s*)\*\*(.+?)\*\*(.*)$', line)
    if m:
        return m.group(1) + m.group(2) + m.group(3)
    return line


def process_file(filepath):
    """Process a single markdown file."""
    global files_modified_desc, files_modified_intro, files_modified_both

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        errors.append(f"Read error: {filepath} - {e}")
        return

    original = content
    lines = content.split('\n')
    new_lines = []
    modified_desc = False
    modified_intro = False

    in_frontmatter = False
    in_content = False

    for i, line in enumerate(lines):
        processed_line = line

        # Track frontmatter
        if i == 0 and line.strip() == '---':
            in_frontmatter = True
        elif in_frontmatter and line.strip() == '---':
            in_frontmatter = False
            in_content = True
        elif in_frontmatter:
            # Fix description in frontmatter
            stripped = line.strip()
            if stripped.startswith('description:'):
                new_line = fix_description_text(line)
                if new_line != line:
                    modified_desc = True
                    processed_line = new_line
        
        # Fix blockquote intro lines in content area
        # Only fix the FIRST line that matches > **...** in content
        if in_content and not modified_intro:
            stripped = line.strip()
            if stripped.startswith('> **'):
                new_line = fix_intro_text(line)
                if new_line != line:
                    modified_intro = True
                    processed_line = new_line

        new_lines.append(processed_line)

    modified = '\n'.join(new_lines)

    if modified != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(modified)
        if modified_desc:
            files_modified_desc += 1
        if modified_intro:
            files_modified_intro += 1
        if modified_desc and modified_intro:
            files_modified_both += 1


def main():
    global files_checked

    md_files = glob.glob(os.path.join(CONTENT_DIR, '**', '*.md'), recursive=True)
    md_files = [f for f in md_files if os.path.isfile(f)]

    print(f"Found {len(md_files)} markdown files in {CONTENT_DIR}")

    for idx, filepath in enumerate(md_files):
        files_checked += 1
        process_file(filepath)

        if (idx + 1) % 200 == 0:
            print(f"  Progress: {idx+1}/{len(md_files)} files processed...")

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total files checked:       {files_checked}")
    print(f"Description fixed:         {files_modified_desc}")
    print(f"Opening intro fixed:       {files_modified_intro}")
    print(f"Both fixed:                {files_modified_both}")
    total_unique = files_modified_desc + files_modified_intro - files_modified_both
    print(f"Total unique files mod:    {total_unique}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors[:10]:
            print(f"  {e}")
        if len(errors) > 10:
            print(f"  ... and {len(errors)-10} more")

    print(f"\n{'='*60}")


if __name__ == '__main__':
    main()
