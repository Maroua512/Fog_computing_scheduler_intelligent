from typing import Dict

import matplotlib.pyplot as plt


class Affichage:
    def tracer_comparaison(self, resultats: Dict[str, Dict[str, object]]) -> None:
        strategies = list(resultats.keys())
        latences = [resultats[s]["latence_moy"] for s in strategies]
        respects = [resultats[s]["respect"] for s in strategies]
        energies = [resultats[s]["energie"] for s in strategies]
        equilibrages = [resultats[s]["equilibrage"] for s in strategies]

        fig, axes = plt.subplots(2, 2, figsize=(11, 8))

        axes[0, 0].bar(strategies, latences, color="#4c78a8")
        axes[0, 0].set_title("Latence moyenne (s)")
        axes[0, 0].set_ylabel("Secondes")

        axes[0, 1].bar(strategies, respects, color="#f58518")
        axes[0, 1].set_title("Respect delai (%)")
        axes[0, 1].set_ylabel("Pourcentage")

        axes[1, 0].bar(strategies, energies, color="#54a24b")
        axes[1, 0].set_title("Energie totale")
        axes[1, 0].set_ylabel("Unites arbitraires")

        axes[1, 1].bar(strategies, equilibrages, color="#e45756")
        axes[1, 1].set_title("Equilibrage (%)")
        axes[1, 1].set_ylabel("Pourcentage")

        for ax in axes.flat:
            ax.set_xlabel("Strategie")
            ax.grid(axis="y", linestyle="--", alpha=0.4)

        fig.tight_layout()
        
        # Sauvegarder le graphique au lieu de bloquer avec plt.show()
        import os
        output_path = os.path.join(os.path.dirname(__file__), "comparaison_planificateurs.png")
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Graphique sauvegarde : {output_path}")
        
        # Optionnel : afficher si mode interactif
        try:
            plt.show()
        except:
            pass  # En cas d'erreur, le graphique est deja sauvegarde
