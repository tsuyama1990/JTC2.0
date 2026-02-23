from src.domain_models.politics import InfluenceNetwork


class NemawashiView:
    """
    Renders the Nemawashi influence network.
    """

    @staticmethod
    def render_network(network: InfluenceNetwork) -> str:
        """
        Returns a text-based visualization of the network.
        """
        if not network.stakeholders:
            return "No stakeholders."

        output = ["Nemawashi Map:"]

        # Header
        names = [s.name for s in network.stakeholders]
        # max_name_len needs to be at least 10 or max name
        max_name_len = max([len(n) for n in names] + [10])

        # Column headers
        # Use first 3 chars of name for column to save space
        header_label = "From -> To"
        header = f"{header_label:<{max_name_len}} | " + " | ".join(f"{n[:3]:<4}" for n in names)
        output.append(header)
        output.append("-" * len(header))

        for i, s in enumerate(network.stakeholders):
            row = f"{s.name:<{max_name_len}} | "
            weights = network.matrix[i]
            row += " | ".join(f"{w:.2f}" for w in weights)
            output.append(row)

        return "\n".join(output)
