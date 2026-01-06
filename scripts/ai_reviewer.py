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
        production codebase maintained long-term by multiple teams.

        Your goal is to identify issues that could:
        - Cause bugs or incorrect behavior now or in the future
        - Introduce security, reliability, or data integrity risks
        - Create performance bottlenecks or scalability problems
        - Reduce code readability, testability, or maintainability over time
        - Violate best practices or architectural principles

        Review guidelines:
        - Think defensively and assume this code will evolve
        - Call out edge cases, failure scenarios, and hidden assumptions
        - Suggest improvements only when they provide clear value
        - Prefer simple, robust solutions over clever ones
        - Avoid stylistic nitpicks unless they impact clarity or safety

        Response format:
        - Group feedback under clear headings (e.g., Bugs, Security, Performance, Maintainability)
        - Use concise, actionable bullet points
        - Reference file names and line numbers where applicable
        - Do NOT repeat or summarize the diff
        - Do NOT suggest changes unrelated to the diff
        - If no issues are found, explicitly state that the changes look solid and production-ready

        Audience:
        - Assume the feedback will be read by senior engineers, tech leads, or engineering managers.
        - Be precise, professional, and focused on long-term impact.
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