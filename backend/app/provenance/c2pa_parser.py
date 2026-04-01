import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

logger = logging.getLogger(__name__)

# C2PA (Coalition for Content Provenance and Authenticity) standard
# Uses c2pa-python library (pip install c2pa-python)
# C2PA embeds a cryptographically signed manifest inside JPEG, PNG, MP4 files

try:
    import c2pa
    C2PA_AVAILABLE = True
except ImportError:
    C2PA_AVAILABLE = False
    logger.warning("c2pa-python not installed. C2PA parsing will return no-data results.")


@dataclass
class C2PAResult:
    present: bool = False
    valid: bool = False
    claim_generator: Optional[str] = None      # software that created/signed
    signer: Optional[str] = None               # certificate issuer
    edit_history: list = field(default_factory=list)
    ingredient_count: int = 0                  # parent media count (0 = original capture)
    error: Optional[str] = None
    details: Optional[dict] = None             # full manifest dict


def parse_c2pa(file_path: str) -> C2PAResult:
    """
    Parse C2PA manifest from a media file.
    C2PA reader validates the certificate chain automatically on parse.
    If reader.from_file() succeeds without exception → signature valid.
    """
    if not C2PA_AVAILABLE:
        return C2PAResult(present=False, valid=False)

    try:
        reader = c2pa.Reader.from_file(file_path)
        manifest = reader.get_active_manifest()

        if manifest is None:
            logger.info(f"No C2PA manifest found in {file_path}")
            return C2PAResult(present=False, valid=False)

        # Extract manifest fields
        claim_generator = manifest.claim_generator()
        ingredients = manifest.ingredients()
        assertions = manifest.assertions()
        signature_info = manifest.signature_info()

        # Signature validated by reader — if we got here it's valid
        is_valid = True

        # Extract edit history from assertions
        edit_actions = []
        for assertion in assertions:
            if assertion.label() == "c2pa.actions":
                actions_data = assertion.data()
                edit_actions = actions_data.get("actions", [])

        result = C2PAResult(
            present=True,
            valid=is_valid,
            claim_generator=claim_generator,
            signer=signature_info.get("issuer"),
            edit_history=edit_actions,
            ingredient_count=len(ingredients),
            details=manifest.to_dict(),
        )

        logger.info(
            f"C2PA parsed: valid={is_valid} generator={claim_generator} "
            f"edits={len(edit_actions)} ingredients={len(ingredients)}"
        )
        return result

    except Exception as e:
        # Signature validation failed or file cannot be parsed
        logger.warning(f"C2PA parse error for {file_path}: {e}")
        return C2PAResult(present=True, valid=False, error=str(e))


def c2pa_to_dict(result: C2PAResult) -> dict:
    """Serialize C2PAResult to dict for API response."""
    return asdict(result)
