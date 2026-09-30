import html
import re

import gradio as gr

from spell_engine import get_suggestions, is_correct

# Words, allowing apostrophes inside (don't, it's)
TOKEN_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)*")

STYLE = """
<style>
.result { white-space: pre-wrap; line-height: 2; font-size: 18px;
          min-height: 200px; padding: 12px; }
.misspelled { position: relative; display: inline-block; cursor: help;
              text-decoration: underline wavy #e11d48;
              text-underline-offset: 4px; }
.misspelled .tip { visibility: hidden; opacity: 0; position: absolute;
    left: 0; top: 100%; margin-top: 4px; z-index: 1000;
    background: #1f2937; color: #fff; padding: 8px 12px; border-radius: 8px;
    font-size: 14px; line-height: 1.5; white-space: nowrap;
    box-shadow: 0 4px 12px rgba(0,0,0,.3); transition: opacity .15s; }
.misspelled:hover .tip { visibility: visible; opacity: 1; }
.tip .head { color: #9ca3af; font-size: 12px; }
.tip .sug { display: block; }
</style>
"""


def match_case(original, suggestion):
    if len(original) > 1 and original.isupper():
        return suggestion.upper()
    if original[0].isupper():
        return suggestion.capitalize()
    return suggestion


def check_spelling(text):
    if not text.strip():
        return STYLE + "<div class='result'><i>Type a sentence and press Check spelling.</i></div>", ""

    parts, found, last = [], [], 0
    for m in TOKEN_RE.finditer(text):
        parts.append(html.escape(text[last:m.start()]))  # spaces/punctuation
        word = m.group()
        last = m.end()

        if is_correct(word):
            parts.append(html.escape(word))
            continue

        suggestions = [match_case(word, s) for s, _ in get_suggestions(word, k=5)]
        found.append((word, suggestions))

        if suggestions:
            items = "".join(f"<span class='sug'>• {html.escape(s)}</span>" for s in suggestions)
            tip = f"<span class='head'>Did you mean:</span>{items}"
        else:
            tip = "<span class='head'>No suggestions found</span>"
        parts.append(f"<span class='misspelled'>{html.escape(word)}<span class='tip'>{tip}</span></span>")

    parts.append(html.escape(text[last:]))
    result_html = STYLE + "<div class='result'>" + "".join(parts) + "</div>"

    if found:
        lines = [f"**{len(found)} possible misspelling(s):**", ""]
        for w, sugg in found:
            lines.append(f"- **{w}** → {', '.join(sugg) if sugg else '(no suggestions)'}")
        summary = "\n".join(lines)
    else:
        summary = "✅ No misspellings found."
    return result_html, summary


def autocorrect(text):
    def fix(m):
        word = m.group()
        if is_correct(word):
            return word
        best = get_suggestions(word, k=1)
        return match_case(word, best[0][0]) if best else word

    return TOKEN_RE.sub(fix, text)


with gr.Blocks(title="Spell Checker") as demo:
    gr.Markdown("# ✍️ Spell Checker\nType a sentence. Misspelled words get a red underline; hover to see suggestions.")

    inp = gr.Textbox(label="Your sentence", lines=4,
                     placeholder="e.g. I beleive machin lerning is amazng")
    with gr.Row():
        check_btn = gr.Button("Check spelling", variant="primary")
        fix_btn = gr.Button("Auto-correct all")

    out_html = gr.HTML(label="Result")
    summary = gr.Markdown()
    corrected = gr.Textbox(label="Auto-corrected text", lines=4, interactive=False)

    check_btn.click(check_spelling, inp, [out_html, summary])
    fix_btn.click(autocorrect, inp, corrected)

    gr.Examples(
        examples=["I beleive machin lerning is amazng",
                  "My freind will recieve the projct tomorow"],
        inputs=inp,
    )

if __name__ == "__main__":
    demo.launch(share=True)