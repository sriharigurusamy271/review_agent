import os
from google import genai
from github import Github

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
API_KEY = os.getenv("GEMINI_API_KEY")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("PR_NUMBER")

client = genai.Client(api_key=API_KEY)

def analyze_code(diff_text):
    prompt = """You are an automated code reviewer.

    Analyze the following GitHub pull request diff.

    Focus on identifying:
    - Potential bugs or logical errors
    - Security or safety concerns
    - Performance or optimization opportunities
    - Code quality or maintainability issues

    Guidelines:
    - Be concise and actionable
    - Reference file names and line numbers where possible
    - Do NOT repeat the diff
    - Do NOT suggest changes unrelated to the diff
    - If no issues are found, explicitly say so

    Provide the feedback in clear bullet points grouped by category."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{prompt}\n\n  GIT DIFF:\n{diff_text}"
        )
        return response.text
    except Exception as e:
        return f"Error while analysing the code {str(e)}"

def main():
    if not GITHUB_TOKEN or not API_KEY:
        print("INsufficient Data")
        return
    
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    pr = repo.get_pull(int(PR_NUMBER))

    print(f"fetching diffence in the PR {PR_NUMBER}")

    diff_content = ""

    for file in pr.get_files():
        if file.status == "removed":
            return
        if not file.filename.endswith(('.py','.js','.ts','.java','.cpp','.html','.css')):
            continue
        diff_content += f"\n\n--- File:{file.filename} ---\n{file.patch}"

    if not diff_content:
        print("No changes found")
        return
    
    print("Sending message to gemini...")
    review = analyze_code(diff_content)

    print("Posting comments to Githib...")
    pr.create_issue_comment(f"Agent Review: {review}")
    print("Done")

if __name__ == "__main__":
    main()