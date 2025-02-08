# RestrictedContentDL

<p align="center">
  <a href="https://github.com/abirxdhack/RestrictedContentDL/stargazers"><img src="https://img.shields.io/github/stars/abirxdhack/RestrictedContentDL?color=blue&style=flat" alt="GitHub Repo stars"></a>
  <a href="https://github.com/abirxdhack/RestrictedContentDL/issues"><img src="https://img.shields.io/github/issues/abirxdhack/RestrictedContentDL" alt="GitHub issues"></a>
  <a href="https://github.com/abirxdhack/RestrictedContentDL/pulls"><img src="https://img.shields.io/github/issues-pr/abirxdhack/RestrictedContentDL" alt="GitHub pull requests"></a>
  <a href="https://github.com/abirxdhack/RestrictedContentDL/graphs/contributors"><img src="https://img.shields.io/github/contributors/abirxdhack/RestrictedContentDL?style=flat" alt="GitHub contributors"></a>
  <a href="https://github.com/abirxdhack/RestrictedContentDL/network/members"><img src="https://img.shields.io/github/forks/abirxdhack/RestrictedContentDL?style=flat" alt="GitHub forks"></a>
</p>

RestrictedContentDL is a Telegram bot script that allows you to download media from restricted channels and groups, both public and private. The bot can handle photos, videos, audio, documents, and text messages, making it a versatile tool for managing Telegram content.

## ✨ Features

- 📷 Download media (photos, videos, audio, documents) from restricted Telegram channels and groups.
- 🌐 Supports both public and private channels.
- 📚 Handles media groups and individual messages.
- 📈 Provides progress updates during the download process.
- 🗑️ Deletes the downloaded file after uploading it to the chat.

## 🛠️ Requirements

- 🐍 Python 3.8 or higher
- 📦 Required libraries: `pyrogram`, `pyleaves`, `urllib`

## 🚀 Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/abirxdhack/RestrictedContentDL.git
    cd RestrictedContentDL
    ```

2. **Install the required libraries:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Configure the bot:**

    Create a `config.py` file in the project directory with the following content:

    ```python
    API_ID = "your_api_id"
    API_HASH = "your_api_hash"
    BOT_TOKEN = "your_bot_token"
    SESSION_STRING = "your_session_string"
    ```

    Replace `your_api_id`, `your_api_hash`, `your_bot_token`, and `your_session_string` with your actual values. You can get your API ID and API Hash from [my.telegram.org](https://my.telegram.org), and your bot token from [@BotFather](https://t.me/BotFather). To get the session string, use a tool like [Telethon](https://github.com/LonamiWebs/Telethon) or [Pyrogram](https://github.com/pyrogram/pyrogram).

## 📋 Usage

1. **Start the bot:**

    ```bash
    python media_bot.py
    ```

2. **Interact with the bot:**

    - **Start the bot:**

      Send the `/start` command to the bot to receive a welcome message.

    - **Get help:**

      Send the `/help` command to the bot to receive instructions on how to use it.

    - **Download media:**

      Send the `/dl post URL` command to download media from a specific message. Replace `post URL` with the actual URL of the Telegram message.

      **Example:**

      ```text
      /dl https://t.me/channelname/123
      ```
      ```text
      /dl https://t.me/c/2155004811/194
      ```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 👤 Author
- Name: Bisnu Ray 
- Telegram: [@TheSmartBisnu](https://t.me/TheSmartBisnu)
- **Name:** Abir Arafat
- **GitHub:** [abirxdhack](https://github.com/abirxdhack)

Feel free to reach out if you have any questions or feedback.
