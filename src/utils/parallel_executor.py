from concurrent.futures import ThreadPoolExecutor, as_completed


def run_agents_in_parallel(agent_map, text):
    """
    Executes multiple domain agents in parallel using ThreadPoolExecutor.
    """

    results = {}

    with ThreadPoolExecutor(max_workers=len(agent_map)) as executor:
        future_to_agent = {
            executor.submit(agent.analyze, text): name
            for name, agent in agent_map.items()
        }

        for future in as_completed(future_to_agent):
            agent_name = future_to_agent[future]
            results[agent_name] = future.result()

    return results
