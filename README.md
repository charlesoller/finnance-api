# finnance-api
To run locally: 
- Ensure Docker is installed and running on your desktop
  - Use `docker ps` to confirm
- Ensure AWS SAM CLI is installed
- Run the following commands:
```bash
sam build
sam local start-api --env-vars env.json
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

If adding packages run:
pip freeze > requirements.txt
to add to requirements.txt
Best practices:
- Always use absolute imports over relative imports