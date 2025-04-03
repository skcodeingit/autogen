from typing import Any, Dict, Set
import yaml
import time

from autogen_core.models import (
    ChatCompletionClient,
)
from autogen_ext.experimental.task_centric_memory import MemoryController
from autogen_ext.experimental.task_centric_memory.utils import Apprentice, Grader, PageLogger


async def eval_retrieval(memory_controller: MemoryController, client: ChatCompletionClient,
                         logger: PageLogger, config: Dict[str, Any], run_dict: Dict[str, Any]) -> str:
    """
    Evaluates precision and recall of task-centric memory retrieval.
    """
    logger.enter_function()
    start_time = time.time()

    # Load the specified data.
    task_files = run_dict["tasks"]
    task_list = []
    for task_file in task_files:
        with open(task_file, "r") as file:
            task = yaml.load(file, Loader=yaml.FullLoader)
            task_list.append(task["task_description"])

    insight_files = run_dict["insights"]
    insight_list = []
    for insight_file in insight_files:
        with open(insight_file, "r") as file:
            insight = yaml.load(file, Loader=yaml.FullLoader)
            insight_list.append(insight["insight"])

    task_insight_relevance = run_dict["task_insight_relevance"]

    # Clear memory, then store the specified task-insight pairs.
    memory_controller.reset_memory()
    for ti, task in enumerate(task_list):
        for ii, insight in enumerate(insight_list):
            if task_insight_relevance[ti][ii] == 2:
                await memory_controller.add_memo(task=task, insight=insight)

    # Test memory retrieval.
    num_retrieved = 0
    num_relevant = 0
    num_relevant_and_retrieved = 0
    for ti, task in enumerate(task_list):
        # Retrieve insights for this task.
        memos = await memory_controller.retrieve_relevant_memos(task=task)
        set_of_retrieved_insights = set(memo.insight for memo in memos)

        # Gather the insights that are relevant to this task according to ground truth.
        set_of_relevant_insights: Set[str] = set()
        for ii, insight in enumerate(insight_list):
            if task_insight_relevance[ti][ii] > 0:
                set_of_relevant_insights.add(insight)

        # Accumulate the counts.
        num_retrieved += len(set_of_retrieved_insights)
        num_relevant += len(set_of_relevant_insights)
        num_relevant_and_retrieved += len(set_of_relevant_insights & set_of_retrieved_insights)
    logger.info("\nNum retrieved:  {}".format(num_retrieved))
    logger.info("\nNum relevant:   {}".format(num_relevant))
    logger.info("\nNum relevant and retrieved:  {}".format(num_relevant_and_retrieved))

    # Compute metrics.
    precision = num_relevant_and_retrieved / num_retrieved if num_retrieved > 0 else 0
    recall = num_relevant_and_retrieved / num_relevant if num_relevant > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0
    end_time = time.time()
    time_spent = end_time - start_time

    precision_str = "Precision:  {:.3f}%".format(precision * 100)
    recall_str = "Recall:     {:.3f}%".format(recall * 100)
    f1_str = "F1:         {:.3f}%".format(f1 * 100)
    time_str = "Time:       {:.3f} seconds".format(time_spent)

    logger.info("\n" + precision_str)
    logger.info("\n" + recall_str)
    logger.info("\n" + f1_str)
    logger.info("\n" + time_str)


    logger.leave_function()
    multiline_str = "\neval_retrieval\n" + precision_str + "\n" + recall_str + "\n" + f1_str + "\n" + time_str
    singleline_str = "{:.3f} {:.3f} {:.3f} {:.3f}".format(precision, recall, f1, time_spent)
    return multiline_str + "\n" + singleline_str
