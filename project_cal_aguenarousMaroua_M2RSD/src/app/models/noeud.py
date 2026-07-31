class Noeud:
    def __init__(self, nom: str, cpu: float, type_noeud: str = "Fog") -> None:
        self.nom = nom
        self.cpu_total = cpu
        self.cpu_dispo = cpu
        self.type = type_noeud
        self.temps_libre: float = 0.0
        self.energie: float = 0.0
        self.taches_en_cours: list = []  # Liste des (fin_time, cpu_utilisé)
    
    def get_cpu_disponible(self, temps_actuel: float) -> float:
        """Retourne le CPU disponible à un temps donné (sans modifier taches_en_cours)"""
        # Ne pas modifier taches_en_cours ici, juste calculer
        cpu_utilisé = sum(cpu for fin, cpu in self.taches_en_cours if fin > temps_actuel)
        return self.cpu_total - cpu_utilisé
    
    def peut_executer(self, cpu_requis: float, temps_actuel: float) -> bool:
        """Vérifie si le fog peut exécuter une tâche nécessitant cpu_requis"""
        return self.get_cpu_disponible(temps_actuel) >= cpu_requis
    
    def get_temps_debut(self, temps_actuel: float) -> float:
        """Retourne le temps auquel la tâche peut commencer"""
        if self.get_cpu_disponible(temps_actuel) > 0:
            return temps_actuel
        return self.temps_libre
