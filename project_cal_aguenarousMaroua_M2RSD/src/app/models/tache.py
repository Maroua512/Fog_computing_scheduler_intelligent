class Tache:
    def __init__(self, nom: str, cpu: float, criticite: float, arrivee: float, delai: float | None) -> None:
        self.nom = nom
        self.cpu = cpu
        self.criticite = criticite
        self.arrivee = arrivee
        self.delai = delai
        self.noeud: str | None = None
        self.debut: float = 0.0
        self.fin: float = 0.0
        self.attente: float = 0.0
        self.latence: float = 0.0
        self.delai_ok: bool = False
