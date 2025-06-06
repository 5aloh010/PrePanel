# Lab Data Validator

A Python GUI application for validating lab data by comparing information from JSON and CSV files. The application uses `tkinter` for the user interface, `pandas` for data manipulation, and `fuzzywuzzy` for string matching.

## Requirements

*   Python 3.x
*   The following Python packages:
    *   `pandas`
    *   `fuzzywuzzy`

## Installation

1.  **Clone the repository (if applicable):**
    If your project is in a Git repository, clone it to your local machine:
    ```bash
    git clone <your-repository-url>
    cd <your-project-directory>
    ```
    If you just have the files locally, navigate to the project directory.

2.  **Create a virtual environment (recommended):**
    It's good practice to create a virtual environment for your project to manage dependencies separately.
    ```bash
    python -m venv venv
    ```
    Activate the virtual environment:
    *   On Windows:
        ```bash
        venv\Scripts\activate
        ```
    *   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```

3.  **Install dependencies:**
    Install the required packages using the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

The application is a GUI program. Once started, you will be able to use the interface to browse for your JSON and CSV files and perform validation.

### Using the Command Line

1.  Navigate to the project's root directory in your terminal or command prompt.
2.  Ensure your virtual environment is activated (if you created one).
3.  Run the main script:
    ```bash
    python validate_lab_data.py
    ```

### Using PyCharm

1.  Open your project folder in PyCharm.
2.  PyCharm should automatically detect your `requirements.txt` and may suggest setting up a virtual environment or installing the packages. If not, you can set up a project interpreter and install the packages manually via PyCharm's settings or terminal.
3.  Locate the `validate_lab_data.py` file in the Project view.
4.  Right-click on `validate_lab_data.py` and select "Run 'validate_lab_data'".

This will launch the GUI application.

---

Feel free to modify any part of this README to better suit your project's specifics!