import json, yaml

filename = "9r"
input_filename = filename + ".json"
output_filename = filename + ".yaml"

# Load the input file as a string
with open(input_filename, "r") as json_file:
    json_data = json_file.read()

    # Convert the JSON string to a Python dictionary
    data_dict = json.loads(json_data)

    # Remove the following keys from the dictionary:  response, plan_summary, needs_plan
    keys_to_remove = ["response", "plan_summary", "needs_plan"]
    for key in keys_to_remove:
        if key in data_dict:
            del data_dict[key]

    # The 'steps' key contains a list of dicts. Remove the 'agent_name' key from each dict in the list.
    if "steps" in data_dict:
        for step in data_dict["steps"]:
            if "agent_name" in step:
                del step["agent_name"]

    # Null out the task key.
    if "task" in data_dict:
        data_dict["task"] = None

    # Convert the modified dict back to a JSON string, containing no newlines.
    json_data = json.dumps(data_dict, indent=None)

    # Wrap this string in a dict.
    yaml_data = {"insight": json_data}

    # Convert the dict to a YAML string
    yaml_string = yaml.dump(yaml_data, default_flow_style=False)

    # Write the YAML string to the output file
    with open(output_filename, "w") as yaml_file:
        yaml_file.write(yaml_string)
