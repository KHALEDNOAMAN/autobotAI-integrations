from github import Auth, Github
import dotenv, os

dotenv.load_dotenv()
token = str(os.environ["GITHUB_TOKEN"])

auth = Auth.Token(token)
gh = Github(auth=auth)

gh.close()
# result = []
# for repo in gh.get_user().get_repos():
#     details = {
#         "name": repo.name,
#         "url": repo.url,
#         "stars_count": repo.stargazers_count,
#     }
#     result.append({
#         "id": repo.id,
#         "details": details,
#     })