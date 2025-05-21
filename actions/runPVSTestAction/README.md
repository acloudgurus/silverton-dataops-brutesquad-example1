#  PVS Testing Documentation 

##  Overview

The **PVS Testing** module is a post-deployment validation mechanism used in **DataOps pipelines** to ensure that the deployed SQL changes (mainly stored procedures) function as expected. PVS which stands for **Production Volume Stress**, integrates with **TDV (Teradata Vantage)** and **Liquibase** to programmatically run validation checks after Liquibase updates are applied.

---

##  File Structure

- `pvs_testing.py` — Core Python script for PVS Testing
- `action.yml` — GitHub Composite Action wrapper for running the test


---

## High-Level Workflow

1. **Liquibase Changes Applied**  
   The `liquibase-processor.yml` applies Liquibase changes from specified folders (per environment like DEV, UAT, PRD).

2. **Folder List Saved**  
   The paths of these folders (containing changelog files) are saved as a GitHub artifact (`folders.json`).

3. **PVS Test Triggered**  
   If Liquibase update succeeds, the `pvs_testing.py` script is executed via the `runPVSTestAction`.

4. **Stored Procedures Extracted**  
   The script parses each `*.changelog.xml` file to extract `.sql` filenames representing stored procedures.

5. **Stored Procedures Executed**  
   These procedures will be executed using TDV credentials passed via environment variables.

6. **PVS Test Validation**  
   Start and End procedures for PVS will wrap execution and query the result from the `PVS_TEST_INFO_V` view.

7. **Result Check**  
   If `TEST_STATUS` is `FAILED`, the pipeline exits with code 1.

---

## Environment Variables

These will be passed from GitHub Actions:

| Variable          | Required | Description                                 |
|-------------------|----------|---------------------------------------------|
| `TDV_ENV`         | ✅       | Environment (e.g., DEV, UAT, PRD)           |
| `FOLDER_LIST`     | ✅       | JSON list of folder paths with changelogs   |
| `TDV_USERNAME`    | ✅       | TDV Username (LDAP)                         |
| `TDV_PASSWORD`    | ✅       | TDV Password                                |

---

## Functionality Breakdown

### 1. **Folder & Environment Initialization**

```python
tdv_env = os.getenv("TDV_ENV")
folder_list = json.loads(os.getenv("FOLDER_LIST"))
```

Used to locate changelog files named like `dev.changelog.xml`.

---

### 2. **Extract Stored Procedures**

```python
def extract_sql_names_from_changelog(file_path):
    ...
```

- Uses XML parsing via `ElementTree`
- Finds `<include file="...sql"/>`
- Extracts only the `.sql` file **base names** (e.g., BLUE_PRINTS_SAMPLE_RUN_SPROC_1.sql -> BLUE_PRINTS_SAMPLE_RUN_SPROC_)

---

### 3. **TDV Connection and Execution (Planned)**

```python
with teradatasql.connect(...) as td_conn:
    ...
```

- Establishes secure LDAP connection to Teradata
- Executes:
  - `START_PVS_TEST(...)`
  - Run Stored Procedures
  - `END_PVS_TEST(...)`
  - Validates via:  
    ```sql
    SELECT TEST_STATUS FROM PVS_TEST.PVS_TEST_INFO_V
    ```

---

### 4. **Error Handling and Exit**

```python
def _pass_or_fail(result_dict):
    if result_dict['TEST_STATUS'][0] == 'FAILED':
        exit(1)
```

- If the result is a failure, the script halts the workflow.

---

## Local Debugging

Before integrating into CI/CD:

```bash
export TDV_ENV=dev
export FOLDER_LIST='["/path/to/sql/folder"]'
python pvs_testing.py
```

Note: Requires `teradatasql`, `pandas`, and valid `.changelog.xml`.

---

## GitHub Integration

### Composite Action: `action.yml`

This wraps the script into a reusable action with:

- Python 3.10 setup
- Poetry dependency management
- Input forwarding (`TDV_ENV`, `TDV_DEV_USERNAME`, `TDV_DEV_PASSWORD`)


---

## Tech Stack

- **Python** 3.10
- **Pandas** — Query handling
- **ElementTree** — XML Parsing
- **Liquibase** — DB Change management
- **GitHub Actions** — CI/CD
- **Teradata SQL** — Validation engine

---

##  Example changelog (XML)

```xml
<databaseChangeLog
    xmlns="http://www.liquibase.org/xml/ns/dbchangelog">
    
    <include file="proc/calculate_interest.sql"/>
    <include file="proc/update_balance.sql"/>
</databaseChangeLog>
```

---

## Final Outcome

Upon successful execution, all updated stored procedures are validated. If any test fails, the deployment is stopped with full traceability and logs for audit and remediation.
