# Echo Game Launcher

Echo Game Launcher is a cross-platform game launcher for your game library with intelligent capabilities. The project is in active development (WIP - Work In Progress), and its goal is to unify games from various services (Steam, Epic Games Store, GOG, etc.) in a single application, enriching them with smart features based on machine learning.

## Table of Contents

-   [Implemented Features](#implemented-features)
-   [Future Plans](#future-plans)
-   [Technology Stack](#technology-stack)
-   [Installation and Launch](#installation-and-launch)
-   [Project Structure](#project-structure)
-   [Contributing](#contributing)
-   [License](#license)
-   [Authors](#authors)
-   [Русская версия документации](README.ru.md)

---

### Implemented Features

-   **Universal Scanning**: Automatic discovery and scanning of games installed from Steam.
-   **IGDB Integration**: Fetches and caches comprehensive game metadata (description, genres, platforms) via the IGDB API.
-   **Dynamic and Animated UI**: An intuitive game gallery with smooth transitions and interactive elements built on PyQt6.
-   **Local Database**: All game data, metadata, and statistics are stored in a local SQLite database.
-   **Known Issues**: In the current version, on a transition to the details page, the gallery tiles visually shift, accompanied by `QPainter` errors in the console.

### Future Plans

-   **ML/AI Integration**:
    -   **Automatic Classification**: Using machine learning to classify games by genre, theme, and mood.
    -   **Personalized Recommendations**: Creating a recommendation system based on user gameplay history.
    -   **Gameplay Session Analysis**: The ability to analyze user gameplay behavior to identify unique patterns.
-   **Expanded Launcher Support**: Integration with Epic Games Store, GOG, Rockstar Games Launcher, and other platforms.
-   **High-Performance Go Core**: Migrating the scanning and process management core from Python to Go for increased speed and efficiency.
-   **Implement filtering, searching, and sorting of games.**
-   **Add settings and customization.**
-   **Improve caching and updating of covers.**
-   **Add unit tests.**

### Technology Stack

The project uses the following technologies:

-   **Python**: The main language for developing the GUI on the PyQt6 framework and for machine learning modules.
-   **Go**: Will be used for the scanning core and other high-performance tasks.
-   **Database**: SQLite for local data storage. (_Transition to PostgreSQL is planned_)

### Installation and Launch

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/FlyingVoodoo/EchoGL.git](https://github.com/FlyingVoodoo/EchoGL.git)
    cd EchoGL
    ```
2.  **Create and activate a virtual environment:**
    * **On Windows:**
        ```sh
        python -m venv venv
        venv\Scripts\activate
        ```
    * **On macOS and Linux:**
        ```sh
        python3 -m venv venv
        source venv/bin/activate
        ```
3.  **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```
4.  **Set up API keys:**
    Create a `.env` file in the project's root directory (`EchoGL/`) and add your keys:
    ```
    TWITCH_CLIENT_ID=your_client_id
    TWITCH_CLIENT_SECRET=your_client_secret
    ```
5.  **Launch the application:**
    ```sh
    python python_modules/main.py
    ```

### Project Structure
```
EchoGL/                         # Project root directory
├── go_modules/
│   └── steam_scanner/          # Go-module for Steam scanning (planned)
├── python_modules/             # Main Python code
│   ├── assets/                 # Resources: style files, fonts, etc.
│   ├── core/                   # Main business logic
│   │   ├── cover_downloader.py   # Module for downloading game covers
│   │   ├── game_manager.py       # Module for managing game data
│   │   └── steam_scanner.py      # Module for scanning Steam libraries
│   ├── data/                   # Data management
│   │   └── db_manager.py         # Module for working with the SQLite database
│   ├── dist/                   # Compiled files
│   │   └── UnifiedGameLauncher.exe
│   ├── ui/                     # User interface
│   │   ├── animated_widgets.py   # Custom animated widgets
│   │   ├── game_details_page.py  # Widget for detailed game information
│   │   ├── game_list_page.py     # Widget for displaying the game list
│   │   ├── main_window.py        # Main window class managing navigation
│   │   └── settings_page.py      # Widget for the settings page
│   ├── utils/                  # Utility modules
│   │   ├── constants.py
│   │   ├── igdb_api_client.py    # Client for working with the IGDB API
│   │   └── metadata_updater.py   # Module for updating game metadata
│   └── main.py                 # Application entry point
├── go.mod                      # Go module dependencies file
├── LICENSE                     # License information
├── README.md                   # This file
└── requirements.txt            # List of Python dependencies
```

### Contributing

The project is open source, and I would be happy to receive any help. If you'd like to contribute or have found a bug, please create an [Issue](https://github.com/FlyingVoodoo/EchoGL/issues) or a [Pull Request](https://github.com/FlyingVoodoo/EchoGL/pulls).

### License

The project is distributed under the GNU GPL v3 license. For more details, see [LICENSE](LICENSE).

### Authors

-   [FlyingVoodoo](https://github.com/FlyingVoodoo)
