# Materials Project API client (mp-api)

- Installed: `mp-api==0.46.5`; Python module `mp_api`.
- Official source: https://github.com/materialsproject/api
- Official usage: https://docs.materialsproject.org/downloading-data/using-the-api/getting-started
- Function: online Materials Project structure and computed-property records.

**Python interface:** `from mp_api.client import MPRester`; `with MPRester() as client: docs = client.materials.summary.search(material_ids=["mp-149"], fields=["material_id", "structure"])`. Input is an API query; output is a list of document objects.

**Access condition:** The official API requires a personal key, read from `MP_API_KEY` or passed to `MPRester`. No key is bundled. Network access and account permissions are required; the local NIMS archives are independent of this service.
