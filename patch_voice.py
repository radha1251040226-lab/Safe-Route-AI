"""Patch script: fixes dashcam streaming voice block to use parent window speechSynthesis."""

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Identify the unique marker for the old block
OLD_MARKER = 'speakLadyVoice(synth, "{safe_v_msg}", "{config.locale_code}");'
NEW_VOICE_BLOCK = '''let _synth = null;
                                    let _UCtor = null;
                                    try {{
                                        if (window.parent && window.parent.speechSynthesis) {{
                                            _synth = window.parent.speechSynthesis;
                                            _UCtor = window.parent.SpeechSynthesisUtterance;
                                        }}
                                    }} catch(e) {{}}
                                    if (!_synth) {{
                                        _synth = window.speechSynthesis;
                                        _UCtor = window.SpeechSynthesisUtterance;
                                    }}
                                    if (_synth && _UCtor) {{
                                        speakLadyVoice(_synth, _UCtor, "{safe_v_msg}", "{config.locale_code}");
                                    }}'''

# Replace the old 3-line voice block with the new 4-argument one
OLD_SECTION = '''                                    const synth = window.speechSynthesis || (window.parent && window.parent.speechSynthesis);
                                    if (synth) {{
                                        speakLadyVoice(synth, "{safe_v_msg}", "{config.locale_code}");
                                    }}'''

if OLD_SECTION in content:
    content = content.replace(OLD_SECTION, NEW_VOICE_BLOCK, 1)
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Dashcam voice block patched (LF version).")
else:
    # Try CRLF line endings
    OLD_SECTION_CRLF = OLD_SECTION.replace("\n", "\r\n")
    if OLD_SECTION_CRLF in content:
        content = content.replace(OLD_SECTION_CRLF, NEW_VOICE_BLOCK.replace("\n", "\r\n"), 1)
        with open("app.py", "w", encoding="utf-8") as f:
            f.write(content)
        print("SUCCESS: Dashcam voice block patched (CRLF version).")
    else:
        # Show raw bytes near the old marker for debugging
        idx = content.find(OLD_MARKER)
        if idx >= 0:
            print("Marker found at:", idx)
            print("Context (300 chars before marker):")
            print(repr(content[idx-300:idx+len(OLD_MARKER)+50]))
        else:
            print("ERROR: Old marker not found in file at all.")
            print("Searching for 'speakLadyVoice' occurrences:")
            start = 0
            while True:
                pos = content.find("speakLadyVoice", start)
                if pos == -1:
                    break
                print(f"  pos {pos}: {repr(content[pos:pos+100])}")
                start = pos + 1
