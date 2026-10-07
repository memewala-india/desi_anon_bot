# Telegram Anonymous Chat Bot

This is a simple anonymous chat bot built using Python and the Telegram Bot API. The bot connects random users for anonymous conversations and includes features like pseudonyms, gender-based pairing, and the ability to skip chats.

## Features

- **Random Pairing**: Users are randomly paired for anonymous chat sessions.
- **Pseudonyms**: Each user is assigned a unique pseudonym to maintain anonymity.
- **Gender Selection**: Users can select their gender (male/female) to be paired with a user of the opposite gender.
- **Skip Feature**: Users can skip the current chat and be reconnected with a new random user.
- **Forbidden Words Filter**: Messages containing forbidden words will be blocked.

## Getting Started

### Prerequisites

To run this bot, you'll need the following installed:

- Python 3.x
- Telegram Bot Token (You can get this from [BotFather](https://core.telegram.org/bots#botfather) on Telegram)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/davlix/Telegram-anonymous-chat-bot.git
   cd Telegram-anonymous-chat-bot
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Add your Telegram Bot Token to the bot by modifying the `TOKEN` variable in the `bot.py` file:
   ```python
   TOKEN = 'YOUR_BOT_TOKEN'
   ```

4. Run the bot:
   ```bash
   python bot.py
   ```

### Commands

- `/start`: Starts the bot and prompts the user to choose their gender.
- `/male`: Choose the male gender for pairing with a female user.
- `/female`: Choose the female gender for pairing with a male user.
- `/skip`: Skip the current chat session and be paired with a new user.
- `/logout`: Exit the current chat or waiting queue.

### How It Works

1. When a user types `/start`, they are asked to choose their gender using `/male` or `/female`.
2. After selecting a gender, they are added to a queue to be paired with a user of the opposite gender.
3. Once paired, users can exchange messages anonymously using their pseudonyms.
4. If a user sends `/skip`, they will leave the current chat and be paired with a new user from the queue.
5. The bot ensures that users are only paired with the opposite gender, and offensive words (defined in the `FORBIDDEN_WORDS` list) are filtered out.

## Customization

- **Forbidden Words**: You can add or modify the forbidden words list by updating the `FORBIDDEN_WORDS` variable in the `bot.py` file.
- **Pseudonyms**: Update the `NICKNAMES` list to use different pseudonyms for users.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

