
with open("src/agents/builder.py") as f:
    content = f.read()

diff = """<<<<<<< SEARCH
        context_str = f"Core Story: {state.sitemap_and_story.core_story.model_dump()}\n"
        if state.value_proposition:
            context_str += f"Value Proposition: {state.value_proposition.model_dump()}\n"
        if state.mental_model:
            context_str += f"Mental Model: {state.mental_model.model_dump()}\n"
        if state.customer_journey:
            context_str += f"Customer Journey: {state.customer_journey.model_dump()}\n"
        if state.sitemap_and_story:
            context_str += f"Sitemap: {state.sitemap_and_story.model_dump()}\n"
        if state.debate_history:
            context_str += (
                f"3H Review History: {[msg.model_dump() for msg in state.debate_history]}\n"
            )
=======
        context_str = f"Core Story: {state.sitemap_and_story.core_story.model_dump_json()}\n"
        if state.value_proposition:
            context_str += f"Value Proposition: {state.value_proposition.model_dump_json()}\n"
        if state.mental_model:
            context_str += f"Mental Model: {state.mental_model.model_dump_json()}\n"
        if state.customer_journey:
            context_str += f"Customer Journey: {state.customer_journey.model_dump_json()}\n"
        if state.sitemap_and_story:
            context_str += f"Sitemap: {state.sitemap_and_story.model_dump_json()}\n"
        if state.debate_history:
            import json
            context_str += (
                f"3H Review History: {json.dumps([msg.model_dump() for msg in state.debate_history])}\n"
            )
>>>>>>> REPLACE"""

with open("patch_builder.patch", "w") as f:
    f.write(diff)
