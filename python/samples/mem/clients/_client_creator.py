import os
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient, OpenAIChatCompletionClient
from azure.identity import AzureCliCredential, ChainedTokenCredential, DefaultAzureCredential, get_bearer_token_provider


class ClientCreator:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def create_client(self):
        self.logger.enter_function()

        # A few args are shared by all clients.
        args = {}
        args["model"] = self.config["model"]

        # The following args don't apply to the 'o1' family of models.
        if args["model"].startswith("o"):
            # Reasoning model.
            # args["reasoning"] = self.config["reasoning"]
            args["reasoning_effort"] = self.config["reasoning_effort"]
        else:
            # Not a reasoning model.
            args["max_completion_tokens"] = self.config["max_completion_tokens"]
            args["max_retries"] = self.config["max_retries"]
            args["temperature"] = self.config["temperature"]
            args["presence_penalty"] = self.config["presence_penalty"]
            args["frequency_penalty"] = self.config["frequency_penalty"]
            args["top_p"] = self.config["top_p"]

        client = None
        provider = self.config["provider"]
        if provider == "openai":
            client, source = self.create_oai_client(args)
        elif provider == "azure_openai":
            client, source = self.create_aoai_client(args)
        elif provider == "trapi":
            client, source = self.create_trapi_client(args)
        elif provider == "phi":
            client, source = self.create_phi_client(args)
        else:
            assert False, "Invalid client provider"

        # Log some details.
        self.logger.info("Client:  {}".format(client._resolved_model))
        self.logger.info(source)

        # Convert the args dict to an indented string for logging.
        args_str = "\n".join(
            ["    {}: {}".format(k, v) for k, v in args.items() if k != "api_key"]
        )
        self.logger.info("  Client args:\n{}".format(args_str))

        # Check if the client should be wrapped.
        if "ChatCompletionClientRecorder" in self.config:
            wrapper_config = self.config["ChatCompletionClientRecorder"]
            if wrapper_config["enabled"]:
                # Wrap the client.
                # client = ClientWrapper(client, wrapper_config["mode"], wrapper_config["session_name"], self.logger)

                from autogen_ext.experimental.task_centric_memory.utils import ChatCompletionClientRecorder
                client = ChatCompletionClientRecorder(
                    client, wrapper_config["mode"], wrapper_config["session_name"], self.logger
                )

        # Check if the client should be wrapped.
        if "ClientRecorder" in self.config:
            wrapper_config = self.config["ClientRecorder"]
            from autogen_ext.experimental.task_centric_memory.utils import ChatCompletionClientRecorder
            client = ChatCompletionClientRecorder(client, wrapper_config["mode"], wrapper_config["session_filename"], self.logger)

        self.logger.leave_function()
        return client

    def create_oai_client(self, args):
        # Create an OpenAI client
        if "api_key" in self.config:
            args["api_key"] = self.config["api_key"]
        client = OpenAIChatCompletionClient(**args)
        return client, "  created through OpenAI"

    def create_aoai_client(self, args):
        # Create an Azure OpenAI client
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
        )
        model = self.config["model"]
        if model == "gpt-4o-2024-11-20":
            azure_deployment = "gpt-4o"
            azure_endpoint = "https://agentic1.openai.azure.com/"  # Also on agentic2
        # elif model == "o1-preview":
        #     azure_deployment = "o1-preview-2024-09-12-eval"
        #     azure_endpoint = "https://agentic2.openai.azure.com/"
        else:
            assert False, "Unsupported model"
        api_version = "2024-12-01-preview"  # From https://learn.microsoft.com/en-us/azure/ai-services/openai/api-version-deprecation#latest-ga-api-release
        args["azure_ad_token_provider"] = token_provider
        args["azure_deployment"] = azure_deployment
        args["azure_endpoint"] = azure_endpoint
        args["api_version"] = api_version
        client = AzureOpenAIChatCompletionClient(**args)
        return client, "  created through Azure OpenAI"

    def create_trapi_client(self, args):
        # Create an Azure OpenAI client through TRAPI
        token_provider = get_bearer_token_provider(
            ChainedTokenCredential(
                AzureCliCredential(),
                DefaultAzureCredential(
                    exclude_cli_credential=True,
                    # Exclude other credentials we are not interested in.
                    exclude_environment_credential=True,
                    exclude_shared_token_cache_credential=True,
                    exclude_developer_cli_credential=True,
                    exclude_powershell_credential=True,
                    exclude_interactive_browser_credential=True,
                    exclude_visual_studio_code_credentials=True,
                    # managed_identity_client_id=os.environ.get("DEFAULT_IDENTITY_CLIENT_ID"),  # See the TRAPI docs
                ),
            ),
            "api://trapi/.default",
        )
        model = self.config["model"]
        if model == "gpt-4o-2024-08-06":
            azure_deployment = "gpt-4o_2024-08-06"  # This is DeploymentName in the table at https://aka.ms/trapi/models
        elif model == "gpt-4o-2024-05-13":
            azure_deployment = "gpt-4o_2024-05-13"
        elif model == "gpt-4o-2024-11-20":
            azure_deployment = "gpt-4o_2024-11-20"
        elif model == "gpt-4.1-2025-04-14":
            azure_deployment = "gpt-4.1_2025-04-14"
        elif model == "o1-preview":
            azure_deployment = "o1-preview_2024-09-12"
        elif model == "o1":
            azure_deployment = "o1_2024-12-17"
        elif model == "o3-mini":
            azure_deployment = "o3-mini_2025-01-31"
            model_version = "2025-01-31"
        elif model == "o4-mini":
            azure_deployment = "o4-mini_2025-04-16"
            model_version = "2025-04-16"
        elif model == "o4-mini-2025-04-16":
            azure_deployment = "o4-mini_2025-04-16"
            model_version = "2025-04-16"
        else:
            assert False, "Unsupported model"
        trapi_suffix = (
            "msraif/shared"  # This is TRAPISuffix (without /openai) in the table at https://aka.ms/trapi/models
        )
        endpoint = f"https://trapi.research.microsoft.com/{trapi_suffix}"
        api_version = "2025-03-01-preview"  # From https://learn.microsoft.com/en-us/azure/ai-services/openai/api-version-deprecation#latest-ga-api-release
        args["azure_ad_token_provider"] = token_provider
        args["azure_deployment"] = azure_deployment
        if model == "o3-mini":
            args["model_version"] = model_version
        args["azure_endpoint"] = endpoint
        args["api_version"] = api_version
        client = AzureOpenAIChatCompletionClient(**args)
        return client, "  created through TRAPI"

    def create_phi_client(self, args):
        args["api_key"] = os.getenv("PHYAGI_API_KEY")
        args["base_url"] = "https://gateway.phyagi.net/api"
        args["model_info"] = {
            "vision": False,
            "function_calling": False,
            "json_output": False,
            "family": "phi",
            "structured_output": False,
            "multiple_system_messages": False,
        }
        client = OpenAIChatCompletionClient(**args)
        return client, "  created through Azure OpenAI"
