# Automated GitHub Repository Generator
This Python script automates the creation of multiple new GitHub repositories, initializes them with a basic index.html file, and automatically enables GitHub Pages for immediate deployment.

The script uses the official GitHub CLI (gh) for all remote operations, ensuring that the new repositories are created outside of this parent repository.

## Project Structure
```
├── github_repo_creator.py  # Main script
├── .env                    # Configuration file (ignored by Git)
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Prerequisites
You must have the following installed on your system:

1. Python 3 (3.8 or higher recommended)

2. Git

3. GitHub CLI (gh): Install instructions can be found on the GitHub CLI documentation.

## Setup and Configuration Steps
__Step 1__: Clone the Repository
Clone this project to your local machine:

git clone [your_repo_url]
cd [your_repo_name]


__Step 2__: Create Environment and Install Dependencies
This step creates the virtual environment and installs the required packages (python-dotenv) in one workflow.

# 1. Create the environment
python3 -m venv venv

# 2. Activate the environment (REQUIRED) and install dependencies
# On macOS/Linux (use one line):
source venv/bin/activate && pip install -r requirements.txt

# On Windows (Command Prompt - use two lines):
.\venv\Scripts\activate
pip install -r requirements.txt

__Step 3__: Configure Authentication with PAT (Required for Portability)
For this script to run automatically by any user, it requires a Personal Access Token (PAT) with the necessary permissions.

### Generate a PAT:

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic).

2. Click Generate new token.

3. Scopes: The crucial step is to grant it the repo scope (full control of private repositories).

4. Copy the generated token immediately—you won't see it again.

### Configure the .env file:
Update the .env file with your GitHub username and the token you just created.

# .env
GITHUB_USERNAME=your_actual_username
GH_TOKEN=your_personal_access_token_here  # Paste your PAT here


__Crucial:__ The GH_TOKEN variable is now required. The script will fail if it's missing, ensuring secure and automated operation.

## Running the Code
Once the environment is set up and the .env file is configured, you can run the main script:

python github_repo_creator.py


The script will handle the creation, content commit, and GitHub Pages activation for all repositories defined in the script's configuration.
