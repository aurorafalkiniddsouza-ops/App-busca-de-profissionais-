from app.connectors.coren_sp import CorenSPConnector
from app.connectors.cremesp_production_candidate import CremespProductionCandidateConnector


CONNECTOR_REGISTRY_CANDIDATE = {
    "COREN-SP": CorenSPConnector,
    "CREMESP": CremespProductionCandidateConnector,
}


def get_connector_candidate(council_name: str):
    connector_class = CONNECTOR_REGISTRY_CANDIDATE.get(council_name)
    if not connector_class:
        raise ValueError(f"Conselho não suportado: {council_name}")
    return connector_class()
