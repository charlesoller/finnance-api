# finnance-api
To run locally: 
- Ensure Docker Desktop is installed and running on your desktop
  - Use `docker ps` to confirm
- Ensure AWS SAM CLI is installed
- Obtain env.json and ddb_cf_template.json files
- Run the following commands:
```bash
python src/watcher.py
```
- This restarts on changes, as well as keeping your Docker containers and .aws-sam build directory clear

Alternatively, to start without changes triggering a restart, you can run:
```bash
sam build
sam local start-api --env-vars env.json
```
- This is what the watcher is running under the hood 

DynamoDB (local setup)
  - Install NoSQL Workbench 
  - Import ddb_cf_template.json (not included in Git repository, must request)
  - Toggle to run database in lower left corner
  - To verify local DDB is running, run:
```bash
aws dynamodb list-tables --endpoint-url http://localhost:8000
```

Linting: 
- Uses pylint, flake8, black, isort, and mypy
- To run:
```bash
  isort src/
  black src/
  pylint src/
  flake8 src/
  mypy src/
```
- I recommend installing the VSCode extension for each of these to get inline linting

- Pre-commit
  - Runs on all staged files using:
```bash
  pre-commit run --all-files
```
  - If you need to modify .pre-commit-config.yaml, make modification, then run:
```bash
pre-commit clean
pre-commit install
pre-commit run --all-files
```
  - You should see the console print out some Passed/Failed messages if it worked correctly
  - If it didn't work correctly, run the linting script above



Best practices:
- If adding any packages, always run the following to add to requirements.txt:
```bash
pip freeze > requirements.txt
```
- Always use absolute imports over relative imports (ex. src.modules.services)