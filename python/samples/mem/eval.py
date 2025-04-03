import asyncio
import importlib.util
import sys
import yaml

from autogen_ext.experimental.task_centric_memory.utils import PageLogger, Apprentice
from autogen_ext.experimental.task_centric_memory import MemoryController
from clients._client_creator import ClientCreator


async def perform_evaluations(config, logger) -> None:
    """
    Perform the evaluations as specified in the config file.
    """
    logger.enter_function()

    # Create the client.
    client_creator = ClientCreator(config=config["client"], logger=logger)
    client = client_creator.create_client()

    # Does config contain an Apprentice section?
    if "Apprentice" in config:
        # Create the apprentice.
        apprentice_config = config["Apprentice"]
        apprentice = Apprentice(
            client=client,
            config=apprentice_config,
            logger=logger)
    else:
        apprentice = None

    # Does config contain a MemoryController section?
    if "MemoryController" in config:
        # Create the memory controller.
        memory_controller_config = config["MemoryController"]
        memory_controller = MemoryController(
            reset=True,
            config=memory_controller_config,
            task_assignment_callback=None,
            client=client,
            logger=logger)
    else:
        memory_controller = None

    # Make sure we have one or the other, but not both.
    if apprentice is not None and memory_controller is not None:
        raise ValueError("Cannot have both Apprentice and MemoryController in the config.")
    if apprentice is None and memory_controller is None:
        raise ValueError("Must have either Apprentice or MemoryController in the config.")

    # Execute each evaluation.
    for evaluation_config in config["evaluations"]:
        # Import the function.
        function_config = evaluation_config["eval_function"]
        module_path = function_config["module_path"]
        try:
            # Create a module spec from the file location
            spec = importlib.util.spec_from_file_location(module_path, module_path)
            if spec is None:
                raise ImportError(f"Can't find module at {module_path}")
            # Create a module based on the spec and execute it
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except ModuleNotFoundError:
            print("Failed to import {}".format(module_path))
            raise
        function_name = function_config["function_name"]
        try:
            eval_function = getattr(module, function_name)
        except AttributeError:
            print("Failed to import {}.{}".format(module_path, function_name))
            raise

        # Call the eval function for each listed run.
        for run_dict in evaluation_config["runs"]:
            if apprentice is not None:
                results = await eval_function(apprentice, client, logger, function_config, run_dict)
            else:
                results = await eval_function(memory_controller, client, logger, function_config, run_dict)
            print(results)

    if hasattr(client, "finalize"):
        # If this is a client wrapper, it needs to be finalized.
        client.finalize()

    logger.leave_function()


async def run(config_filepath):
    # Load the config from yaml.
    with open(config_filepath, "r") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
        logger = PageLogger(config["PageLogger"])

        # Perform the evaluations.
        await perform_evaluations(config, logger)


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 1:
        print("Usage:  amt.py <path to *.yaml file>")
    else:
        asyncio.run(run(config_filepath=args[0]))
