import asyncio
import json
import random
import re
import time
from pathlib import Path

import gradio as gr

from backend import tree
from backend.app import post_model_call

STRATEGIES = {n["id"]: n["action"] for n in tree.debate_tree.values() if "action" in n}
DEMOS = json.load(open(Path(__file__).parent / "debate_results.json"))

CSS = """
#header {text-align: center; padding: 1.5rem; border-radius: 16px;
         background: linear-gradient(135deg, #4c1d95, #db2777); color: white;}
#header h1 {font-size: 2.4rem; margin: 0; color: white;}
#header p {opacity: .85; margin: .4rem 0 0; color: white;}
"""


def parse_history(history):
    return [
        {"role": "user" if tag == "Opponent" else "assistant", "content": text.strip()}
        for tag, text in re.findall(r"<(Opponent|You)>(.*?)</\1>", history, re.S)
    ]


def to_history(messages):
    tags = {"user": "Opponent", "assistant": "You"}
    return "".join(
        f"<{tags[m['role']]}>{m['content']}</{tags[m['role']]}>"
        for m in messages
        if not (m.get("metadata") or {}).get("title")
    )


def reply_messages(result):
    return [
        {
            "role": "assistant",
            "content": STRATEGIES.get(result["action_id"], "No strategy found"),
            "metadata": {"title": f"🧠 Schopenhauer strategy #{result['action_id']}"},
        },
        {"role": "assistant", "content": result["response"]},
    ]


def live_reply(message, messages):
    if not tree.MISTRAL_API_TOKEN:
        raise gr.Error("Set MISTRAL_API_TOKEN in backend/.env, or try the Demo tab.")
    messages = messages + [{"role": "user", "content": message}]
    yield "", messages
    result = asyncio.run(post_model_call(to_history(messages)))
    yield "", messages + reply_messages(result)


def demo_label(i):
    first = parse_history(list(DEMOS[i]["history"].values())[0])[0]["content"]
    return f"#{i + 1} · {first[:80]}…"


def play_demo(label):
    result = DEMOS[int(label.split(" ")[0][1:]) - 1]
    messages = []
    for m in parse_history(list(result["history"].values())[0]):
        messages.append(m)
        yield messages
        time.sleep(0.4)
    for m in reply_messages(result):
        messages.append(m)
        yield messages
        time.sleep(0.6)


theme = gr.themes.Soft(primary_hue="violet", secondary_hue="pink", font=gr.themes.GoogleFont("Inter"))

with gr.Blocks(theme=theme, css=CSS, title="SchopGPT") as demo:
    gr.HTML(
        "<div id='header'><h1>🎩 SchopGPT</h1>"
        "<p>Win any Twitter debate with Schopenhauer's <i>Art of Being Right</i></p></div>"
    )
    with gr.Tab("🎬 Demo (no API key)"):
        labels = [demo_label(i) for i in range(len(DEMOS))]
        with gr.Row():
            picker = gr.Dropdown(labels, value=labels[0], label="Pick a debate", scale=4)
            dice = gr.Button("🎲 Random", scale=1)
        demo_chat = gr.Chatbot(type="messages", height=520, label="Debate")
        picker.change(play_demo, picker, demo_chat)
        dice.click(lambda: random.choice(labels), None, picker)
        demo.load(play_demo, picker, demo_chat)
    with gr.Tab("⚔️ Live (Mistral)"):
        live_chat = gr.Chatbot(
            type="messages",
            height=520,
            label="Debate",
            placeholder="Paste a tweet attacking the Silicon Valley Bank and let SchopGPT answer.",
        )
        box = gr.Textbox(placeholder="Opponent's tweet…", show_label=False, submit_btn=True)
        box.submit(live_reply, [box, live_chat], [box, live_chat])
        gr.ClearButton([box, live_chat])

if __name__ == "__main__":
    demo.launch()
