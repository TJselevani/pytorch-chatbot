from app.work import create_hybrid_chatbot


def chat_terminal():
    """Run chatbot in terminal mode."""
    bot = create_hybrid_chatbot()

    print(f"{bot.bot_name}: Hello! Type 'quit' to exit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit" or user_input.lower() == "exit":
            print(f"{bot.bot_name}: Goodbye!")
            break
        response = bot.process_message("terminal_user", user_input)
        print(f"{bot.bot_name}: {response[bot.bot_name]}")


if __name__ == "__main__":
    chat_terminal()
