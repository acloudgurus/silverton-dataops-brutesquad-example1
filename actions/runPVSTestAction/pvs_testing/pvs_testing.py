## Highest priority
## TODO-1: Create functions to replace large chunks of coupled code

## TODO-2: Add "_" to beginning internal functions
## TODO-Continued: Internal function is one that is called by another function, not main


import os
from datetime import datetime
import pandas as pd
import teradatasql
import logging
import sys
import glob
import json
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# # Executes SQL query given against td_conn passed into function
def execute_tdv_query(td_conn, query):
    query_result = pd.read_sql(query, td_conn)
    logger.info({'query': query, 'result': query_result})
    try:
        return query_result.to_dict()
    except Exception as e:
        logger.info(str(e))
        return {}


# # Returns results of the PVS TEST when passing in results from PVS TEST TABLE sql query
def pass_or_fail(result_dict):
    pvs_result = result_dict['TEST_STATUS'][0]
    logger.info(pvs_result)
    if pvs_result == 'FAILED':
        logger.info("FAILURE")
        exit(1)

# Fetch files from the tables folder
def fetch_all_sql_files(base_folder):
    tables_path = os.path.join(base_folder, 'tables')
    sql_files = []

    if not os.path.exists(tables_path):
        logger.info(f"No tables directory in {base_folder}")
        return []

    for filename in os.listdir(tables_path):
        if filename.endswith(".sql"):
            sql_files.append(os.path.join(tables_path, filename))

    return sql_files

# Extracting the stored procedure name
def extract_proc_names_from_file(filepath):
    extracted_procs = []

    with open(filepath, 'r') as f:
        file_content = f.read()  # Read the entire file at once
    
    # Regex to find CREATE PROCEDURE/FUNCTION containing ${dbEnv}
    pattern = r'(?i)\b(create|replace|update)\s+(procedure\s+)?(\S+\$\{dbEnv\}\.\S+)'
    matches = re.findall(pattern, file_content)

    for match in matches:
        proc_name = match[2]  # Group capturing schema.${dbEnv}.object
        extracted_procs.append(proc_name)
    

    return extracted_procs




def main():

    # Capture environment relevant env vars
    folder_list = os.environ.get("FOLDER_LIST")
    teradata_dir_list = os.environ.get("DIRECTORY_LIST")
    logger.info(f"teradata_folder_list: {teradata_dir_list}")

    # Validate folder_list env variable
    if not folder_list:
        logger.info("FOLDER_LIST not found in env")
        return
    try:
        folder_list = json.loads(folder_list)
    except Exception as e:
        logger.info("Failed to parse FOLDER_LIST:", e)
        return
    folder_list = [folder for folder in folder_list if folder.strip()]
    logger.info(f"folder_list: {str(folder_list)}")

    # TODO: Comment describing block
    final_proc_list = []
    for folder in folder_list:
        logger.info(f"Searching in Folder: {folder}")
        sql_files = fetch_all_sql_files(folder)
        logger.info(f"Found {len(sql_files)} SQL files in {folder}")
        for sql_file in sql_files:
            procs = extract_proc_names_from_file(sql_file)
            if procs:
                logger.info(f"Extracted from {sql_file}: {procs}")
                final_proc_list.extend(procs)
    # final_proc_list = list(set(final_proc_list))
    proc_set = set()
    logger.info("\n==== FINAL LIST OF PROCEDURES/FUNCTIONS FOUND ====")
    for proc in final_proc_list:
        # Insert env variable into sp with correct syntax
        string_proc = str(proc).replace("${dbEnv}.", "_" + os.environ.get("TDV_ENV") +".")
        string_proc = string_proc+"()"
        # Convert list into set - Eliminating duplicates
        proc_set.add(string_proc)

    # Convert set of stored procs back into list
    procs_clean = list(proc_set)
    logger.info("PROCS CLEAN: ")
    for x in procs_clean:
        logger.info(x)

    # Initialize variables with environment variable values for connecting to database
    teradata_username = os.environ.get("TDV_USERNAME")
    teradata_password = os.environ.get("TDV_PASSWORD")
    teradata_host_server = "hstntduat.healthspring.inside"

    # Construct WorkItemID string parameter
    change_num = os.environ.get("ChangeTicket_Num")
    task_num = os.environ.get("CTASK_NUM")
    work_item_id = f"CHG{change_num}_CTASK{task_num}"
    logger.info(f"WorkitemID: {work_item_id}")

    # Define queries to be used for PVS Testing loop
    pvs_table_result_query = f"select TEST_STATUS from PVS_TEST.PVS_TEST_INFO_V where USER_NAME = '{teradata_username}' and WORK_ITEM = '{work_item_id}'"
    start_test_procedure = f"CALL PVS_TEST.START_PVS_TEST('{teradata_username}','{work_item_id}',PROC_MSG)"
    end_test_procedure = f"CALL PVS_TEST.END_PVS_TEST('{teradata_username}','{work_item_id}',PROC_MSG)"

    # PVS testing loop
    # with teradatasql.connect(
    #             host=teradata_host_server,
    #             user=teradata_username,
    #             password=teradata_password,
    #             LOGMECH="LDAP",
    #             encryptdata=True
    #     ) as td_conn:
    
    #     # Start PVS Test
    #     logger.info(f"Executing Start PVS Test")
    #     execute_tdv_query(td_conn=td_conn, query=start_test_procedure)

    #     # Run stored procedure(s)
    #     for sp in procs_clean:
    #         logger.info(f"Executing Stored Procedure: {sp}")
    #         execute_tdv_query(td_conn=td_conn, query="CALL " + sp)

    #     # End PVS Test
    #     logger.info(f"Executing End PVS Test")
    #     execute_tdv_query(td_conn=td_conn, query=end_test_procedure)

    #     # Get results
    #     logger.info(f"Result of PVS Test")
    #     pvs_result = execute_tdv_query(td_conn=td_conn, query=pvs_table_result_query)
    #     pass_or_fail(pvs_result)


if __name__ == "__main__":
    main()
