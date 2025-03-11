app = modal.App("example-llama-cpp")


@app.local_entrypoint()
def main(
    prompt: str = None,
    model: str = "DeepSeek-R1",  # or "phi-4"
    n_predict: int = -1,  # max number of tokens to predict, -1 is infinite
    args: str = None,  # string of arguments to pass to llama.cpp's cli
    fast_download: bool = None,  # download model before starting inference function
):
    """Run llama.cpp inference on Modal for phi-4 or deepseek r1."""
    import shlex

    org_name = "unsloth"
    # two sample models: the diminuitive phi-4 and the chonky deepseek r1
    if model.lower() == "phi-4":
        model_name = "phi-4-GGUF"
        quant = "Q2_K"
        model_entrypoint_file = f"phi-4-{quant}.gguf"
        model_pattern = f"*{quant}*"
        revision = None
        if args is not None:
            args = shlex.split(args)
    elif model.lower() == "deepseek-r1":
        model_name = "DeepSeek-R1-GGUF"
        quant = "UD-IQ1_S"
        model_entrypoint_file = (
            f"{model}-{quant}/DeepSeek-R1-{quant}-00001-of-00003.gguf"
        )
        model_pattern = f"*{quant}*"
        revision = "02656f62d2aa9da4d3f0cdb34c341d30dd87c3b6"
        if args is None:
            args = DEFAULT_DEEPSEEK_R1_ARGS
        else:
            args = shlex.split(args)
    else:
        raise ValueError(f"Unknown model {model}")

    repo_id = f"{org_name}/{model_name}"
    if fast_download or model.lower() == "deepseek-r1":
        download_model.remote(repo_id, [model_pattern], revision)

    # call out to a `.remote` Function on Modal for inference
    result = llama_cpp_inference.remote(
        model_entrypoint_file,
        prompt,
        n_predict,
        args,
        store_output=model.lower() == "deepseek-r1",
    )
    output_path = Path("/tmp") / f"llama-cpp-{model}.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"🦙 writing response to {output_path}")
    output_path.write_text(result)

