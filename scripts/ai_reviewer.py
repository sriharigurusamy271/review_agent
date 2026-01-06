import os
from google import genai
from github import Github

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
API_KEY = os.getenv("GEMINI_API_KEY")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("PR_NUMBER")

client = genai.Client(api_key=API_KEY)

def analyze_code(diff_text):
    prompt = """You are a senior software engineer acting as a code reviewer.

            Review the following GitHub Pull Request diff as if it will be merged into a
            long-term, production codebase maintained by multiple teams.

            Your goal is to identify issues that could:
            - Cause bugs or incorrect behavior
            - Introduce security or reliability risks
            - Impact performance or scalability
            - Reduce readability or maintainability over time

            Review guidelines:
            - Focus only on meaningful, high-signal issues
            - Prefer practical, defensive improvements
            - Avoid stylistic nitpicks unless they affect clarity or safety
            - Do not speculate beyond what is visible in the diff

            Response format (STRICT):
            - Group feedback under clear headings (e.g., Bug, Security, Maintainability)
            - Each finding MUST be at most **2 short lines**
            - First line: describe the issue
            - Second line: give a concrete improvement or recommendation
            - Reference file names and line numbers where applicable
            - Use concise bullet points only
            - Do NOT repeat or summarize the diff
            - Do NOT include long explanations or justification paragraphs
            - If no issues are found, state: “No significant issues found; changes look production-ready.”

            Audience:
            - Senior engineers and tech leads
            - Keep feedback precise, direct, and easy to scan

        """

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