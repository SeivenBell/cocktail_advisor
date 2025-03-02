document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const favoriteIngredients = document.getElementById('favorite-ingredients');
    const favoriteCocktails = document.getElementById('favorite-cocktails');
    const exampleQuestions = document.querySelectorAll('.example-question');
    
    // User ID (in a real app, this would be from authentication)
    const userId = 'default_user';
    
    // Initialize the chat with a welcome message
    addBotMessage(`
        Hello! I'm your personal cocktail advisor. You can ask me about:
        <ul>
            <li>Information about specific cocktails</li>
            <li>Cocktails containing certain ingredients</li>
            <li>Personalized recommendations based on your preferences</li>
        </ul>
        What would you like to know about cocktails today?
    `);
    
    // Load user preferences
    loadUserPreferences();
    
    // Add event listener for form submission
    chatForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const message = userInput.value.trim();
        
        if (message) {
            // Add the user message to the chat
            addUserMessage(message);
            
            // Clear the input field
            userInput.value = '';
            
            // Send the message to the server
            sendMessage(message);
        }
    });
    
    // Add event listeners for example questions
    exampleQuestions.forEach(question => {
        question.addEventListener('click', function() {
            const message = this.textContent.trim();
            
            // Set the input field text
            userInput.value = message;
            
            // Focus the input field
            userInput.focus();
        });
    });
    
    // Function to send a message to the server
    function sendMessage(message) {
        // Show typing indicator
        showTypingIndicator();
        
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                user_id: userId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Remove typing indicator
            removeTypingIndicator();
            
            // Add the bot's response to the chat
            addBotMessage(data.response);
            
            // Update preferences if new ones were detected
            if (data.detected_preferences && 
                (data.detected_preferences.ingredients.length > 0 || 
                 data.detected_preferences.cocktails.length > 0)) {
                loadUserPreferences();
            }
        })
        .catch(error => {
            // Remove typing indicator
            removeTypingIndicator();
            
            // Show error message
            addBotMessage('Sorry, there was an error processing your request. Please try again.');
            console.error('Error:', error);
        });
    }
    
    // Function to add a user message to the chat
    function addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'chat-message user-message';
        messageElement.textContent = message;
        
        const timeElement = document.createElement('div');
        timeElement.className = 'message-time';
        timeElement.textContent = getCurrentTime();
        
        messageElement.appendChild(timeElement);
        chatMessages.appendChild(messageElement);
        
        // Scroll to the bottom of the chat
        scrollToBottom();
    }
    
    // Function to add a bot message to the chat
    function addBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'chat-message bot-message';
        messageElement.innerHTML = message;
        
        const timeElement = document.createElement('div');
        timeElement.className = 'message-time';
        timeElement.textContent = getCurrentTime();
        
        messageElement.appendChild(timeElement);
        chatMessages.appendChild(messageElement);
        
        // Scroll to the bottom of the chat
        scrollToBottom();
    }
    
    // Function to show typing indicator
    function showTypingIndicator() {
        const typingElement = document.createElement('div');
        typingElement.className = 'chat-message bot-message typing-indicator';
        typingElement.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
        typingElement.id = 'typing-indicator';
        chatMessages.appendChild(typingElement);
        
        // Scroll to the bottom of the chat
        scrollToBottom();
    }
    
    // Function to remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Function to scroll to the bottom of the chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to get the current time
    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // Function to load user preferences
    function loadUserPreferences() {
        fetch(`/api/preferences/${userId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updatePreferencesList(favoriteIngredients, data.favorite_ingredients, 'ingredient');
            updatePreferencesList(favoriteCocktails, data.favorite_cocktails, 'cocktail');
        })
        .catch(error => {
            console.error('Error loading preferences:', error);
        });
    }
    
    // Function to update the preferences list
    function updatePreferencesList(listElement, items, type) {
        // Clear the list
        listElement.innerHTML = '';
        
        if (items.length === 0) {
            const li = document.createElement('li');
            li.className = 'list-group-item text-muted';
            li.textContent = `No favorite ${type}s yet`;
            listElement.appendChild(li);
        } else {
            items.forEach(item => {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                
                const spanTag = document.createElement('span');
                spanTag.className = 'preference-tag';
                spanTag.textContent = item;
                
                const removeIcon = document.createElement('i');
                removeIcon.className = 'fas fa-times';
                removeIcon.addEventListener('click', function() {
                    removePreference(type, item);
                });
                
                spanTag.appendChild(removeIcon);
                li.appendChild(spanTag);
                listElement.appendChild(li);
            });
        }
    }
    
    // Function to remove a preference
    function removePreference(type, item) {
        const data = {
            user_id: userId
        };
        
        if (type === 'ingredient') {
            data.ingredients = [item];
        } else {
            data.cocktails = [item];
        }
        
        fetch('/api/preferences/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Reload preferences
            loadUserPreferences();
        })
        .catch(error => {
            console.error('Error removing preference:', error);
        });
    }
});
