import os
import subprocess
import base64
import tempfile
from dotenv import load_dotenv

# --- Configuration ---
NUM_REPOS = 2
# Load environment variables from .env file
load_dotenv()
USERNAME = os.getenv("GITHUB_USERNAME")
TOKEN = os.getenv("GITHUB_TOKEN")

# --- Utility Functions ---

def subprocess_run_safe(command, cwd=None, env=None):
    """
    Executes a subprocess command and handles errors.
    Returns stdout/stderr combined for logging.
    """
    # CRITICAL: Pass GH_TOKEN environment variable for gh CLI commands.
    # The 'env' is explicitly set to include the existing environment plus the token.
    if env is None:
        env = os.environ.copy()
    if TOKEN:
        env['GH_TOKEN'] = TOKEN

    try:
        result = subprocess.run(
            command,
            check=True,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Log combined output
        output = result.stdout + result.stderr
        # FIX: Process the output string before inserting into the f-string to avoid SyntaxError
        output_to_print = output.strip().replace('\n', ' ')
        
        print(f"    [OUTPUT] Command successful.")
        if output_to_print:
            # Only print output if it exists and is not just empty space
            print(f"    [OUTPUT] {output_to_print}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"    [ERROR] Command failed with exit code {e.returncode}: {' '.join(command)}")
        print(f"    [STDERR] {e.stderr.strip()}")
        # Check specifically if the failure is due to missing GH CLI
        if 'gh: not found' in e.stderr or 'gh: command not found' in e.stderr:
            print("FATAL ERROR: GitHub CLI ('gh') is not installed or not in your PATH.")
        return False
    except FileNotFoundError:
        print("FATAL ERROR: Command executable not found. Is 'git' or 'gh' installed?")
        return False

def get_html_content(repo_name):
    """Generates unique, basic HTML content for the repository's GitHub Page."""
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{repo_name} - GitHub Page</title>
    <style>
        body {{
            font-family: 'Inter', sans-serif;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background-color: #f0f4f8;
            color: #1a202c;
            text-align: center;
        }}
        .container {{
            padding: 2rem;
            border-radius: 12px;
            background: white;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            max-width: 90%;
            transition: all 0.3s ease;
        }}
        h1 {{
            color: #4c51bf;
            margin-bottom: 0.5rem;
        }}
        p {{
            color: #4a5568;
            font-size: 1.1rem;
        }}
        .badge {{
            display: inline-block;
            padding: 0.3rem 0.7rem;
            margin-top: 1rem;
            border-radius: 9999px;
            background-color: #667eea;
            color: white;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.75rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Deployment Success!</h1>
        <p>This page was automatically deployed via the GitHub CLI automation script.</p>
        <p>This is the content for the repository:</p>
        <h2>{repo_name}</h2>
        <span class="badge">Created by {USERNAME}</span>
    </div>
</body>
</html>
    """
    return html_template.strip()

def create_and_setup_repo(repo_name, username, token):
    """Creates repo, commits content using Git, and enables GitHub Pages via gh API."""

    # 1. Create remote repository using GH CLI
    print(f"1. Creating remote repository: {repo_name}...")
    # Use the --public flag to make it immediately visible and eligible for GitHub Pages
    if not subprocess_run_safe(["gh", "repo", "create", f"{username}/{repo_name}", "--public", "--clone=false"]):
        print(f"--- FAILURE: Failed to create repository {repo_name}. ---")
        return

    # 2. Commit files non-interactively using Git and the Token
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = os.path.join(tmpdir, repo_name)
        
        # --- CRITICAL FIX: Use Token in URL for Non-Interactive Git Operations ---
        # Format: https://oauth2:<TOKEN>@github.com/<user>/<repo>.git
        auth_url = f"https://oauth2:{token}@github.com/{username}/{repo_name}.git"

        # 2a. Cloning repository into isolated temporary directory using authenticated URL
        print("2a. Cloning repository into isolated temporary directory...")
        if not subprocess_run_safe(["git", "clone", auth_url, repo_dir]):
            print(f"--- FAILURE: Failed to clone {repo_name}. ---")
            return

        # 2b. Generating and writing index.html
        print("2b. Generating and writing index.html...")
        html_content = get_html_content(repo_name)
        file_path = os.path.join(repo_dir, "index.html")
        with open(file_path, "w") as f:
            f.write(html_content)

        # 2c. Committing and pushing index.html
        print("2c. Committing and pushing index.html...")
        
        # Set directory for Git commands
        # The subsequent git push will use the authenticated URL stored during git clone
        if not subprocess_run_safe(["git", "config", "user.name", "GitHub Automation Script"], cwd=repo_dir): return
        if not subprocess_run_safe(["git", "config", "user.email", "automation@example.com"], cwd=repo_dir): return
        if not subprocess_run_safe(["git", "add", "."], cwd=repo_dir): return
        if not subprocess_run_safe(["git", "commit", "-m", "Initial commit: Add index.html for GitHub Pages"], cwd=repo_dir): return
        
        # This git push should now succeed non-interactively
        if not subprocess_run_safe(["git", "push", "origin", "main"], cwd=repo_dir):
             print(f"--- FAILURE: Failed to push to {repo_name}. This is usually due to an invalid token or permissions. ---")
             return

    # 3. Enable GitHub Pages using gh API
    print("3. Enabling GitHub Pages on 'main' branch...")
    pages_endpoint = f"repos/{username}/{repo_name}/pages"
    
    # Payload to set the source to the 'main' branch root (/)
    payload = '{"source": {"branch": "main", "path": "/"}}'
    
    # The gh api command is authenticated via the GH_TOKEN environment variable
    if not subprocess_run_safe(["gh", "api", "--method", "POST", pages_endpoint, "--input", "-"], input=payload.encode('utf-8')):
        print(f"--- FAILURE: Failed to enable GitHub Pages for {repo_name}. ---")
        return

    print(f"4. Success! Deployment URL: https://{username}.github.io/{repo_name}")
    print(f"--- Process finished for {repo_name} ---")


# --- Main Execution ---
if __name__ == "__main__":
    if not USERNAME:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("FATAL ERROR: GITHUB_USERNAME not found. Set it in the .env file.")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    elif not TOKEN:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("FATAL ERROR: GH_TOKEN not found. Set it in the .env file for portability.")
        print("             This token is required to create repositories.")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        print(f"Starting GitHub CLI automation for user: {USERNAME}")
        print(f"Creating and setting up {NUM_REPOS} repositories...")
        print("-" * 50)

        for i in range(NUM_REPOS):
            repo_name = f"repo_{i}"
            print(f"--- Starting process for {repo_name} (Index: {i}) ---")
            create_and_setup_repo(repo_name, USERNAME, TOKEN)
            print("-" * 50)

        print("Automation complete.")
