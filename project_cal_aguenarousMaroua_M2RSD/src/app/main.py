import os
import sys

if __package__ is None or __package__ == "":
  
    src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


if __package__ is None or __package__ == "":
    from app.affichage import Affichage
    from app.traitement import Traitement
else:
    from .affichage import Affichage
    from .traitement import Traitement


class Main:
    def __init__(self) -> None:
        self.traitement = Traitement()
        self.affichage = Affichage()

    def executer(self) -> None:
        self._afficher_entete()
        resultats = {}

        try:
            for strat in ["FIFO", "RR", "Aleatoire", "Intelligent"]:
                print(f"\nExecution {strat}...")
                metrics = self.traitement.simuler(strat)
                resultats[strat] = metrics
                self._afficher_resultat_console(strat, metrics)
                print(f"{strat} termine avec succes")

            self._afficher_conclusion()
            print("\nGeneration des graphiques...")
            self.affichage.tracer_comparaison(resultats)
            print("Graphiques affiches")
        except Exception as e:
            print(f"ERREUR : {e}")
            import traceback
            traceback.print_exc()

    def _afficher_entete(self) -> None:
        print("=" * 60)
        print("COMPARAISON DES PLANIFICATEURS")
        print("=" * 60)

    def _afficher_resultat_console(self, strategie: str, metrics: dict) -> None:
        print(f"\n--- {strategie} ---")
        print(f"Latence moyenne : {metrics['latence_moy']:.3f}s")
        print(f"Respect delai  : {metrics['respect']:.1f}%")
        print(f"Energie        : {metrics['energie']:.2f}")
        print(f"Equilibrage    : {metrics['equilibrage']:.1f}%")

        if strategie == "Intelligent":
            print("\nDetails d'assignation Intelligent :")
            print(f"Total taches: {len(metrics['taches'])}")
            for tache in sorted(metrics["taches"], key=lambda x: x.arrivee):
                status = "OK" if tache.delai_ok else "Non"
                print(
                    f"  {tache.nom:8} -> {tache.noeud:6} | Debut:{tache.debut:5.2f} "
                    f"Fin:{tache.fin:5.2f} | Delai:{tache.delai:4.1f} {status}"
                )
            manquantes = [t for t in metrics["taches"] if t.noeud is None]
            if manquantes:
                print("ATTENTION: taches sans noeud -> " + ", ".join(t.nom for t in manquantes))

    def _afficher_conclusion(self) -> None:
        print("\n" + "=" * 60)
        print("ANALYSE : Le planificateur Intelligent devrait avoir un")
        print("meilleur taux de respect des delais grace a la priorite dynamique")
        print("=" * 60)


if __name__ == "__main__":
    Main().executer()
