# Azure DevOps – Monorepo Conditional Build Pipeline

# Goal: Only build the service folder that had changes, leave the others alone

---

## The Full Pipeline File (`azure-pipelines.yml`)

```yaml
# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER
# "When should this whole pipeline start running?"
# ─────────────────────────────────────────────────────────────────────────────

trigger:               # This tells Azure DevOps when to automatically run this pipeline
  branches:
    include:
      - main           # ONLY run this pipeline when someone pushes code to the "main" branch
                       # If someone pushes to a feature branch, nothing happens here


# ─────────────────────────────────────────────────────────────────────────────
# POOL
# "What kind of computer should run these tasks?"
# ─────────────────────────────────────────────────────────────────────────────

pool:
  vmImage: 'ubuntu-latest'   # Use a fresh Ubuntu Linux machine (provided by Azure)
                             # Think of this as renting a temporary computer for the build


# ─────────────────────────────────────────────────────────────────────────────
# JOBS
# A "job" is a group of steps/tasks that run together on that computer above
# ─────────────────────────────────────────────────────────────────────────────

jobs:


# ══════════════════════════════════════════════════════════════════════════════
# JOB 1: DetectChanges
# "Before we do anything, let's first figure out WHAT actually changed."
# ══════════════════════════════════════════════════════════════════════════════

- job: DetectChanges          # Name of this job (we reference this name later)
  steps:                      # The list of tasks this job will perform, in order

  - checkout: self            # Step 1: Download the repo code onto the temp machine
    fetchDepth: 0             # fetchDepth: 0 means "download the FULL git history"
                              # We need history so that git can compare current vs previous code

  - bash: |                   # Step 2: Run a Bash (Linux terminal) script
                              # The | symbol means "the script starts on the next line"

      # Ask git: "Which files were different between the last commit and the one before it?"
      # HEAD    = the latest commit (what just got pushed)
      # HEAD~1  = one commit before that (the previous state)
      CHANGED=$(git diff --name-only HEAD HEAD~1)
      # CHANGED is now a variable holding a list of file paths, e.g.:
      #   backend/main.py
      #   backend/requirements.txt
      #   analytics-reporter/index.js

      # Print that list to the build log so we can see it (useful for debugging)
      echo "Changed files:"
      echo "$CHANGED"

      # ── FLAG FOR BACKEND ────────────────────────────────────────────────
      # Check if any of the changed files start with "backend/"
      # grep -q 'backend/' checks quietly (no output), just returns true or false
      # If true  → we set buildBackend to "yes"
      # If false → we set buildBackend to "no"
      # The ##vso[...] part is Azure DevOps special syntax to save a variable
      # isOutput=true means: "other jobs can read this variable too"
      echo "##vso[task.setvariable variable=buildBackend;isOutput=true]$(echo "$CHANGED" | grep -q 'backend/' && echo 'yes' || echo 'no')"

      # ── FLAG FOR FRONTEND ───────────────────────────────────────────────
      # Same thing, but checking for "frontend/"
      echo "##vso[task.setvariable variable=buildFrontend;isOutput=true]$(echo "$CHANGED" | grep -q 'frontend/' && echo 'yes' || echo 'no')"

      # ── FLAG FOR ANALYTICS REPORTER ─────────────────────────────────────
      # Same thing, but checking for "analytics-reporter/"
      echo "##vso[task.setvariable variable=buildAnalytics;isOutput=true]$(echo "$CHANGED" | grep -q 'analytics-reporter/' && echo 'yes' || echo 'no')"

    name: flags               # Give this bash script step a name: "flags"
                              # We use this name later to read the variables it set
                              # Syntax: DetectChanges.outputs['flags.buildBackend']


# ══════════════════════════════════════════════════════════════════════════════
# JOB 2: BuildBackend
# "Build the Backend — but ONLY if it had changes."
# ══════════════════════════════════════════════════════════════════════════════

- job: BuildBackend
  dependsOn: DetectChanges    # "Wait for the DetectChanges job to finish first"
                              # We need it to finish so we can read its flags

  condition: eq(dependencies.DetectChanges.outputs['flags.buildBackend'], 'yes')
  # condition = "Only run this job if the following is true:"
  # eq(...)   = "equals" check
  # dependencies.DetectChanges.outputs['flags.buildBackend']
  #           = "look at DetectChanges job → the 'flags' script → the buildBackend variable"
  # 'yes'     = and check if it equals the word "yes"
  # Summary:  → If backend/ had changes, run. If not, skip.

  steps:
  - script: echo "Building Backend"   # Replace this line with your real build commands
                                      # e.g. pip install, pytest, docker build, etc.


# ══════════════════════════════════════════════════════════════════════════════
# JOB 3: BuildFrontend
# "Build the Frontend — but ONLY if it had changes."
# ══════════════════════════════════════════════════════════════════════════════

- job: BuildFrontend
  dependsOn: DetectChanges    # Same: wait for DetectChanges to finish first

  condition: eq(dependencies.DetectChanges.outputs['flags.buildFrontend'], 'yes')
  # Same logic as above, but reading the buildFrontend flag instead

  steps:
  - script: echo "Building Frontend"   # Replace with your actual frontend build steps


# ══════════════════════════════════════════════════════════════════════════════
# JOB 4: BuildAnalytics
# "Build the Analytics Reporter — but ONLY if it had changes."
# ══════════════════════════════════════════════════════════════════════════════

- job: BuildAnalytics
  dependsOn: DetectChanges    # Same: wait for DetectChanges to finish first

  condition: eq(dependencies.DetectChanges.outputs['flags.buildAnalytics'], 'yes')
  # Same logic as above, but reading the buildAnalytics flag instead

  steps:
  - script: echo "Building Analytics Reporter"   # Replace with your actual analytics-reporter build steps
```

---

## How It All Flows (Plain English)

```
Push code to "main"
        │
        ▼
  [ DetectChanges ]
  "Which files changed?"
  git diff HEAD HEAD~1
        │
        ├── backend/ changed?            → set buildBackend  = "yes"
        ├── frontend/ changed?           → set buildFrontend = "no"
        └── analytics-reporter/ changed? → set buildAnalytics = "yes"
        │
        ▼
  ┌───────────────┬─────────────────┬──────────────────────┐
  │ BuildBackend  │  BuildFrontend  │   BuildAnalytics     │
  │  flag=yes     │   flag=no       │    flag=yes          │
  │  ✅ RUNS      │   ⏭ SKIPPED     │    ✅ RUNS            │
  └───────────────┴─────────────────┴──────────────────────┘
```

---

## Key Concepts Glossary

| Term | What it means in plain English |
|---|---|
| `trigger` | "What event starts this pipeline?" |
| `pool` | "What computer runs the tasks?" |
| `job` | "A group of steps that run together" |
| `dependsOn` | "Don't start until this other job is done" |
| `condition` | "Only run if this check passes" |
| `checkout: self` | "Download my repo code onto the temp machine" |
| `fetchDepth: 0` | "Download the full git history, not just the latest" |
| `git diff HEAD HEAD~1` | "Show me what files changed in the last commit" |
| `grep -q 'backend/'` | "Quietly check if 'backend/' appears in the list" |
| `##vso[task.setvariable...]` | "Azure DevOps, please save this value for other jobs to use" |
| `isOutput=true` | "Let other jobs read this variable, not just this one" |
| `dependencies.X.outputs['y.z']` | "Read the variable 'z' that was set by job X, step y" |
