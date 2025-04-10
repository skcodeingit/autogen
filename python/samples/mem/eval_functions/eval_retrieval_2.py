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
    # task_files = run_dict["tasks"]
    # task_list = []
    # for task_file in task_files:
    #     with open(task_file, "r") as file:
    #         task = yaml.load(file, Loader=yaml.FullLoader)
    #         task_list.append(task["task_description"])
    #
    # insight_files = run_dict["insights"]
    # insight_list = []
    # for insight_file in insight_files:
    #     with open(insight_file, "r") as file:
    #         insight = yaml.load(file, Loader=yaml.FullLoader)
    #         insight_list.append(insight["insight"])
    #
    # task_insight_relevance = run_dict["task_insight_relevance"]

    task_pairs = run_dict["task_pairs"]  # List of tuples (task to store, task to retrieve)

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

    # Clear the counters.
    num_memos_stored = 0
    num_retrieval_operations = 0
    num_retrieved = 0
    num_relevant = 0
    num_relevant_and_retrieved = 0
    total_storage_time = 0.
    total_retrieval_time = 0.

    # Loop over each side of the partition, storing the corresponding half of the tasks in memory each time.
    for side_i in range(2):
        storage_flag = str(side_i)
        logger.info(f"Storing tasks with flag: {storage_flag}")

        # Clear memory, then store the tasks specified by the partition.
        memory_controller.reset_memory()
        start_storage_time = time.time()
        for ti, task_pair in enumerate(task_pairs):
            if partition[ti] == storage_flag:
                # Store the first task in the pair, using the pair index as the insight to be retrieved later.
                with open(task_pair[0], "r") as file:
                    task_to_store = yaml.load(file, Loader=yaml.FullLoader)["task_description"]
                await memory_controller.add_memo(task=task_to_store, insight=str(ti), index_on_both=False)
                num_memos_stored += 1
        total_storage_time += time.time() - start_storage_time

        # Test memory retrieval.
        start_retrieval_time = time.time()
        for ti, task_pair in enumerate(task_pairs):
            # Retrieve insights for the second task in the pair.
            query_task_file = task_pair[1]
            with open(query_task_file, "r") as file:
                query_task = yaml.load(file, Loader=yaml.FullLoader)["task_description"]
            memos = await memory_controller.retrieve_relevant_memos(task=query_task)
            assert len(memos) <= 1, "No more than one memo should be retrieved."
            num_retrieval_operations += 1
            # set_of_retrieved_insights = set(memo.insight for memo in memos)

            # Gather the insights that are relevant to this task according to ground truth.
            # set_of_relevant_insights: Set[str] = set()
            # for ii, insight in enumerate(insight_list):
            #     if task_insight_relevance[ti][ii] > 0:
            #         set_of_relevant_insights.add(insight)

            # Accumulate the counts.
            query_task_should_be_found = (partition[ti] == storage_flag)
            if query_task_should_be_found:
                num_relevant += 1
                logger.info(f"This query task should be found.")
            if len(memos) == 1:
                num_retrieved += 1
                memo = memos[0]
                if memo.insight == str(ti):
                    num_relevant_and_retrieved += 1
                    logger.info(f"This query task was found.")

            # num_retrieved += len(set_of_retrieved_insights)
            # num_relevant += len(set_of_relevant_insights)
            # num_relevant_and_retrieved += len(set_of_relevant_insights & set_of_retrieved_insights)
        total_retrieval_time += time.time() - start_retrieval_time

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

    logger.leave_function()
    multiline_str = "\neval_retrieval\n" + precision_str + "\n" + recall_str + "\n" + f1_str + "\n" + time_per_storage_str + "\n" + time_per_retrieval_str
    singleline_str = "{} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f}".format(partition_index, precision, recall, f1, time_per_storage, time_per_retrieval)

    # Append singleline_str to ./output.txt
    with open("output.txt", "a") as file:
        file.write(singleline_str + "\n")
    return multiline_str + "\n" + singleline_str
