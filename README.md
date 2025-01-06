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

Best practices:
- Always use absolute imports over relative imports