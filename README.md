# finnance-api
To run locally: 
- Ensure you have Python v3.13.1 installed (This is used by the Lambda deployment)
- Create virtual environment
```bash
python3.13 -m venv venv
```
- Ensure you're on the correct version
```bash
python --version
```
- If done properly, this should print Python 3.13.1
- Install dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```
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

Common issues:
- If you randomly can't start the server with a message like "Can't find module lambda_function", this is probably related to Docker. Run the following to stop all containers, remove them, and remove the aws build folder. Then run your watcher.py script and it should be fixed.
```bash
docker stop $(docker ps -a -q)
docker stop $(docker ps -a -q)
rm -rf .aws-sam
```

Best practices:
- If adding any packages, always run the following to add to requirements.txt:
```bash
pip freeze > requirements.txt
```
Or if dev dependency, manually add it to 
```bash
requirements-dev.txt
```
- Always use absolute imports over relative imports (ex. src.modules.services)