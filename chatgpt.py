# Import required libraries
from flask import Flask, render_template_string, request, jsonify
from openai import OpenAI
import re

# ============================
#  OPENAI CLIENT CONFIGURATION
# ============================
client = OpenAI(api_key="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")

# ================
#  FLASK APP SETUP
# ================
app = Flask(__name__)

# ======================
#  FRONTEND HTML PAGE UI
# ======================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Mini ChatGPT</title>

    <style>
        html, body {
            margin: 0; padding: 0;
            height: 100%; width: 100%;
            background: #f7f8fa;
            font-family: 'Segoe UI', sans-serif;
            overflow: hidden;
        }

        #chatbox {
            width: 100vw;
            height: 100vh;
            background: white;
            display: flex;
            flex-direction: column;
        }

        #header {
            background: #0078ff;
            color: white;
            padding: 15px;
            font-size: 24px;
            text-align: center;
        }

        #messages {
            flex: 1;
            overflow-y: scroll;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }

        .msg { 
            max-width: 75%;
            padding: 10px 14px;
            margin: 8px 0;
            border-radius: 15px;
        }

        .user {
            background: #0078ff;
            color: white;
            align-self: flex-end;
        }

        .bot {
            background: #e9ecef;
            color: #333;
            align-self: flex-start;
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
        }

        button {
            background: #0078ff;
            color: white;
            padding: 0 20px;
            border: none;
            cursor: pointer;
        }
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

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message})
                });

                const data = await response.json();

                messagesDiv.innerHTML += `<div class='msg bot'><b>Bot:</b> ${data.reply}</div>`;
                messagesDiv.scrollTop = messagesDiv.scrollHeight;

            } catch (error) {
                messagesDiv.innerHTML += `<div class='msg bot'><b>Bot:</b> Error: ${error}</div>`;
            }
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

# =================================================
#  CLEAN BOT REPLY – Converts Markdown → HTML tags
# =================================================
def clean_bot_reply(text):
    # Convert headings
    text = re.sub(r'###\s*(.*)', r'<h3>\1</h3>', text)
    text = re.sub(r'##\s*(.*)', r'<h3>\1</h3>', text)
    text = re.sub(r'#\s*(.*)', r'<h3>\1</h3>', text)

    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

    # Lists
    lines = text.split('\n')
    new_lines = []
    in_ol = in_ul = False

    for line in lines:
        stripped = line.strip()

        if re.match(r'^\d+\.', stripped):
            if not in_ol:
                new_lines.append('<ol>')
                in_ol = True
            item = re.sub(r'^\d+\. ', '', stripped)
            new_lines.append(f'<li>{item}</li>')

        elif stripped.startswith('- '):
            if not in_ul:
                new_lines.append('<ul>')
                in_ul = True
            new_lines.append(f"<li>{stripped[2:]}</li>")

        else:
            if in_ol:
                new_lines.append('</ol>'); in_ol = False
            if in_ul:
                new_lines.append('</ul>'); in_ul = False
            new_lines.append(stripped)

    if in_ol: new_lines.append('</ol>')
    if in_ul: new_lines.append('</ul>')

    return ''.join(new_lines)


# =========================
#  REMOVE \1, \2, \3 ...
# =========================
def remove_slash_numbers(text):
    return re.sub(r'\\+\d+', '', text)


# =====================
#  MAIN ROUTES (BACKEND)
# =====================
@app.route('/')
def index():
    return render_template_string(HTML_PAGE)


@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": "You are Mini ChatGPT. Format answers neatly with headings and lists."},
                {"role": "user", "content": user_input}
            ]
        )

        reply = response.output_text

        # Fix \1, \2, etc.
        reply = remove_slash_numbers(reply)

        formatted_reply = clean_bot_reply(reply)

        return jsonify({'reply': formatted_reply})

    except Exception as e:
        return jsonify({'reply': "Server Error: " + str(e)})


# ================
#  START FLASK APP
# ================
if __name__ == '__main__':
    app.run(debug=True)