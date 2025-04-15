import os
from typing import Any, Dict, Set
import yaml
import time

from autogen_core.models import (
    ChatCompletionClient,
)
from autogen_ext.experimental.task_centric_memory import MemoryController
from autogen_ext.experimental.task_centric_memory.utils import Apprentice, Grader, PageLogger


async def eval_retrieval_2(memory_controller: MemoryController, client: ChatCompletionClient,
                         logger: PageLogger, config: Dict[str, Any], run_dict: Dict[str, Any]) -> str:
    """
    Evaluates precision and recall of task-centric memory retrieval.
    """
    logger.enter_function()

    # Load the specified data.
    query_task_files = run_dict["query_tasks"]
    query_task_list = []
    for query_task_file in query_task_files:
        with open(query_task_file, "r") as file:
            query_task = yaml.load(file, Loader=yaml.FullLoader)
            query_task_list.append(query_task["task_description"])

    stored_task_files = run_dict["tasks_to_store"]
    stored_task_list = []
    for stored_task_file in stored_task_files:
        with open(stored_task_file, "r") as file:
            stored_task = yaml.load(file, Loader=yaml.FullLoader)
            stored_task_list.append(stored_task["task_description"])

    insight_files = run_dict["insights"]
    insight_list = []
    for insight_file in insight_files:
        with open(insight_file, "r") as file:
            insight = yaml.load(file, Loader=yaml.FullLoader)
            insight_list.append(insight["insight"])

    # Make sure the number of tasks and insights match.
    num_tasks = len(query_task_list)
    assert num_tasks == len(stored_task_list), "Number of query and stored tasks must match."
    assert num_tasks == len(insight_list), "Number of tasks and insights must match."

    # Load the current partition index.
    with open(run_dict["partition_index_filename"], "r") as file:
        partition_index = int(file.read().strip())
    logger.info(f"Partition index: {partition_index}")

    # Use the index to read the corresponding partition.
    with open(run_dict["partitions_filename"], "r") as file:
        partitions = file.readlines()
        num_partitions = len(partitions)
        partition_index = partition_index % num_partitions
        partition = partitions[partition_index].strip()
        logger.info(f"Partition: {partition}")
        assert len(partition) == num_tasks, "Partition length must match number of tasks."

    # Read the output filename, and make sure its directory exists.
    output_filename = run_dict["output_filename"]
    output_dir = output_filename.rsplit("/", 1)[0]
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Clear the counters.
    num_memos_stored = 0
    num_retrieval_operations = 0
    num_retrieved = 0
    num_relevant = 0
    num_relevant_and_retrieved = 0
    total_storage_time = 0.
    total_retrieval_time = 0.
    retrieval_time_for_existing_plans = 0.  # Whether any plan was retrieved or not.
    retrieval_time_for_missing_plans = 0.   # Whether any plan was retrieved or not.

    # Loop over each side of the partition, storing the corresponding half of the tasks in memory each time.
    for side_i in range(2):
        storage_flag = str(side_i)
        logger.info(f"Storing tasks with flag: {storage_flag}")

        # Clear memory, then store the tasks specified by the partition.
        memory_controller.reset_memory()
        start_storage_time = time.time()
        for i in range(num_tasks):
            if partition[i] == storage_flag:
                await memory_controller.add_memo(task=stored_task_list[i], insight=insight_list[i], index_on_both=False)
                num_memos_stored += 1
                logger.info(f"Stored task: {stored_task_list[i]}")
                logger.info(f"Stored insight: {insight_list[i]}")
        total_storage_time += time.time() - start_storage_time

        # Test memory retrieval.
        for i in range(num_tasks):
            query_task = query_task_list[i]
            logger.info(f"\nQuery task: {query_task}")
            plan_was_stored = (partition[i] == storage_flag)
            logger.info(f"Was a corresponding plan stored?  {plan_was_stored}")

            # Time the retrieval operation.
            start_retrieval_time = time.time()
            memos = await memory_controller.retrieve_relevant_memos(task=query_task)
            retrieval_time = time.time() - start_retrieval_time
            total_retrieval_time += retrieval_time
            if plan_was_stored:
                retrieval_time_for_existing_plans += retrieval_time
            else:
                retrieval_time_for_missing_plans += retrieval_time

            assert len(memos) <= 1, "No more than one memo should be retrieved."
            num_retrieval_operations += 1

            # Accumulate the counts.
            if plan_was_stored:
                num_relevant += 1
                logger.info(f"A similar task was stored.")
            else:
                logger.info(f"No similar task was stored.")
            if len(memos) > 0:
                num_retrieved += 1
                logger.info(f"Insight retrieved: {memos[0].insight}")
                if plan_was_stored:
                    if memos[0].insight == insight_list[i]:
                        num_relevant_and_retrieved += 1
                        logger.info(f"Correct plan retrieved.")
                    else:
                        logger.info(f"Erroneous retrieval (wrong plan).")
                else:
                    logger.info(f"Erroneous retrieval (nothing should have been found).")
            else:
                logger.info(f"No insight was retrieved.")

    logger.info(f"\nNumber of memos stored: {num_memos_stored}")
    logger.info("\nNum retrieved:  {}".format(num_retrieved))
    logger.info("\nNum relevant:   {}".format(num_relevant))
    logger.info("\nNum relevant and retrieved:  {}".format(num_relevant_and_retrieved))

    # Compute metrics.
    precision = num_relevant_and_retrieved / num_retrieved if num_retrieved > 0 else 0
    recall = num_relevant_and_retrieved / num_relevant if num_relevant > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0
    time_per_storage = total_storage_time / num_memos_stored if num_memos_stored > 0 else 0
    time_per_retrieval = total_retrieval_time / num_retrieval_operations if num_retrieval_operations > 0 else 0
    retrieval_time_for_existing_plans = retrieval_time_for_existing_plans / (num_retrieval_operations/2) if num_retrieval_operations > 0 else 0
    retrieval_time_for_missing_plans = retrieval_time_for_missing_plans / (num_retrieval_operations/2) if num_retrieval_operations > 0 else 0

    precision_str = "Precision:  {:.3f}".format(precision)
    recall_str = "Recall:     {:.3f}".format(recall)
    f1_str = "F1:         {:.3f}".format(f1)
    time_per_storage_str = "Time per storage:  {:.3f} seconds".format(time_per_storage)
    time_per_retrieval_str = "Time per retrieval:  {:.3f} seconds".format(time_per_retrieval)

    logger.info("\n" + precision_str)
    logger.info("\n" + recall_str)
    logger.info("\n" + f1_str)
    logger.info("\n" + time_per_storage_str)
    logger.info("\n" + time_per_retrieval_str)
    logger.info("\nRetrieval time for existing plans:  {:.3f}".format(retrieval_time_for_existing_plans))
    logger.info("\nRetrieval time for missing plans:  {:.3f}".format(retrieval_time_for_missing_plans))
    logger.leave_function()

    multiline_str = ""
    multiline_str += "\npartition_index: {}".format(partition_index)
    multiline_str += "\npartition: {}".format(partition)
    multiline_str += "\nnum_relevant: {}".format(num_relevant)
    multiline_str += "\nnum_retrieved: {}".format(num_retrieved)
    multiline_str += "\nnum_relevant_and_retrieved: {}".format(num_relevant_and_retrieved)
    multiline_str += "\nprecision: {:.3f}".format(precision)
    multiline_str += "\nrecall: {:.3f}".format(recall)
    multiline_str += "\nf1: {:.3f}".format(f1)
    multiline_str += "\ntime_per_storage: {:.3f}".format(time_per_storage)
    multiline_str += "\ntime_per_retrieval: {:.3f}".format(time_per_retrieval)
    multiline_str += "\nretrieval_time_for_existing_plans: {:.3f}".format(retrieval_time_for_existing_plans)
    multiline_str += "\nretrieval_time_for_missing_plans: {:.3f}".format(retrieval_time_for_missing_plans)

    singleline_str = ""
    singleline_str += "{} ".format(partition_index)
    singleline_str += "{} ".format(partition)
    singleline_str += "{} ".format(num_relevant)
    singleline_str += "{} ".format(num_retrieved)
    singleline_str += "{} ".format(num_relevant_and_retrieved)
    singleline_str += "{:.3f} ".format(precision)
    singleline_str += "{:.3f} ".format(recall)
    singleline_str += "{:.3f} ".format(f1)
    singleline_str += "{:.3f} ".format(time_per_storage)
    singleline_str += "{:.3f} ".format(time_per_retrieval)
    singleline_str += "{:.3f} ".format(retrieval_time_for_existing_plans)
    singleline_str += "{:.3f} ".format(retrieval_time_for_missing_plans)

    # Append singleline_str to ./output.txt
    with open(output_filename, "a") as file:
        file.write(singleline_str + "\n")
    return multiline_str + "\n" + singleline_str
