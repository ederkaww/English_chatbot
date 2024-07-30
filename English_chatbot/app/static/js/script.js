function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function sendMessage() {
    const userInput = document.getElementById('user-input').value;
    if (userInput.trim() === "") return;

    appendMessage(userInput, 'user');
    document.getElementById('user-input').value = '';

    fetch('http://localhost:5000/webhook', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userInput }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.response) {
            appendMessage(data.response, 'bot', true);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function appendMessage(message, sender, isHtml = false) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);

    const messageContent = document.createElement('div');
    messageContent.classList.add('message-content');
    if (isHtml) {
        messageContent.innerHTML = message;  // Interpret HTML
    } else {
        messageContent.textContent = message;  // Render as text
    }

    messageElement.appendChild(messageContent);

    const chatBox = document.getElementById('chat-box');
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}
