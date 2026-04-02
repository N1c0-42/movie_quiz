# Filmquiz Deluxe

## Project Overview
"Filmquiz Deluxe" is a local network, interactive movie quiz application built with Python and Streamlit. It's designed for a group of specific players (Daniel, Marlon, Sabbl, Nico, Gast) and features two main components:
1.  **Player View (Mobile/Tablet):** Allows participants to submit their answers to quiz questions via their own devices.
2.  **Moderator & Scoreboard View (Beamer/Screen):** A central dashboard for the quiz master to manage the game, view incoming answers live, and display a visually appealing HTML-based scoreboard.

### Main Technologies
*   **Python:** Core logic and backend.
*   **Streamlit:** Web framework for the UI (both player and moderator views).
*   **HTML/CSS/JavaScript:** Used for the customized, standalone scoreboard (`movie_quiz_board.htm`) which is embedded into the Streamlit app.
*   **JSON:** Simple file-based database (`quiz_data.json`) for temporary storage of player answers.

## Building and Running
To run the application, you need Python and the required libraries (Streamlit, pandas, qrcode). 

1.  Ensure dependencies are installed (you may need to install them manually as there is no `requirements.txt` present):
    ```bash
    pip install streamlit pandas qrcode
    ```
2.  Start the application using Streamlit:
    ```bash
    streamlit run quiz_app.py
    ```
3.  The app will open in your browser. The Moderator view will provide a QR code and a local network link for players to join.

## Development Conventions
*   **Architecture:** The app uses Streamlit's query parameters (`?view=player`) to differentiate between the "player" view and the "moderator" view within the same `quiz_app.py` script.
*   **State Management:**
    *   Streamlit's `st.session_state` is used for player session handling.
    *   A local `quiz_data.json` file is used as a rudimentary database to pass answers from the player sessions to the moderator session.
    *   The HTML scoreboard (`movie_quiz_board.htm`) relies on browser `localStorage` to persist the overall game score and progress across reloads independently of the Python backend.
*   **UI/UX:** The project employs modern UI design principles with custom CSS injected into Streamlit and a dedicated, styled HTML file for the scoreboard.
