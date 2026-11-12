import re


def verify_claims(claims: list[dict], sources: list[dict]) -> list[dict]:
    index = {s['id']: s for s in sources}
    normalize = lambda s: re.sub(r'\s+', ' ', s).strip()
    errors = []
    for claim in claims:
        source = index.get(claim.get('source_id'))
        quote = normalize(claim.get('quote', ''))
        if source is None or not quote or quote not in normalize(source['text']):
            errors.append({'code': 'INVALID_EVIDENCE', 'message': 'Nguồn hoặc trích dẫn không khớp tập nguồn đã cấp.'})
    # Exact citations do not prove entailment. All generated content remains a draft.
    return errors
