from flask import Flask, render_template_string, request, jsonify
from openai import OpenAI
import re

# ===== CONFIGURATION =====
client = OpenAI(api_key="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")  # 🔒 Replace with your real API key

# ===== FLASK APP =====
app = Flask(__name__)

# ===== HTML TEMPLATE =====
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Mini ChatGPT</title>
    <style>
        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
            width: 100%;
            font-family: 'Segoe UI', sans-serif;
            background: #f7f8fa;
            overflow: hidden;
        }

        #chatbox {
            width: 100vw;
            height: 100vh;
            background: white;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        #header {
            background-color: #0078ff;
            color: white;
            text-align: center;
            padding: 15px;
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 1px;
        }

        #messages {
            flex: 1;
            overflow-y: scroll;
            padding: 20px;
            display: flex;
            flex-direction: column;
            scrollbar-width: none;
        }
        #messages::-webkit-scrollbar { display: none; }

        .msg {
            max-width: 75%;
            margin: 8px 0;
            padding: 10px 14px;
            border-radius: 15px;
            line-height: 1.6;
            word-wrap: break-word;
            display: inline-block;
        }
        .user {
            background: #0078ff;
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 0;
            text-align: right;
        }
        .bot {
            background: #e9ecef;
            color: #333;
            align-self: flex-start;
            border-bottom-left-radius: 0;
        }

        #input-area {
            display: flex;
            border-top: 1px solid #ddd;
        }
        #user-input {
            flex: 1;
            border: none;
            padding: 14px;
            font-size: 16px;
            outline: none;
            resize: none;
        }
        button {
            background: #0078ff;
            color: white;
            border: none;
            padding: 0 20px;
            cursor: pointer;
            font-size: 16px;
            transition: 0.2s;
        }
        button:hover { background: #005fd4; }

        h3 {
            margin-top: 10px;
            margin-bottom: 6px;
            color: #0078ff;
        }
        ul, ol {
            margin: 5px 0 5px 25px;
            padding-left: 10px;
        }
        li { margin-bottom: 3px; }
        strong { font-weight: 600; }
    </style>
</head>
<body>
    <div id="chatbox">
        <div id="header">Mini ChatGPT</div>
        <div id="messages"></div>
        <div id="input-area">
            <textarea id="user-input" rows="1" placeholder="Ask anything..."></textarea>
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        const input = document.getElementById('user-input');
        const messagesDiv = document.getElementById('messages');

        async function sendMessage() {
            const message = input.value.trim();
            if (!message) return;

            messagesDiv.innerHTML += `<div class='msg user'><b>You:</b> ${message}</div>`;
            input.value = '';
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            const response = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message})
            });
            const data = await response.json();
            messagesDiv.innerHTML += `<div class='msg bot'><b>Bot:</b> ${data.reply}</div>`;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        input.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        });
    </script>
</body>
</html>
"""

# ===== FIXED CLEANER FUNCTION =====
def clean_bot_reply(text):
    """Convert GPT output into clean HTML."""
    # Properly use raw strings to reference regex groups
    text = re.sub(r'###\s*(.*)', r'<h3>\1</h3>', text)
    text = re.sub(r'##\s*(.*)', r'<h3>\1</h3>', text)
    text = re.sub(r'#\s*(.*)', r'<h3>\1</h3>', text)

    # Bold text
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

    # Process lists
    lines = text.split('\n')
    new_lines = []
    in_ol = in_ul = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if re.match(r'^\d+\.', stripped):
            if not in_ol:
                new_lines.append('<ol>')
                in_ol = True
            item = re.sub(r'^\d+\.\s*', '', stripped)
            new_lines.append(f'<li>{item}</li>')
        elif stripped.startswith('- '):
            if not in_ul:
                new_lines.append('<ul>')
                in_ul = True
            item = stripped[2:]
            new_lines.append(f'<li>{item}</li>')
        else:
            if in_ol:
                new_lines.append('</ol>')
                in_ol = False
            if in_ul:
                new_lines.append('</ul>')
                in_ul = False
            new_lines.append(stripped)

    if in_ol:
        new_lines.append('</ol>')
    if in_ul:
        new_lines.append('</ul>')

    return ''.join(new_lines)

# ===== ROUTES =====
@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are Mini ChatGPT. Format answers neatly with headings and lists."},
            {"role": "user", "content": user_input}
        ]
    )

    reply = completion.choices[0].message.content
    formatted_reply = clean_bot_reply(reply)
    return jsonify({'reply': formatted_reply})

# ===== RUN APP =====
if __name__ == '__main__':
    app.run(debug=True)
