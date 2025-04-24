# HP Printer Analytics Dashboard - CMU Guest Speaking Session!

This project displays an interactive Streamlit dashboard for analyzing HP printer usage demo data, consumables, errors, and business metrics.

## Overview

The dashboard provides insights into:
* Overall usage trends (total pages, active printers, daily averages).
* Print volume trends over time, segmented by customer type.
* Printer model performance (top models by volume, market share).
* Consumable usage (ink consumption by type and model).
* Printer health (error frequency).
* Business/customer views (regional distribution, active printer counts, revenue contribution).
* Nested data analysis (ink level distribution).

## Prerequisites

* **For Manual Setup:**
    * Python (version 3.8 or higher recommended)
    * `pip` (Python package installer)
    * Git (for cloning the repository)
* **For Docker Setup:**
    * Docker Desktop (Windows/Mac) or Docker Engine (Linux) installed and running.
    * Git (for cloning the repository)

## Manual Setup & Running

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory-name>
    ```
    *(Replace `<your-repository-url>` and `<repository-directory-name>`)*

2.  **Create and Activate a Virtual Environment (Recommended):**
    * On macOS/Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    * On Windows:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install Dependencies:**
    Make sure you are in the project's root directory (where `requirements.txt` is located).
    ```bash
    pip install -r requirements.txt
    ```

4.  **Generate Demo Data:**
    This step creates the necessary CSV files in the `sample_data` directory. Run this from the project's root directory.
    ```bash
    python generate_demo_data.py
    ```
    *(Note: Ensure `generate_demo_data.py` successfully creates the `sample_data` folder with `printers.csv`, `daily_usage.csv`, `printer_errors.csv`, and `revenue_share.csv`)*

5.  **Run the Streamlit App:**
    ```bash
    streamlit run main.py
    ```

6.  **Access the Application:**
    Open your web browser and navigate to the URL provided by Streamlit (usually `http://localhost:8501`).

## Running with Docker (Recommended for Easy Deployment)

Using Docker allows you to run the application in a self-contained environment without needing to manually manage Python versions or dependencies on your host machine (beyond installing Docker itself).

1.  **Clone the Repository (if not already done):**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory-name>
    ```

2.  **Ensure Docker is Running:** Start Docker Desktop or ensure the Docker service is active.

3.  **Build the Docker Image:**
    * Open your terminal or command prompt.
    * Navigate (`cd`) into the project's root directory (the one containing the `Dockerfile`, `main.py`, etc.).
    * Run the build command:
        ```bash
        docker build -t hp-printer-dashboard .
        ```
        * `docker build`: The command to build an image from a Dockerfile.
        * `-t hp-printer-dashboard`: Tags the image with the name `hp-printer-dashboard` for easy reference. You can change this name if you like.
        * `.`: Specifies that the build context (the files needed for the build, including the `Dockerfile`) is the current directory.
    * This process might take a few minutes as Docker downloads the base image, installs dependencies, and runs the data generation script.

4.  **Run the Docker Container:**
    * Once the image is successfully built, run the following command in your terminal:
        ```bash
        docker run -p 8501:8501 hp-printer-dashboard
        ```
        * `docker run`: The command to start a new container from an image.
        * `-p 8501:8501`: Maps port `8501` on your host machine to port `8501` inside the container. Streamlit runs on port `8501` by default inside the container, and this mapping makes it accessible from your host machine's browser.
        * `hp-printer-dashboard`: The name of the image you built in the previous step.
    * You should see output from Streamlit starting up in your terminal.

5.  **Access the Application:**
    * Open your web browser (Chrome, Firefox, etc.).
    * Navigate to: `http://localhost:8501`
    * You should see the HP Printer Analytics Dashboard running.

6.  **Stopping the Container:**
    * **Foreground Mode (Default):** If you ran the `docker run` command as shown above, it runs in the foreground. To stop it, go back to the terminal window where it's running and press `Ctrl + C`.
    * **Detached Mode (Background):** If you want the container to run in the background, add the `-d` flag:
        ```bash
        docker run -d -p 8501:8501 hp-printer-dashboard
        ```
        This will print a container ID and return you to the prompt. To stop it later:
        1.  Find the container ID using `docker ps`.
        2.  Stop the container using `docker stop <container_id>`.

## File Structure