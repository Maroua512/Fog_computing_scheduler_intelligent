import math
import os
import random
import sys
from typing import Dict, List, Tuple

if __package__ is None or __package__ == "":
    
    src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


if __package__ is None or __package__ == "":
    from app.models.noeud import Noeud
    from app.models.tache import Tache
else:
    from .models.noeud import Noeud
    from .models.tache import Tache


class Traitement:
    LATENCE_FOG = 0.005
    LATENCE_CLOUD = 0.8

    # Poids pour la priorité dynamique
    ALPHA = 0.1   # Poids temps d'attente
    BETA = 0.6    # Poids urgence
    GAMMA = 0.3   # Poids criticité

    def __init__(self) -> None:
        # Scénario conçu pour mettre en évidence le scheduler intelligent
        self.fogs_template = [
            Noeud("Fog1", 4),
            Noeud("Fog2", 3),
            Noeud("Fog3", 2),
            Noeud("Fog4", 2),
            Noeud("Fog5", 1),
            Noeud("Fog6", 1),
        ]
        self.cloud_template = Noeud("Cloud", 100, "Cloud")
        self.taches_template = [
            # Phase 1 : Tâches non critiques lourdes (piège pour Aléatoire)
            Tache("1", 4, 0.1, 0.00, 20.0),
            Tache("2", 4, 0.1, 0.01, 20.0),
            # Phase 2 : Avalanche de tâches critiques avec délais TRÈS serrés
            Tache("3", 2, 0.95, 0.05, 1.0),   # Délai 1.0s - très urgent
            Tache("4", 1, 0.98, 0.08, 0.8),   # Délai 0.8s - extrêmement urgent
            Tache("5", 2, 0.95, 0.10, 1.2),
            Tache("6", 1, 0.90, 0.12, 1.0),
            Tache("7", 2, 0.95, 0.15, 1.3),
            Tache("8", 1, 0.98, 0.18, 0.9),   # Délai 0.9s - critique
            # Phase 3 : Mix avec tâches moyennes
            Tache("9", 4, 0.5, 0.20, 5.0),
            Tache("10", 2, 0.92, 0.22, 1.1),
            Tache("11", 1, 0.95, 0.25, 1.0),
            Tache("12", 3, 0.2, 0.28, 15.0),
            Tache("13", 2, 0.90, 0.30, 1.2),
            # Phase 4 : Dernière vague critique
            Tache("14", 1, 0.98, 0.35, 0.8),  # Très urgent
            Tache("15", 2, 0.1, 0.40, 18.0),
        ]

    def simuler(self, strategie: str) -> Dict[str, object]:
        fogs, cloud = self._copier_noeuds()
        taches = self._copier_taches()

        if strategie == "Intelligent":
            self._simuler_intelligent(taches, fogs, cloud)
        else:
            self._simuler_classique(strategie, taches, fogs)

        lat_moy = sum(t.latence for t in taches) / len(taches)
        respect = sum(t.delai_ok for t in taches) / len(taches) * 100
        energie = sum(f.energie for f in fogs) + cloud.energie

        loads = [f.temps_libre for f in fogs]
        mean = sum(loads) / len(loads)
        variance = sum((l - mean) ** 2 for l in loads) / len(loads)
        equilibrage = max(0.0, 100 - math.sqrt(variance) * 25)

        return {
            "latence_moy": lat_moy,
            "respect": respect,
            "energie": energie,
            "equilibrage": equilibrage,
            "taches": taches,
        }

    # -----------------------------
    # Simulation interne
    # -----------------------------
    def _simuler_intelligent(self, taches: List[Tache], fogs: List[Noeud], cloud: Noeud) -> None:
        temps_actuel = 0.0
        file_attente: List[Tache] = []
        taches_triees = sorted(taches, key=lambda x: x.arrivee)
        index_tache = 0

        while index_tache < len(taches_triees) or file_attente:
            while index_tache < len(taches_triees) and taches_triees[index_tache].arrivee <= temps_actuel:
                file_attente.append(taches_triees[index_tache])
                index_tache += 1

            if not file_attente:
                if index_tache < len(taches_triees):
                    temps_actuel = taches_triees[index_tache].arrivee
                continue

            file_attente.sort(key=lambda t: -self._priorite_dynamique(t, temps_actuel))
            tache = file_attente.pop(0)

            # Libérer les ressources terminées avant de décider
            for noeud in fogs:
                self._liberer_ressources_terminees(noeud, temps_actuel)

            # Pour tâches urgentes: considérer TOUS les fogs (capacité totale)
            # Pour non-urgentes: seulement ceux avec CPU disponible maintenant
            est_urgente = tache.criticite >= 0.8 or (tache.delai is not None and tache.delai < 2.0)
            
            # Politique proactive Cloud: tâches non-critiques avec long délai vont au Cloud
            # pour libérer les Fogs pour les futures tâches critiques
            if tache.criticite < 0.5 and (tache.delai is None or tache.delai >= 10.0):
                noeud = cloud
            else:
                # Tâches critiques ou moyennes : utiliser les Fogs
               
                candidats = [f for f in fogs if f.get_cpu_disponible(temps_actuel) >= tache.cpu]

                if not candidats:
                    # Saturation complète: attendre la prochaine libération
                    prochain_fog = min((f.temps_libre for f in fogs), default=None)
                    prochain_arrivee = (
                        taches_triees[index_tache].arrivee
                        if index_tache < len(taches_triees)
                        else None
                    )

                    if prochain_fog is not None and prochain_arrivee is not None:
                        prochain_temps = min(prochain_fog, prochain_arrivee)
                    elif prochain_fog is not None:
                        prochain_temps = prochain_fog
                    else:
                        prochain_temps = prochain_arrivee

                    # Sécurité: s'assurer que le temps avance
                    if prochain_temps is None or prochain_temps <= temps_actuel:
                        prochain_temps = temps_actuel + 0.001

                    temps_actuel = prochain_temps
                    file_attente.insert(0, tache)
                    continue
                
                else:
                    noeud = self._choisir_noeud_intelligent(tache, candidats, cloud, temps_actuel)

            # Exécution simultanée : début dès que CPU disponible
            tache.debut = max(tache.arrivee, noeud.get_temps_debut(temps_actuel))
            vitesse = noeud.cpu_total if noeud.type == "Fog" else 100
            exec_time = tache.cpu / vitesse
            tache.fin = tache.debut + exec_time

            tache.attente = tache.debut - tache.arrivee
            lat_net = self.LATENCE_FOG if noeud.type == "Fog" else self.LATENCE_CLOUD
            tache.latence = tache.attente + lat_net
            tache.delai_ok = (tache.fin - tache.arrivee) <= tache.delai
            tache.noeud = noeud.nom

            # Ajout à la liste des tâches en cours pour exécution parallèle
            noeud.taches_en_cours.append((tache.fin, tache.cpu))
            noeud.temps_libre = max(noeud.temps_libre, tache.fin)
            noeud.energie += tache.cpu * exec_time

            temps_actuel = max(temps_actuel, tache.debut)

    def _simuler_classique(self, strategie: str, taches: List[Tache], fogs: List[Noeud]) -> None:
        temps_actuel = 0.0
        file_attente: List[Tache] = []
        taches_triees = sorted(taches, key=lambda x: x.arrivee)
        index_tache = 0
        compteur_rr = 0

        def _choisir_tache() -> Tuple[Tache, int | None]:
            nonlocal compteur_rr
            if strategie == "FIFO":
                return file_attente[0], 0
            if strategie == "RR":
                idx = compteur_rr % len(file_attente)
                return file_attente[idx], idx
            # Aléatoire
            tache_alea = random.choice(file_attente)
            return tache_alea, None

        def _obtenir_candidats_et_disponibles(tache: Tache) -> Tuple[List[Noeud], List[Noeud]]:
            # Fogs disponibles maintenant selon CPU disponible
            candidats = [f for f in fogs if f.get_cpu_disponible(temps_actuel) >= tache.cpu]
            disponibles = candidats
            return candidats, disponibles

        def _choisir_noeud(disponibles: List[Noeud]) -> Noeud:
            nonlocal compteur_rr
            if strategie == "RR":
                return disponibles[compteur_rr % len(disponibles)]
            if strategie == "Aleatoire":
                return random.choice(disponibles)
            return disponibles[0]

        def _retirer_tache(tache: Tache, index: int | None) -> None:
            nonlocal compteur_rr
            if strategie == "FIFO":
                file_attente.pop(0)
            elif strategie == "RR":
                file_attente.pop(index if index is not None else 0)
                compteur_rr += 1
            else:
                file_attente.remove(tache)

        while index_tache < len(taches_triees) or file_attente:
            index_tache = self._remplir_file_attente(file_attente, taches_triees, index_tache, temps_actuel)

            continuer, temps_actuel = self._avancer_temps_si_file_vide(
                file_attente, taches_triees, index_tache, temps_actuel
            )
            if continuer:
                continue

            tache, tache_index = _choisir_tache()

            # Libérer les ressources AVANT de vérifier la disponibilité
            for noeud in fogs:
                self._liberer_ressources_terminees(noeud, temps_actuel)

            candidats, disponibles = _obtenir_candidats_et_disponibles(tache)
            if not disponibles:
                nouveau_temps = self._calculer_prochain_temps(candidats, taches_triees, index_tache)
                if nouveau_temps is not None and nouveau_temps > temps_actuel:
                    temps_actuel = nouveau_temps
                else:
                    # Sécurité: avancer le temps d'un petit pas pour éviter une boucle infinie
                    temps_actuel += 0.001
                continue

            noeud = _choisir_noeud(disponibles)
            self._executer_tache(tache, noeud, temps_actuel)

            _retirer_tache(tache, tache_index)
            temps_actuel = max(temps_actuel, tache.debut)

    # -----------------------------
    # Fonctions auxiliaires pour simulateurs
    # -----------------------------
    def _remplir_file_attente(self, file_attente: List[Tache], taches_triees: List[Tache], 
                               index_tache: int, temps_actuel: float) -> int:
        """Ajoute à la file d'attente toutes les tâches arrivées jusqu'à temps_actuel"""
        while index_tache < len(taches_triees) and taches_triees[index_tache].arrivee <= temps_actuel:
            file_attente.append(taches_triees[index_tache])
            index_tache += 1
        return index_tache

    def _avancer_temps_si_file_vide(self, file_attente: List[Tache], taches_triees: List[Tache],
                                      index_tache: int, temps_actuel: float) -> tuple[bool, float]:
        """Avance le temps si la file est vide. Retourne (continuer, nouveau_temps)"""
        if not file_attente:
            if index_tache < len(taches_triees):
                return True, taches_triees[index_tache].arrivee
        return False, temps_actuel

    def _calculer_prochain_temps(self, candidats: List[Noeud], taches_triees: List[Tache], 
                                  index_tache: int) -> float:
        """Calcule le prochain moment où un événement se produira"""
        prochains_fogs = [f.temps_libre for f in candidats]
        prochain_fog = min(prochains_fogs) if prochains_fogs else None
        prochain_arrivee = (
            taches_triees[index_tache].arrivee
            if index_tache < len(taches_triees)
            else None
        )

        if prochain_fog is not None and prochain_arrivee is not None:
            return min(prochain_fog, prochain_arrivee)
        elif prochain_fog is not None:
            return prochain_fog
        elif prochain_arrivee is not None:
            return prochain_arrivee
        return None

    def _executer_tache(self, tache: Tache, noeud: Noeud, temps_actuel: float = 0.0) -> None:
        """Exécute une tâche sur un nœud (support exécution parallèle)"""
        # Vérifier si le nœud a assez de CPU disponible maintenant
        cpu_dispo = noeud.get_cpu_disponible(temps_actuel)
        
        if cpu_dispo >= tache.cpu:
            # CPU disponible : exécution immédiate (parallèle si d'autres tâches en cours)
            tache.debut = max(tache.arrivee, temps_actuel)
        else:
            # Pas assez de CPU : attendre la fin d'une tâche
            if noeud.taches_en_cours:
                temps_fin_max = max(fin for fin, _ in noeud.taches_en_cours)
            else:
                temps_fin_max = noeud.temps_libre
            tache.debut = max(tache.arrivee, temps_fin_max, temps_actuel)
        
        vitesse = noeud.cpu_total if noeud.type == "Fog" else 100
        exec_time = tache.cpu / vitesse
        tache.fin = tache.debut + exec_time

        tache.attente = tache.debut - tache.arrivee
        lat_net = self.LATENCE_FOG if noeud.type == "Fog" else self.LATENCE_CLOUD
        tache.latence = tache.attente + lat_net
        tache.delai_ok = (tache.fin - tache.arrivee) <= tache.delai
        tache.noeud = noeud.nom

        # Ajout à la liste des tâches en cours pour exécution parallèle
        noeud.taches_en_cours.append((tache.fin, tache.cpu))
        noeud.temps_libre = max(noeud.temps_libre, tache.fin)
        noeud.energie += tache.cpu * exec_time

    def _obtenir_noeuds_disponibles(self, fogs: List[Noeud], tache: Tache, temps_actuel: float) -> List[Noeud]:
        """Retourne la liste des nœuds disponibles pour une tâche"""
        # Libérer les ressources des tâches terminées avant de vérifier la disponibilité
        for noeud in fogs:
            self._liberer_ressources_terminees(noeud, temps_actuel)
        
        # Un nœud est disponible s'il a assez de CPU libre ou sera libre bientôt
        disponibles = []
        for f in fogs:
            if f.cpu_total >= tache.cpu:
                cpu_dispo = f.get_cpu_disponible(temps_actuel)
                if cpu_dispo >= tache.cpu:
                    disponibles.append(f)
        
        return disponibles

    def _liberer_ressources_terminees(self, noeud: Noeud, temps_actuel: float) -> None:
        """Libère les ressources des tâches terminées jusqu'à temps_actuel"""
        # Nettoyer les tâches en cours qui sont terminées
        noeud.taches_en_cours = [
            (fin, cpu) for fin, cpu in noeud.taches_en_cours 
            if fin > temps_actuel
        ]

    # -----------------------------
    # Aide à la décision
    # -----------------------------
    def _choisir_noeud_intelligent(self, tache: Tache, candidats: List[Noeud], cloud: Noeud, temps_actuel: float = 0.0) -> Noeud:
      
        # Déterminer si la tâche est urgente (très critique OU délai court)
        est_urgente = tache.criticite >= 0.8 or (tache.delai is not None and tache.delai < 2.0)
        
        if est_urgente:
            # Pour urgent : minimiser (temps_fin + pénalité_charge)
            # Cela balance entre rapidité et équilibrage
            def score_noeud(fog: Noeud) -> float:
                cpu_dispo_maintenant = fog.get_cpu_disponible(temps_actuel)
                
                if cpu_dispo_maintenant >= tache.cpu:
                    # CPU disponible maintenant : exécution immédiate
                    debut = temps_actuel
                else:
                    # CPU insuffisant : attendre la libération
                    debut = max((fin for fin, _ in fog.taches_en_cours), default=temps_actuel)
                
                # Calcul du temps d'exécution
                vitesse = fog.cpu_total
                exec_time = tache.cpu / vitesse
                temps_fin = debut + exec_time
                
                # Ratio de charge actuelle (0 = vide, 1+ = surchargé)
                charge_ratio = len(fog.taches_en_cours) / fog.cpu_total
                
                # Score = temps_fin + pénalité_équilibrage
                # 0.7 pour temps, 0.3 pour équilibrage
                score = 0.7 * temps_fin + 0.3 * charge_ratio
                return score
            
            # Choisir le fog qui minimise le score
            return min(candidats, key=score_noeud)
        else:
            # Pour non-urgent : préférer le moins chargé parmi les disponibles
            # Combiner disponibilité (CPU libre) ET charge (ratio relative)
            fogs_libres = [f for f in candidats if f.get_cpu_disponible(temps_actuel) >= tache.cpu]
            if fogs_libres:
                # Choisir par ratio de charge (charge_actuelle / capacité)
                return min(fogs_libres, key=lambda f: (
                    len(f.taches_en_cours) / f.cpu_total,
                    -f.get_cpu_disponible(temps_actuel)
                ))
            return cloud

    def _calcul_urgence(self, tache: Tache, temps_actuel: float) -> float:
        temps_restant = max(0.001, tache.delai - (temps_actuel - tache.arrivee))
        return min(100.0, 1.0 / temps_restant)

    def _priorite_dynamique(self, tache: Tache, temps_actuel: float) -> float:
        urgence = self._calcul_urgence(tache, temps_actuel)
        attente = max(0.0, temps_actuel - tache.arrivee)
        return self.BETA * urgence + self.GAMMA * tache.criticite + self.ALPHA * attente

    # -----------------------------
    # Utilitaires
    # -----------------------------
    def _copier_noeuds(self) -> Tuple[List[Noeud], Noeud]:
        fogs = [Noeud(f.nom, f.cpu_total, f.type) for f in self.fogs_template]
        cloud = Noeud(self.cloud_template.nom, self.cloud_template.cpu_total, self.cloud_template.type)
        return fogs, cloud

    def _copier_taches(self) -> List[Tache]:
        return [
            Tache(t.nom, t.cpu, t.criticite, t.arrivee, t.delai)
            for t in self.taches_template
        ]
