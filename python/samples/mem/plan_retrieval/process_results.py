
import os

output_dir_str = "outputs"


class ConfigStats:
    def __init__(self, filename: str, run_result_list: list):
        """
        filename: Defines the configuration settings
        run_result_list: List of RunResult objects.
        """
        self.settings = filename.split(".")[0]
        self.run_result_list = run_result_list
        self.num_relevant = 0
        self.num_retrieved = 0
        self.num_relevant_and_retrieved = 0
        self.precision = 0.0
        self.recall = 0.0
        self.f1 = 0.0
        self.time_per_storage = 0.0
        self.time_per_retrieval = 0.0
        self.retrieval_time_for_existing_plans = 0.0
        self.retrieval_time_for_missing_plans = 0.0

    def compile_stats(self, num_results) -> str:
        for i in range(num_results):
            run_result = self.run_result_list[i]
            self.num_relevant += run_result.num_relevant
            self.num_retrieved += run_result.num_retrieved
            self.num_relevant_and_retrieved += run_result.num_relevant_and_retrieved
            self.time_per_storage += run_result.time_per_storage
            self.time_per_retrieval += run_result.time_per_retrieval
            self.retrieval_time_for_existing_plans += run_result.retrieval_time_for_existing_plans
            self.retrieval_time_for_missing_plans += run_result.retrieval_time_for_missing_plans
        self.precision = self.num_relevant_and_retrieved / self.num_retrieved if self.num_retrieved > 0 else 0
        self.recall = self.num_relevant_and_retrieved / self.num_relevant if self.num_relevant > 0 else 0
        self.f1 = (
            2 * self.precision * self.recall / (self.precision + self.recall)
            if (self.precision + self.recall) > 0
            else 0
        )
        self.time_per_storage /= num_results
        self.time_per_retrieval /= num_results
        self.retrieval_time_for_existing_plans /= num_results
        self.retrieval_time_for_missing_plans /= num_results

        output_str = self.settings + ' '
        output_str += "{} ".format(self.num_relevant)
        output_str += "{} ".format(self.num_retrieved)
        output_str += "{} ".format(self.num_relevant_and_retrieved)
        output_str += "{:.3f} ".format(self.precision)
        output_str += "{:.3f} ".format(self.recall)
        output_str += "{:.3f} ".format(self.f1)
        output_str += "{:.3f} ".format(self.time_per_storage)
        output_str += "{:.3f} ".format(self.time_per_retrieval)
        output_str += "{:.3f} ".format(self.retrieval_time_for_existing_plans)
        output_str += "{:.3f} ".format(self.retrieval_time_for_missing_plans)
        output_str += "\n"
        return output_str


class RunResult():
    def __init__(self, result_str: str):
        """
        Initialize the RunResult object with a result string, which is one line of an output file.

        :param result_str: The result string to be processed.
        """
        result_strs = result_str.split(" ")
        self.partition_index: int = int(result_strs[0])
        self.partition: str = result_strs[1]
        self.num_relevant: int = int(result_strs[2])
        self.num_retrieved: int = int(result_strs[3])
        self.num_relevant_and_retrieved: int = int(result_strs[4])
        self.precision: float = float(result_strs[5])
        self.recall: float = float(result_strs[6])
        self.f1: float = float(result_strs[7])
        self.time_per_storage: float = float(result_strs[8])
        self.time_per_retrieval: float = float(result_strs[9])
        self.retrieval_time_for_existing_plans: float = float(result_strs[10])
        self.retrieval_time_for_missing_plans: float = float(result_strs[11])


def process_output_files_in_directory():
    """
    Process all files in the given directory and print their contents.
    """
    # Get a list of all files in the directory
    file_names = os.listdir(output_dir_str)
    config_stat_list = []
    min_lines_per_file = 1000000

    # Process each file
    for filename in file_names:
        file_path = os.path.join(output_dir_str, filename)
        with open(file_path, 'r') as file:
            content = file.read()
            run_results = []

            # Pass each line to a new RunResult object.
            lines = content.splitlines()
            num_lines = len(lines)
            if num_lines < min_lines_per_file:
                min_lines_per_file = num_lines
            for line in lines:
                if len(line) > 0:
                    run_result = RunResult(line)
                    run_results.append(run_result)

            # Create a ConfigStats object for the current file.
            config_stats = ConfigStats(filename, run_results)
            config_stat_list.append(config_stats)

    # Sort the config_stat_list by their settings strings.
    config_stat_list.sort(key=lambda x: x.settings)

    # Produce an output file summarizing the stats.
    with open("output_summary.txt", "w") as output_file:
        # Compile all the stats, considering the same number of lines from each file.
        for config_stat in config_stat_list:
            line = config_stat.compile_stats(min_lines_per_file)
            output_file.write(line)


if __name__ == "__main__":
    process_output_files_in_directory()
