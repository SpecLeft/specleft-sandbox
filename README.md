# specleft-sandbox
A small repository to try the specleft functionality

## Python setup walkthrough

### 1) Prerequisites
- Python 3.13+
- `pip`

### 2) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install project dependencies

```bash
python -m pip install --upgrade pip
python -m pip install .
```

### 4) Run the project

```bash
python main.py
```

You should see:

```text
Hello from specleft-sandbox!
```

### 5) SpecLeft Specs

As part of init setup, there is an example features added in to `.specleft/specs/example-feature.md`

To see the status of the coverage:

```bash
specleft status
```

There are no tests, which means there's no coverage on the define specs.

Feel free to add your own and/or delete the examples ones.

There are two workflows to get a better undersanding of SpecLeft's power. 

#### Agent Driven Worfklow

Give a prompt to your agent to implement features (any you like).

Include in your prompt "follow specleft's SKILL.md" for implementation.

#### Developer Driven Workflow

Follow these steps in your workflow

```markdown
**Add more features**

# Create a new feature spec
specleft features add --id auth --title "Authentication"

# Add a scenario and generate a skeleton test file
specleft features add-scenario \
  --feature auth \
  --title "Successful logout" \
  --step "Given a user has logged in" \
  --step "When the user logs out" \
  --step "Then the user session is ended" \
  --step "And cannot send POST requests to the health endpoint successfully" \
  --add-test skeleton

# Show traceability / coverage status
specleft status
```

#### Implement the code logic

The above steps create a test skeleton - this is your scaffolding.

You can now implement the code and test logic.


### Run tests

```bash
python -m pytest
```

### View the feature coverage report

Get a visual of the coverage

```bash
specleft test report --open-browser
```


### 6) Deactivate the environment

```bash
deactivate
```
